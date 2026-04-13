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