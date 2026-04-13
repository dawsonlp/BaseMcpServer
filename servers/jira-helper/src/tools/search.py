"""Search operations: JQL search, project ticket listing, JQL validation."""

import logging
import re

from jira_client import get_jira_client, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError
from output_sanitizer import sanitize_string, truncate_string

logger = logging.getLogger(__name__)

_FORBIDDEN_PATTERNS = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|ALTER|INSERT|UPDATE)\b", re.IGNORECASE
)
MAX_JQL_LENGTH = 4000


def _extract_issue(issue: dict) -> dict:
    """Extract standard fields from a raw Jira issue dict."""
    fields = issue.get("fields", {})
    raw_summary = fields.get("summary", "")
    return {
        "key": issue.get("key", ""),
        "summary": truncate_string(sanitize_string(raw_summary), 200),
        "status": fields.get("status", {}).get("name", "") if fields.get("status") else "",
        "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
        "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
        "issue_type": fields.get("issuetype", {}).get("name", "") if fields.get("issuetype") else "",
        "project": fields.get("project", {}).get("key", "") if fields.get("project") else "",
    }


def search_jira_issues(jql: str, max_results: int = 20, instance_name: str = None, **kwargs) -> dict:
    """Execute a JQL search query to find Jira issues."""
    if not jql or not jql.strip():
        raise JiraValidationError("JQL query is required.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        result = client.jql(jql, limit=max_results)
        issues_raw = result.get("issues", []) if isinstance(result, dict) else []
        issues = [_extract_issue(i) for i in issues_raw]
        return {
            "instance": name,
            "jql": jql,
            "issues": issues,
            "total": result.get("total", len(issues)) if isinstance(result, dict) else len(issues),
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"JQL search failed: {e}", instance_name=name)


def list_project_tickets(
    project_key: str, status: str = None, assignee: str = None,
    issue_type: str = None, max_results: int = 20,
    instance_name: str = None, **kwargs
) -> dict:
    """List tickets in a Jira project with optional filtering."""
    if not project_key:
        raise JiraValidationError("project_key is required.")
    clauses = [f'project = "{project_key.strip().upper()}"']
    if status:
        clauses.append(f'status = "{status}"')
    if assignee:
        clauses.append(f'assignee = "{assignee}"')
    if issue_type:
        clauses.append(f'issuetype = "{issue_type}"')
    jql = " AND ".join(clauses) + " ORDER BY updated DESC"
    return search_jira_issues(jql=jql, max_results=max_results, instance_name=instance_name)


def validate_jql_query(jql: str, **kwargs) -> dict:
    """Validate JQL syntax without executing the query."""
    issues = []
    if not jql or not jql.strip():
        return {"valid": False, "jql": jql or "", "issues": ["JQL query is empty."]}
    if len(jql) > MAX_JQL_LENGTH:
        issues.append(f"JQL exceeds maximum length of {MAX_JQL_LENGTH} characters.")
    if _FORBIDDEN_PATTERNS.search(jql):
        issues.append("JQL contains forbidden SQL keywords.")
    return {"valid": len(issues) == 0, "jql": jql, "issues": issues}