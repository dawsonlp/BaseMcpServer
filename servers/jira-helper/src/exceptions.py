"""
Simplified exception hierarchy for Jira Helper MCP Server.

Collapsed from 30+ exceptions to 7 practical classes.
Most callers catch the base class, so fine-grained hierarchy added no value.
"""


class JiraError(Exception):
    """Base exception for all Jira operations."""

    def __init__(self, message: str, instance_name: str = None):
        self.instance_name = instance_name
        super().__init__(message)


class JiraConnectionError(JiraError):
    """Failed to connect to Jira instance (network, DNS, timeout)."""

    pass


class JiraAuthenticationError(JiraError):
    """Authentication or authorization failure."""

    pass


class JiraNotFoundError(JiraError):
    """Requested resource not found (issue, project, attachment, etc)."""

    pass


class JiraValidationError(JiraError):
    """Input validation failure (bad issue key, empty field, invalid JQL, etc)."""

    pass


class JiraPermissionError(JiraError):
    """Insufficient permissions for the requested operation."""

    pass


class JiraApiError(JiraError):
    """Catch-all for unexpected Jira API errors."""

    pass


class JiraGraphError(JiraError):
    """Workflow graph generation failure."""

    pass


def public_error_message(error: JiraError) -> str:
    """Render expected failures without forwarding upstream bodies or credentials."""
    # HTTP failures may be wrapped by ordinary domain exceptions. Inspect structured
    # status rather than searching exception text, which can contain arbitrary data.
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        status = getattr(getattr(current, "response", None), "status_code", None)
        if status == 401:
            return "Atlassian authentication failed. Check credentials for the selected instance."
        if status == 403:
            return "Atlassian denied this operation. Check permissions for the selected instance."
        if status == 404:
            return "The requested Atlassian object was not found or is not visible to this account."
        current = current.__cause__ or current.__context__
    if isinstance(error, (JiraValidationError, JiraNotFoundError)):
        return str(
            error
        )  # These are locally authored validation/configuration messages.
    if isinstance(error, JiraAuthenticationError):
        return "Atlassian authentication failed. Check credentials for the selected instance."
    if isinstance(error, JiraPermissionError):
        return "Atlassian denied this operation. Check permissions for the selected instance."
    if isinstance(error, JiraConnectionError):
        return "Could not reach the selected Atlassian instance. Check connectivity and configuration; verify any write before retrying."
    if isinstance(error, JiraGraphError):
        return "Workflow graph generation failed. Check the server log for details."
    return "The Atlassian operation failed. Check the server log and verify any write before retrying."
