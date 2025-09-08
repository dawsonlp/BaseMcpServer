"""
Application layer use cases for file operations.

This module contains the business logic for file attachment operations,
coordinating between domain models and infrastructure adapters.
"""

from typing import Optional

from application.base_use_case import BaseUseCase, BaseCommandUseCase, BaseQueryUseCase
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


class UploadFileUseCase(BaseCommandUseCase):
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
    ):
        """
        Upload a file to a Jira issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            file_path: Path to the file to upload
            comment: Optional comment to add with the attachment
            instance_name: Name of the Jira instance to use
            
        Returns:
            UseCaseResult containing FileUploadResult or error
        """
        self._validate_required_params(issue_key=issue_key, file_path=file_path)

        async def upload_operation():
            self._logger.info(f"Starting file upload for issue {issue_key}: {file_path}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                raise ValueError(f"Jira instance not found: {instance_name or 'default'}")
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                raise ValueError("No Jira instance specified and no default configured")
            
            # Create upload request
            upload_request = FileUploadRequest(
                issue_key=issue_key,
                file_path=file_path,
                comment=comment
            )
            
            # Validate file path
            path_errors = self._file_validation_port.validate_file_path(file_path)
            if path_errors:
                raise ValueError(f"File path validation failed: {'; '.join(path_errors)}")
            
            # Check if file exists and is readable
            if not self._file_system_port.file_exists(file_path):
                raise FileNotFoundError(f"File does not exist: {file_path}")
            
            if not self._file_validation_port.is_file_readable(file_path):
                raise PermissionError(f"File is not readable: {file_path}")
            
            # Get file information
            file_size = self._file_validation_port.get_file_size(file_path)
            mime_type = self._file_validation_port.detect_mime_type(file_path)
            filename = upload_request.get_filename_from_path()
            
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
                raise ValueError(f"File upload policy violation: {policy_error}")
            
            # Read file content
            file_content_bytes = self._file_system_port.read_file(file_path)
            file_content = FileContent(
                filename=filename,
                content=file_content_bytes,
                mime_type=mime_type,
                size=file_size
            )
            
            # Validate file content
            content_errors = self._file_validation_port.validate_file_content(file_content, policy)
            if content_errors:
                raise ValueError(f"File content validation failed: {'; '.join(content_errors)}")
            
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
                if self._event_publisher is not None:
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
                raise RuntimeError(upload_result.error or "Upload failed")
            
            return upload_result

        def success_mapper(upload_result):
            return {
                "uploaded": True,
                "issue_key": issue_key,
                "filename": upload_result.attachment.filename if upload_result.attachment else None,
                "file_size": upload_result.attachment.size if upload_result.attachment else None,
                "attachment_id": upload_result.get_attachment_id(),
                "url": upload_result.attachment.download_url if upload_result.attachment else None,
                "comment_added": bool(comment),
                "instance": instance_name
            }

        return await self.execute_command(
            upload_operation,
            success_mapper,
            issue_key=issue_key,
            file_path=file_path,
            instance_name=instance_name
        )


class UploadFileContentUseCase(BaseCommandUseCase):
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
    ):
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
            UseCaseResult containing FileUploadResult or error
        """
        self._validate_required_params(issue_key=issue_key, filename=filename, content=content)

        async def upload_operation():
            self._logger.info(f"Starting file content upload for issue {issue_key}: {filename}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                raise ValueError(f"Jira instance not found: {instance_name or 'default'}")
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                raise ValueError("No Jira instance specified and no default configured")
            
            # Auto-detect MIME type if not provided
            detected_mime_type = mime_type
            if detected_mime_type is None:
                try:
                    detected_mime_type = self._file_validation_port.detect_mime_type_from_content(
                        content, filename
                    )
                except Exception as e:
                    self._logger.warning(f"Failed to detect MIME type: {str(e)}")
                    detected_mime_type = "application/octet-stream"  # Default binary type
            
            # Create file content object
            try:
                file_content = FileContent(
                    filename=filename,
                    content=content,
                    mime_type=detected_mime_type
                )
            except ValueError as e:
                raise ValueError(f"Invalid file content: {str(e)}")
            
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
                filename, detected_mime_type, len(content), policy
            )
            if not is_allowed:
                raise ValueError(f"File upload policy violation: {policy_error}")
            
            # Validate file content
            content_errors = self._file_validation_port.validate_file_content(file_content, policy)
            if content_errors:
                raise ValueError(f"File content validation failed: {'; '.join(content_errors)}")
            
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
                if self._event_publisher is not None:
                    try:
                        await self._event_publisher.publish_comment_added(
                            issue_key, None, actual_instance_name
                        )
                    except Exception as e:
                        self._logger.warning(f"Failed to publish file upload event: {str(e)}")
            else:
                self._logger.error(f"File content upload failed for {issue_key}: {upload_result.error}")
                raise RuntimeError(upload_result.error or "Upload failed")
            
            return upload_result

        def success_mapper(upload_result):
            return {
                "uploaded": True,
                "issue_key": issue_key,
                "filename": upload_result.attachment.filename if upload_result.attachment else None,
                "file_size": upload_result.attachment.size if upload_result.attachment else None,
                "attachment_id": upload_result.get_attachment_id(),
                "url": upload_result.attachment.download_url if upload_result.attachment else None,
                "comment_added": bool(comment),
                "instance": instance_name
            }

        return await self.execute_command(
            upload_operation,
            success_mapper,
            issue_key=issue_key,
            filename=filename,
            instance_name=instance_name
        )


class ListAttachmentsUseCase(BaseQueryUseCase):
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
    ):
        """
        List all attachments for a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            include_thumbnails: Whether to include thumbnail URLs
            instance_name: Name of the Jira instance to use
            
        Returns:
            UseCaseResult containing AttachmentListResult or error
        """
        self._validate_required_params(issue_key=issue_key)

        async def query_operation():
            self._logger.debug(f"Listing attachments for issue {issue_key}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                raise ValueError(f"Jira instance not found: {instance_name or 'default'}")
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                raise ValueError("No Jira instance specified and no default configured")
            
            # Create list request
            try:
                list_request = AttachmentListRequest(
                    issue_key=issue_key,
                    include_thumbnails=include_thumbnails
                )
            except ValueError as e:
                raise ValueError(f"Invalid list request: {str(e)}")
            
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
                raise RuntimeError(list_result.error or "Failed to list attachments")
            
            return list_result

        def result_mapper(list_result):
            attachments = []
            if hasattr(list_result, 'attachments') and list_result.attachments:
                for attachment in list_result.attachments:
                    attachment_data = {
                        "id": attachment.id,
                        "filename": attachment.filename,
                        "size": attachment.size,
                        "mime_type": attachment.mime_type,
                        "created": attachment.created if hasattr(attachment, 'created') and attachment.created else None,
                        "author": attachment.author if hasattr(attachment, 'author') else None,
                        "url": attachment.content_url if hasattr(attachment, 'content_url') else None
                    }
                    if include_thumbnails and hasattr(attachment, 'thumbnail_url'):
                        attachment_data["thumbnail_url"] = attachment.thumbnail_url
                    attachments.append(attachment_data)
            
            return {
                "issue_key": issue_key,
                "attachment_count": list_result.get_attachment_count() if hasattr(list_result, 'get_attachment_count') else len(attachments),
                "attachments": attachments,
                "include_thumbnails": include_thumbnails,
                "instance": instance_name
            }

        return await self.execute_query(
            query_operation,
            result_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class DeleteAttachmentUseCase(BaseCommandUseCase):
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
    ):
        """
        Delete an attachment from a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            attachment_id: ID of the attachment to delete
            instance_name: Name of the Jira instance to use
            
        Returns:
            UseCaseResult containing AttachmentDeleteResult or error
        """
        self._validate_required_params(issue_key=issue_key, attachment_id=attachment_id)

        async def delete_operation():
            self._logger.info(f"Deleting attachment {attachment_id} from issue {issue_key}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                raise ValueError(f"Jira instance not found: {instance_name or 'default'}")
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                raise ValueError("No Jira instance specified and no default configured")
            
            # Create delete request
            try:
                delete_request = AttachmentDeleteRequest(
                    issue_key=issue_key,
                    attachment_id=attachment_id
                )
            except ValueError as e:
                raise ValueError(f"Invalid delete request: {str(e)}")
            
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
                if self._event_publisher is not None:
                    try:
                        await self._event_publisher.publish_comment_added(
                            issue_key, None, actual_instance_name
                        )
                    except Exception as e:
                        self._logger.warning(f"Failed to publish attachment deletion event: {str(e)}")
            else:
                self._logger.error(f"Failed to delete attachment {attachment_id}: {delete_result.error}")
                raise RuntimeError(delete_result.error or "Attachment deletion failed")
            
            return delete_result

        def success_mapper(delete_result):
            return {
                "deleted": True,
                "issue_key": issue_key,
                "attachment_id": attachment_id,
                "filename": delete_result.filename if hasattr(delete_result, 'filename') else None,
                "instance": instance_name
            }

        return await self.execute_command(
            delete_operation,
            success_mapper,
            issue_key=issue_key,
            attachment_id=attachment_id,
            instance_name=instance_name
        )


class GetAttachmentUseCase(BaseQueryUseCase):
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
    ):
        """
        Get attachment details by ID.
        
        Args:
            attachment_id: ID of the attachment
            instance_name: Name of the Jira instance to use
            
        Returns:
            UseCaseResult containing JiraAttachment or None if not found
        """
        self._validate_required_params(attachment_id=attachment_id)

        async def query_operation():
            self._logger.debug(f"Getting attachment details for ID: {attachment_id}")
            
            # Validate instance
            instance = self._config_provider.get_instance(instance_name)
            if not instance:
                raise ValueError(f"Jira instance not found: {instance_name or 'default'}")
            
            actual_instance_name = instance_name or self._config_provider.get_default_instance_name()
            if not actual_instance_name:
                raise ValueError("No Jira instance specified and no default configured")
            
            # Get attachment
            attachment = await self._file_attachment_port.get_attachment(
                attachment_id, actual_instance_name
            )
            
            if attachment:
                self._logger.debug(f"Found attachment: {attachment.filename}")
            else:
                self._logger.debug(f"Attachment not found: {attachment_id}")
            
            return attachment

        def result_mapper(attachment):
            if attachment:
                return {
                    "attachment_id": attachment.id,
                    "filename": attachment.filename,
                    "size": attachment.size,
                    "mime_type": attachment.mime_type,
                    "created": attachment.created if hasattr(attachment, 'created') and attachment.created else None,
                    "author": attachment.author if hasattr(attachment, 'author') else None,
                    "url": attachment.content_url if hasattr(attachment, 'content_url') else None,
                    "thumbnail_url": attachment.thumbnail_url if hasattr(attachment, 'thumbnail_url') else None,
                    "found": True,
                    "instance": instance_name
                }
            else:
                return {
                    "attachment_id": attachment_id,
                    "found": False,
                    "instance": instance_name
                }

        return await self.execute_query(
            query_operation,
            result_mapper,
            attachment_id=attachment_id,
            instance_name=instance_name
        )
