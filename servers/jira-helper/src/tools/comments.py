"""Comment and transition query operations for Jira issues."""

import logging

from jira_client import get_jira_client, validate_issue_key, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError

logger = logging.getLogger(__name__)


def add_comment_to_jira_ticket(
    issue_key: str, comment: str, instance_name: str = None, **kwargs
) -> dict:
    """Add a comment to an existing Jira ticket."""
    if not comment or not comment.strip():
        raise JiraValidationError("comment is required.")
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        client.issue_add_comment(key, comment)
        return {"key": key, "instance": name, "message": f"Successfully added comment to {key}"}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to add comment to {key}: {e}", instance_name=name)


def get_issue_transitions(issue_key: str, instance_name: str = None, **kwargs) -> dict:
    """Get available workflow transitions for a Jira issue."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        transitions = client.get_issue_transitions(key)
        result = []
        for t in transitions:
            result.append({
                "id": t.get("id", ""),
                "name": t.get("name", ""),
                "to_status": t.get("to", {}).get("name", "") if t.get("to") else "",
            })
        return {"key": key, "instance": name, "transitions": result, "count": len(result)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get transitions for {key}: {e}", instance_name=name)