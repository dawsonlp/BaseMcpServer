"""File attachment operations: upload, list, delete."""

import logging
import os

from jira_client import get_jira_client, validate_issue_key, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def upload_file_to_jira(
    issue_key: str, file_path: str, instance_name: str = None, **kwargs
) -> dict:
    """Upload a file to a Jira issue as an attachment."""
    key = validate_issue_key(issue_key)
    if not file_path:
        raise JiraValidationError("file_path is required.")
    if not os.path.exists(file_path):
        raise JiraValidationError(f"File not found: {file_path}")
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise JiraValidationError(
            f"File too large: {file_size / (1024*1024):.1f} MB. Maximum is 25 MB."
        )
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        result = client.add_attachment(key, file_path)
        filename = os.path.basename(file_path)
        return {
            "key": key, "instance": name, "filename": filename,
            "size": file_size,
            "message": f"Successfully uploaded {filename} to {key}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to upload file to {key}: {e}", instance_name=name)


def list_issue_attachments(issue_key: str, instance_name: str = None, **kwargs) -> dict:
    """List all attachments for a Jira issue."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        issue = client.issue(key, fields="attachment")
        attachments_raw = issue.get("fields", {}).get("attachment", [])
        attachments = []
        for a in attachments_raw:
            attachments.append({
                "id": a.get("id", ""),
                "filename": a.get("filename", ""),
                "size": a.get("size", 0),
                "mime_type": a.get("mimeType", ""),
                "created": a.get("created", ""),
                "author": a.get("author", {}).get("displayName", "") if a.get("author") else "",
            })
        return {"key": key, "instance": name, "attachments": attachments, "count": len(attachments)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to list attachments for {key}: {e}", instance_name=name)


def delete_issue_attachment(
    attachment_id: str, instance_name: str = None, **kwargs
) -> dict:
    """Delete an attachment from a Jira issue."""
    if not attachment_id:
        raise JiraValidationError("attachment_id is required.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        client.delete_attachment(attachment_id)
        return {
            "attachment_id": attachment_id, "instance": name,
            "message": f"Successfully deleted attachment {attachment_id}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to delete attachment {attachment_id}: {e}", instance_name=name)