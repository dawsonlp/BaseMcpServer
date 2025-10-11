"""
Infrastructure adapter for Jira file attachment operations.

This module implements the FileAttachmentPort using the Atlassian REST API.
"""

import base64
import mimetypes
from typing import Optional

from atlassian import Jira

from domain.exceptions import JiraIssueNotFound
from domain.file_models import (
    AttachmentDeleteRequest,
    AttachmentDeleteResult,
    AttachmentListRequest,
    AttachmentListResult,
    FileContent,
    FileUploadRequest,
    FileUploadResult,
    JiraAttachment,
)
from domain.ports import FileAttachmentPort, JiraClientFactory, Logger
from infrastructure.base_adapter import BaseJiraAdapter
from infrastructure.converters import convert_jira_attachment


class AtlassianFileAdapter(BaseJiraAdapter, FileAttachmentPort):
    """Adapter for Jira file attachment operations using Atlassian Python API."""

    def __init__(self, config_provider, client_factory: JiraClientFactory):
        super().__init__(client_factory, config_provider)

    async def upload_file(self, request: FileUploadRequest, instance_name: str | None = None) -> FileUploadResult:
        """Upload a file to a Jira issue."""
        async def operation(client):
            self._logger.info(f"Uploading file {request.file_path} to issue {request.issue_key}")
            
            # Upload the file
            response = client.add_attachment(request.issue_key, request.file_path)
            
            # Check if the response indicates success
            if not response or len(response) == 0:
                return FileUploadResult(
                    issue_key=request.issue_key,
                    uploaded=False,
                    error="No attachment was created - empty response from Jira"
                )
            
            # Get the first (and typically only) attachment from response
            attachment_data = response[0] if isinstance(response, list) else response
            
            # Convert to domain model
            attachment = convert_jira_attachment(attachment_data)
            
            self._logger.info(
                f"File uploaded successfully: {attachment.filename} (ID: {attachment.id})"
            )
            
            return FileUploadResult(
                issue_key=request.issue_key,
                uploaded=True,
                attachment=attachment
            )

        error_mappings = {
            "does not exist": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "issue does not exist": JiraIssueNotFound(request.issue_key, instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("upload_file", operation, instance_name, error_mappings)
        except Exception as e:
            error_msg = f"Failed to upload file to {request.issue_key}: {str(e)}"
            self._logger.error(error_msg)
            return FileUploadResult(
                issue_key=request.issue_key,
                uploaded=False,
                error=error_msg
            )

    async def upload_file_content(
        self, 
        issue_key: str, 
        file_content: FileContent, 
        comment: str | None = None, 
        instance_name: str | None = None
    ) -> FileUploadResult:
        """Upload file content directly to a Jira issue."""
        async def operation(client):
            self._logger.info(f"Uploading file content {file_content.filename} to issue {issue_key}")
            
            # Create a temporary file-like object or use direct content upload
            # The Atlassian library expects file paths, so we need to work with the raw API
            import tempfile
            import os
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=f"_{file_content.filename}",
                prefix="jira_upload_"
            ) as temp_file:
                temp_file.write(file_content.content)
                temp_file_path = temp_file.name
            
            try:
                # Upload using the temporary file
                response = client.add_attachment(issue_key, temp_file_path)
                
                # Check if the response indicates success
                if not response or len(response) == 0:
                    return FileUploadResult(
                        issue_key=issue_key,
                        uploaded=False,
                        error="No attachment was created - empty response from Jira"
                    )
                
                # Get the first attachment from response
                attachment_data = response[0] if isinstance(response, list) else response
                
                # Convert to domain model
                attachment = convert_jira_attachment(attachment_data)
                
                self._logger.info(
                    f"File content uploaded successfully: {attachment.filename} (ID: {attachment.id})"
                )
                
                return FileUploadResult(
                    issue_key=issue_key,
                    uploaded=True,
                    attachment=attachment
                )
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    self._logger.warning(f"Failed to delete temporary file: {temp_file_path}")

        error_mappings = {
            "does not exist": JiraIssueNotFound(issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(issue_key, instance_name or "default"),
            "issue does not exist": JiraIssueNotFound(issue_key, instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("upload_file_content", operation, instance_name, error_mappings)
        except Exception as e:
            error_msg = f"Failed to upload file content to {issue_key}: {str(e)}"
            self._logger.error(error_msg)
            return FileUploadResult(
                issue_key=issue_key,
                uploaded=False,
                error=error_msg
            )

    async def list_attachments(
        self, 
        request: AttachmentListRequest, 
        instance_name: str | None = None
    ) -> AttachmentListResult:
        """List all attachments for an issue."""
        try:
            self._logger.debug(f"Listing attachments for issue {request.issue_key}")
            
            # Get Jira client
            client: Jira = self._client_factory.create_client(instance_name)
            
            # Get issue details with attachments
            issue_data = client.issue(request.issue_key, fields="attachment")
            
            # Extract attachments
            attachments_data = issue_data.get("fields", {}).get("attachment", [])
            
            # Convert to domain models
            attachments = []
            for attachment_data in attachments_data:
                try:
                    attachment = convert_jira_attachment(attachment_data)
                    attachments.append(attachment)
                except Exception as e:
                    self._logger.warning(f"Failed to convert attachment data: {str(e)}")
                    continue
            
            self._logger.debug(f"Found {len(attachments)} attachments for {request.issue_key}")
            
            return AttachmentListResult(
                issue_key=request.issue_key,
                attachments=attachments
            )
            
        except Exception as e:
            error_msg = f"Failed to list attachments for {request.issue_key}: {str(e)}"
            self._logger.error(error_msg)
            return AttachmentListResult(
                issue_key=request.issue_key,
                attachments=[],
                error=error_msg
            )

    async def delete_attachment(
        self, 
        request: AttachmentDeleteRequest, 
        instance_name: str | None = None
    ) -> AttachmentDeleteResult:
        """Delete an attachment from an issue."""
        try:
            self._logger.info(
                f"Deleting attachment {request.attachment_id} from issue {request.issue_key}"
            )
            
            # Get Jira client
            client: Jira = self._client_factory.create_client(instance_name)
            
            # Delete the attachment
            # Note: The Atlassian library might not have a direct method for this,
            # so we use the raw API
            url = f"{client.url}/rest/api/2/attachment/{request.attachment_id}"
            response = client._session.delete(url)
            
            if response.status_code == 204:  # No Content - successful deletion
                self._logger.info(f"Attachment {request.attachment_id} deleted successfully")
                return AttachmentDeleteResult(
                    issue_key=request.issue_key,
                    attachment_id=request.attachment_id,
                    deleted=True
                )
            else:
                error_msg = f"Failed to delete attachment: HTTP {response.status_code}"
                self._logger.error(error_msg)
                return AttachmentDeleteResult(
                    issue_key=request.issue_key,
                    attachment_id=request.attachment_id,
                    deleted=False,
                    error=error_msg
                )
            
        except Exception as e:
            error_msg = f"Failed to delete attachment {request.attachment_id}: {str(e)}"
            self._logger.error(error_msg)
            return AttachmentDeleteResult(
                issue_key=request.issue_key,
                attachment_id=request.attachment_id,
                deleted=False,
                error=error_msg
            )

    async def get_attachment(
        self, 
        attachment_id: str, 
        instance_name: str | None = None
    ) -> JiraAttachment | None:
        """Get attachment details by ID."""
        try:
            self._logger.debug(f"Getting attachment details for ID: {attachment_id}")
            
            # Get Jira client
            client: Jira = self._client_factory.create_client(instance_name)
            
            # Get attachment details via API
            url = f"{client.url}/rest/api/2/attachment/{attachment_id}"
            response = client._session.get(url)
            
            if response.status_code == 200:
                attachment_data = response.json()
                attachment = convert_jira_attachment(attachment_data)
                self._logger.debug(f"Found attachment: {attachment.filename}")
                return attachment
            elif response.status_code == 404:
                self._logger.debug(f"Attachment not found: {attachment_id}")
                return None
            else:
                self._logger.error(f"Failed to get attachment: HTTP {response.status_code}")
                return None
            
        except Exception as e:
            self._logger.error(f"Failed to get attachment {attachment_id}: {str(e)}")
            return None

    async def download_attachment(
        self, 
        attachment_id: str, 
        instance_name: str | None = None
    ) -> bytes | None:
        """Download attachment content by ID."""
        try:
            self._logger.debug(f"Downloading attachment content for ID: {attachment_id}")
            
            # First get attachment metadata to get download URL
            attachment = await self.get_attachment(attachment_id, instance_name)
            if not attachment or not attachment.download_url:
                self._logger.error(f"No download URL available for attachment {attachment_id}")
                return None
            
            # Get Jira client for authenticated session
            client: Jira = self._client_factory.create_client(instance_name)
            
            # Download the attachment content
            response = client._session.get(attachment.download_url)
            
            if response.status_code == 200:
                self._logger.debug(f"Downloaded attachment content: {len(response.content)} bytes")
                return response.content
            else:
                self._logger.error(
                    f"Failed to download attachment: HTTP {response.status_code}"
                )
                return None
            
        except Exception as e:
            self._logger.error(f"Failed to download attachment {attachment_id}: {str(e)}")
            return None
