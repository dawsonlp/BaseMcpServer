"""
Application layer use cases for file operations.

This module contains the business logic for file attachment operations,
coordinating between domain models and infrastructure adapters.
"""

from typing import Optional

from application.base_use_case import BaseUseCase
from application.error_mappers import map_domain_error_to_result
from domain.exceptions import JiraHelperException
from domain.file_models import (
    AttachmentDeleteRequest,
    AttachmentDeleteResult,
    AttachmentListRequest,
    AttachmentListResult,
    FileContent,
    FileUploadPolicy,
    FileUploadRequest,
    FileUploadResult,
    JiraAttachment,
)
from domain.ports import (
    ConfigurationProvider,
    EventPublisher,
    FileAttachmentPort,
    FileSystemPort,
    FileUploadPolicyProvider,
    FileValidationPort,
    Logger,
)
from domain.results import Result


class UploadFileUseCase(BaseUseCase):
    """Use case for uploading a file to a Jira issue."""

    def __init__(
        self,
        file_attachment_port: FileAttachmentPort,
        file_validation_port: FileValidationPort,
        file_system_port: FileSystemPort,
        policy_provider: FileUploadPolicyProvider,
        config_provider: ConfigurationProvider,
        event_publisher: EventPublisher,
        logger: Logger,
    ):
        super().__init__(config_provider=config_provider, logger=logger)
        self._file_attachment_port = file_attachment_port
        self._file_validation_port = file_validation_port
        self._file_system_port = file_system_port
        self._policy_provider = policy_provider
        self._event_publisher = event_publisher

    async def execute(
        self, 
        issue_key: str,
        file_path: str,
        comment: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Result[FileUploadResult]:
        """
        Upload a file to a Jira issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            file_path: Path to the file to upload
            comment: Optional comment to add with the attachment
            instance_name: Name of the Jira instance to use
            
        Returns:
            Result containing FileUploadResult or error
        """
        try:
            self._logger.info(f"Starting file upload for issue {issue_key}: {file_path}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                return Result.error(
                    f"Jira instance not found: {instance_name or 'default'}"
                )
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                return Result.error("No Jira instance specified and no default configured")
            
            # Create upload request
            try:
                upload_request = FileUploadRequest(
                    issue_key=issue_key,
                    file_path=file_path,
                    comment=comment
                )
            except ValueError as e:
                return Result.error(f"Invalid upload request: {str(e)}")
            
            # Validate file path
            path_errors = self._file_validation_port.validate_file_path(file_path)
            if path_errors:
                return Result.error(f"File path validation failed: {'; '.join(path_errors)}")
            
            # Check if file exists and is readable
            if not self._file_system_port.file_exists(file_path):
                return Result.error(f"File does not exist: {file_path}")
            
            if not self._file_validation_port.is_file_readable(file_path):
                return Result.error(f"File is not readable: {file_path}")
            
            # Get file information
            try:
                file_size = self._file_validation_port.get_file_size(file_path)
                mime_type = self._file_validation_port.detect_mime_type(file_path)
                filename = upload_request.get_filename_from_path()
            except Exception as e:
                return Result.error(f"Failed to get file information: {str(e)}")
            
            # Get upload policy and validate file
            try:
                # Try to get project-specific policy first
                project_key = issue_key.split('-')[0] if '-' in issue_key else None
                if project_key:
                    policy = self._policy_provider.get_policy_for_project(
                        project_key, actual_instance_name
                    )
                else:
                    policy = self._policy_provider.get_policy_for_instance(actual_instance_name)
            except Exception:
                # Fall back to default policy if project-specific policy fails
                policy = self._policy_provider.get_default_policy()
            
            # Validate against policy
            is_allowed, policy_error = self._policy_provider.validate_against_policy(
                filename, mime_type, file_size, policy
            )
            if not is_allowed:
                return Result.error(f"File upload policy violation: {policy_error}")
            
            # Read file content
            try:
                file_content_bytes = self._file_system_port.read_file(file_path)
                file_content = FileContent(
                    filename=filename,
                    content=file_content_bytes,
                    mime_type=mime_type,
                    size=file_size
                )
            except Exception as e:
                return Result.error(f"Failed to read file content: {str(e)}")
            
            # Validate file content
            content_errors = self._file_validation_port.validate_file_content(file_content, policy)
            if content_errors:
                return Result.error(f"File content validation failed: {'; '.join(content_errors)}")
            
            # Perform the upload
            upload_result = await self._file_attachment_port.upload_file(
                upload_request, actual_instance_name
            )
            
            if upload_result.is_successful():
                self._logger.info(
                    f"File uploaded successfully to {issue_key}: {filename} "
                    f"(ID: {upload_result.get_attachment_id()})"
                )
                
                # Publish event (fire and forget)
                try:
                    await self._event_publisher.publish_comment_added(
                        issue_key, 
                        None,  # No comment object for file upload
                        actual_instance_name
                    )
                except Exception as e:
                    self._logger.warning(f"Failed to publish file upload event: {str(e)}")
            else:
                self._logger.error(f"File upload failed for {issue_key}: {upload_result.error}")
            
            return Result.success(upload_result)
            
        except JiraHelperException as e:
            self._logger.error(f"Domain error during file upload: {str(e)}")
            return map_domain_error_to_result(e, FileUploadResult)
        except Exception as e:
            self._logger.error(f"Unexpected error during file upload: {str(e)}")
            return Result.error(f"File upload failed: {str(e)}")


class UploadFileContentUseCase(BaseUseCase):
    """Use case for uploading file content directly to a Jira issue."""

    def __init__(
        self,
        file_attachment_port: FileAttachmentPort,
        file_validation_port: FileValidationPort,
        policy_provider: FileUploadPolicyProvider,
        config_provider: ConfigurationProvider,
        event_publisher: EventPublisher,
        logger: Logger,
    ):
        super().__init__(config_provider=config_provider, logger=logger)
        self._file_attachment_port = file_attachment_port
        self._file_validation_port = file_validation_port
        self._policy_provider = policy_provider
        self._event_publisher = event_publisher

    async def execute(
        self,
        issue_key: str,
        filename: str,
        content: bytes,
        mime_type: Optional[str] = None,
        comment: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Result[FileUploadResult]:
        """
        Upload file content directly to a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            filename: Name for the uploaded file
            content: File content as bytes
            mime_type: MIME type (auto-detected if not provided)
            comment: Optional comment to add with the attachment
            instance_name: Name of the Jira instance to use
            
        Returns:
            Result containing FileUploadResult or error
        """
        try:
            self._logger.info(f"Starting file content upload for issue {issue_key}: {filename}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                return Result.error(
                    f"Jira instance not found: {instance_name or 'default'}"
                )
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                return Result.error("No Jira instance specified and no default configured")
            
            # Auto-detect MIME type if not provided
            if mime_type is None:
                try:
                    mime_type = self._file_validation_port.detect_mime_type_from_content(
                        content, filename
                    )
                except Exception as e:
                    self._logger.warning(f"Failed to detect MIME type: {str(e)}")
                    mime_type = "application/octet-stream"  # Default binary type
            
            # Create file content object
            try:
                file_content = FileContent(
                    filename=filename,
                    content=content,
                    mime_type=mime_type
                )
            except ValueError as e:
                return Result.error(f"Invalid file content: {str(e)}")
            
            # Get upload policy and validate file
            try:
                project_key = issue_key.split('-')[0] if '-' in issue_key else None
                if project_key:
                    policy = self._policy_provider.get_policy_for_project(
                        project_key, actual_instance_name
                    )
                else:
                    policy = self._policy_provider.get_policy_for_instance(actual_instance_name)
            except Exception:
                policy = self._policy_provider.get_default_policy()
            
            # Validate against policy
            is_allowed, policy_error = self._policy_provider.validate_against_policy(
                filename, mime_type, len(content), policy
            )
            if not is_allowed:
                return Result.error(f"File upload policy violation: {policy_error}")
            
            # Validate file content
            content_errors = self._file_validation_port.validate_file_content(file_content, policy)
            if content_errors:
                return Result.error(f"File content validation failed: {'; '.join(content_errors)}")
            
            # Perform the upload
            upload_result = await self._file_attachment_port.upload_file_content(
                issue_key, file_content, comment, actual_instance_name
            )
            
            if upload_result.is_successful():
                self._logger.info(
                    f"File content uploaded successfully to {issue_key}: {filename} "
                    f"(ID: {upload_result.get_attachment_id()})"
                )
                
                # Publish event (fire and forget)
                try:
                    await self._event_publisher.publish_comment_added(
                        issue_key, None, actual_instance_name
                    )
                except Exception as e:
                    self._logger.warning(f"Failed to publish file upload event: {str(e)}")
            else:
                self._logger.error(f"File content upload failed for {issue_key}: {upload_result.error}")
            
            return Result.success(upload_result)
            
        except JiraHelperException as e:
            self._logger.error(f"Domain error during file content upload: {str(e)}")
            return map_domain_error_to_result(e, FileUploadResult)
        except Exception as e:
            self._logger.error(f"Unexpected error during file content upload: {str(e)}")
            return Result.error(f"File content upload failed: {str(e)}")


class ListAttachmentsUseCase(BaseUseCase):
    """Use case for listing attachments of a Jira issue."""

    def __init__(
        self,
        file_attachment_port: FileAttachmentPort,
        config_provider: ConfigurationProvider,
        logger: Logger,
    ):
        super().__init__(config_provider=config_provider, logger=logger)
        self._file_attachment_port = file_attachment_port

    async def execute(
        self,
        issue_key: str,
        include_thumbnails: bool = False,
        instance_name: Optional[str] = None
    ) -> Result[AttachmentListResult]:
        """
        List all attachments for a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            include_thumbnails: Whether to include thumbnail URLs
            instance_name: Name of the Jira instance to use
            
        Returns:
            Result containing AttachmentListResult or error
        """
        try:
            self._logger.debug(f"Listing attachments for issue {issue_key}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                return Result.error(
                    f"Jira instance not found: {instance_name or 'default'}"
                )
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                return Result.error("No Jira instance specified and no default configured")
            
            # Create list request
            try:
                list_request = AttachmentListRequest(
                    issue_key=issue_key,
                    include_thumbnails=include_thumbnails
                )
            except ValueError as e:
                return Result.error(f"Invalid list request: {str(e)}")
            
            # Get attachments
            list_result = await self._file_attachment_port.list_attachments(
                list_request, actual_instance_name
            )
            
            if list_result.is_successful():
                self._logger.debug(
                    f"Found {list_result.get_attachment_count()} attachments for {issue_key}"
                )
            else:
                self._logger.error(f"Failed to list attachments for {issue_key}: {list_result.error}")
            
            return Result.success(list_result)
            
        except JiraHelperException as e:
            self._logger.error(f"Domain error during attachment listing: {str(e)}")
            return map_domain_error_to_result(e, AttachmentListResult)
        except Exception as e:
            self._logger.error(f"Unexpected error during attachment listing: {str(e)}")
            return Result.error(f"Attachment listing failed: {str(e)}")


class DeleteAttachmentUseCase(BaseUseCase):
    """Use case for deleting an attachment from a Jira issue."""

    def __init__(
        self,
        file_attachment_port: FileAttachmentPort,
        config_provider: ConfigurationProvider,
        event_publisher: EventPublisher,
        logger: Logger,
    ):
        super().__init__(config_provider=config_provider, logger=logger)
        self._file_attachment_port = file_attachment_port
        self._event_publisher = event_publisher

    async def execute(
        self,
        issue_key: str,
        attachment_id: str,
        instance_name: Optional[str] = None
    ) -> Result[AttachmentDeleteResult]:
        """
        Delete an attachment from a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            attachment_id: ID of the attachment to delete
            instance_name: Name of the Jira instance to use
            
        Returns:
            Result containing AttachmentDeleteResult or error
        """
        try:
            self._logger.info(f"Deleting attachment {attachment_id} from issue {issue_key}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                return Result.error(
                    f"Jira instance not found: {instance_name or 'default'}"
                )
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                return Result.error("No Jira instance specified and no default configured")
            
            # Create delete request
            try:
                delete_request = AttachmentDeleteRequest(
                    issue_key=issue_key,
                    attachment_id=attachment_id
                )
            except ValueError as e:
                return Result.error(f"Invalid delete request: {str(e)}")
            
            # Get attachment info before deletion (for logging/events)
            attachment_info = await self._file_attachment_port.get_attachment(
                attachment_id, actual_instance_name
            )
            
            # Delete attachment
            delete_result = await self._file_attachment_port.delete_attachment(
                delete_request, actual_instance_name
            )
            
            if delete_result.is_successful():
                filename = attachment_info.filename if attachment_info else "unknown"
                self._logger.info(
                    f"Attachment deleted successfully from {issue_key}: {filename} (ID: {attachment_id})"
                )
                
                # Publish event (fire and forget)
                try:
                    await self._event_publisher.publish_comment_added(
                        issue_key, None, actual_instance_name
                    )
                except Exception as e:
                    self._logger.warning(f"Failed to publish attachment deletion event: {str(e)}")
            else:
                self._logger.error(f"Failed to delete attachment {attachment_id}: {delete_result.error}")
            
            return Result.success(delete_result)
            
        except JiraHelperException as e:
            self._logger.error(f"Domain error during attachment deletion: {str(e)}")
            return map_domain_error_to_result(e, AttachmentDeleteResult)
        except Exception as e:
            self._logger.error(f"Unexpected error during attachment deletion: {str(e)}")
            return Result.error(f"Attachment deletion failed: {str(e)}")


class GetAttachmentUseCase(BaseUseCase):
    """Use case for getting attachment details."""

    def __init__(
        self,
        file_attachment_port: FileAttachmentPort,
        config_provider: ConfigurationProvider,
        logger: Logger,
    ):
        super().__init__(config_provider=config_provider, logger=logger)
        self._file_attachment_port = file_attachment_port

    async def execute(
        self,
        attachment_id: str,
        instance_name: Optional[str] = None
    ) -> Result[Optional[JiraAttachment]]:
        """
        Get attachment details by ID.
        
        Args:
            attachment_id: ID of the attachment
            instance_name: Name of the Jira instance to use
            
        Returns:
            Result containing JiraAttachment or None if not found
        """
        try:
            self._logger.debug(f"Getting attachment details for ID: {attachment_id}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                return Result.error(
                    f"Jira instance not found: {instance_name or 'default'}"
                )
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                return Result.error("No Jira instance specified and no default configured")
            
            # Get attachment
            attachment = await self._file_attachment_port.get_attachment(
                attachment_id, actual_instance_name
            )
            
            if attachment:
                self._logger.debug(f"Found attachment: {attachment.filename}")
            else:
                self._logger.debug(f"Attachment not found: {attachment_id}")
            
            return Result.success(attachment)
            
        except JiraHelperException as e:
            self._logger.error(f"Domain error during attachment retrieval: {str(e)}")
            return Result.error(f"Failed to get attachment: {str(e)}")
        except Exception as e:
            self._logger.error(f"Unexpected error during attachment retrieval: {str(e)}")
            return Result.error(f"Attachment retrieval failed: {str(e)}")
