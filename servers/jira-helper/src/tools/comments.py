"""Comment and transition query operations for Jira issues."""

import logging
from typing import TypedDict

from jira_client import validate_issue_key
from collections.abc import Callable
from atlassian import Jira
from exceptions import JiraError, JiraValidationError, JiraApiError

logger = logging.getLogger(__name__)


class TransitionInfo(TypedDict):
    id: str
    name: str
    to_status: str


class CommentResult(TypedDict):
    key: str
    instance: str
    message: str


class TransitionsResult(TypedDict):
    key: str
    instance: str
    transitions: list[TransitionInfo]
    count: int


def add_comment_to_jira_ticket(
    issue_key: str,
    comment: str,
    instance_name: str | None = None,
    *,
    get_client: Callable[[], Jira],
) -> CommentResult:
    """Add a comment to an existing Jira ticket."""
    if not comment or not comment.strip():
        raise JiraValidationError("comment is required.")
    key = validate_issue_key(issue_key)
    name = instance_name
    client = get_client()
    try:
        client.issue_add_comment(key, comment)
        return {
            "key": key,
            "instance": name,
            "message": f"Successfully added comment to {key}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to add comment to {key}: {e}", instance_name=name)


def get_issue_transitions(
    issue_key: str, instance_name: str | None = None, *, get_client: Callable[[], Jira]
) -> TransitionsResult:
    """Get available workflow transitions for a Jira issue."""
    key = validate_issue_key(issue_key)
    name = instance_name
    client = get_client()
    try:
        transitions = client.get_issue_transitions(key)
        result = []
        for t in transitions:
            result.append(
                {
                    "id": t.get("id", ""),
                    "name": t.get("name", ""),
                    "to_status": t.get("to", {}).get("name", "") if t.get("to") else "",
                }
            )
        return {
            "key": key,
            "instance": name,
            "transitions": result,
            "count": len(result),
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(
            f"Failed to get transitions for {key}: {e}", instance_name=name
        )
