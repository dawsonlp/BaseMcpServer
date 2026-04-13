"""Time tracking operations: work logs, estimates."""

import logging
import re

from jira_client import get_jira_client, validate_issue_key, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError

logger = logging.getLogger(__name__)

_TIME_FORMAT = re.compile(r"^(\d+[wdhm]\s*)+$", re.IGNORECASE)


def log_work(
    issue_key: str, time_spent: str, comment: str = None,
    started: str = None, instance_name: str = None, **kwargs
) -> dict:
    """Log work time on a Jira issue."""
    key = validate_issue_key(issue_key)
    if not time_spent or not time_spent.strip():
        raise JiraValidationError("time_spent is required (e.g. '2h', '30m', '1d 4h').")
    if not _TIME_FORMAT.match(time_spent.strip()):
        raise JiraValidationError(f"Invalid time format: '{time_spent}'. Use format like '2h', '30m', '1d 4h'.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        worklog_data = {"timeSpent": time_spent.strip()}
        if comment:
            worklog_data["comment"] = comment
        if started:
            worklog_data["started"] = started
        client.issue_worklog(key, **worklog_data)
        return {
            "key": key, "instance": name, "time_spent": time_spent.strip(),
            "message": f"Successfully logged {time_spent.strip()} on {key}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to log work on {key}: {e}", instance_name=name)


def get_work_logs(issue_key: str, instance_name: str = None, **kwargs) -> dict:
    """Get work log entries for a Jira issue."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        # Try dedicated worklog endpoint first
        try:
            worklogs_data = client.issue_get_worklogs(key)
        except (AttributeError, TypeError):
            issue = client.issue(key, fields="worklog")
            worklogs_data = issue.get("fields", {}).get("worklog", {})

        raw = worklogs_data.get("worklogs", []) if isinstance(worklogs_data, dict) else []
        worklogs = []
        for w in raw:
            worklogs.append({
                "id": w.get("id", ""),
                "author": w.get("author", {}).get("displayName", "") if w.get("author") else "",
                "time_spent": w.get("timeSpent", ""),
                "time_spent_seconds": w.get("timeSpentSeconds", 0),
                "started": w.get("started", ""),
                "comment": w.get("comment", ""),
            })
        return {"key": key, "instance": name, "worklogs": worklogs, "count": len(worklogs)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get worklogs for {key}: {e}", instance_name=name)


def get_time_tracking_info(issue_key: str, instance_name: str = None, **kwargs) -> dict:
    """Get time tracking information for a Jira issue."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        issue = client.issue(key, fields="timetracking")
        tt = issue.get("fields", {}).get("timetracking", {})
        return {
            "key": key, "instance": name,
            "time_tracking": {
                "original_estimate": tt.get("originalEstimate", ""),
                "remaining_estimate": tt.get("remainingEstimate", ""),
                "time_spent": tt.get("timeSpent", ""),
                "original_estimate_seconds": tt.get("originalEstimateSeconds", 0),
                "remaining_estimate_seconds": tt.get("remainingEstimateSeconds", 0),
                "time_spent_seconds": tt.get("timeSpentSeconds", 0),
            },
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get time tracking for {key}: {e}", instance_name=name)


def update_time_estimates(
    issue_key: str, original_estimate: str = None,
    remaining_estimate: str = None, instance_name: str = None, **kwargs
) -> dict:
    """Update time estimates for a Jira issue."""
    key = validate_issue_key(issue_key)
    if not original_estimate and not remaining_estimate:
        raise JiraValidationError("At least one of original_estimate or remaining_estimate is required.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        tt = {}
        if original_estimate:
            tt["originalEstimate"] = original_estimate
        if remaining_estimate:
            tt["remainingEstimate"] = remaining_estimate
        client.issue_update(key, fields={"timetracking": tt})
        return {
            "key": key, "instance": name, "updated": tt,
            "message": f"Successfully updated time estimates for {key}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to update time estimates for {key}: {e}", instance_name=name)