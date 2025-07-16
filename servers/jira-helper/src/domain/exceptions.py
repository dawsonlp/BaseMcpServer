"""
Domain exceptions for the Jira Helper.

This module contains domain-specific exceptions that represent business rule violations
and error conditions within the Jira domain.
"""


class JiraDomainException(Exception):
    """Base exception for all Jira domain errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class JiraInstanceNotFound(JiraDomainException):
    """Raised when a requested Jira instance is not found."""

    def __init__(self, instance_name: str, available_instances: list = None):
        available = ", ".join(available_instances) if available_instances else "none"
        message = f"Jira instance '{instance_name}' not found. Available instances: {available}"
        super().__init__(message, {"instance_name": instance_name, "available_instances": available_instances})


class JiraInstanceConfigurationError(JiraDomainException):
    """Raised when a Jira instance is misconfigured."""

    def __init__(self, instance_name: str, configuration_error: str):
        message = f"Configuration error for Jira instance '{instance_name}': {configuration_error}"
        super().__init__(message, {"instance_name": instance_name, "configuration_error": configuration_error})


class JiraConnectionError(JiraDomainException):
    """Raised when unable to connect to a Jira instance."""

    def __init__(self, instance_name: str, connection_error: str):
        message = f"Failed to connect to Jira instance '{instance_name}': {connection_error}"
        super().__init__(message, {"instance_name": instance_name, "connection_error": connection_error})


class JiraAuthenticationError(JiraDomainException):
    """Raised when authentication fails for a Jira instance."""

    def __init__(self, instance_name: str, auth_error: str):
        message = f"Authentication failed for Jira instance '{instance_name}': {auth_error}"
        super().__init__(message, {"instance_name": instance_name, "auth_error": auth_error})


class JiraProjectNotFound(JiraDomainException):
    """Raised when a requested Jira project is not found."""

    def __init__(self, project_key: str, instance_name: str):
        message = f"Project '{project_key}' not found in Jira instance '{instance_name}'"
        super().__init__(message, {"project_key": project_key, "instance_name": instance_name})


class JiraIssueNotFound(JiraDomainException):
    """Raised when a requested Jira issue is not found."""

    def __init__(self, issue_key: str, instance_name: str):
        message = f"Issue '{issue_key}' not found in Jira instance '{instance_name}'"
        super().__init__(message, {"issue_key": issue_key, "instance_name": instance_name})


class JiraIssueValidationError(JiraDomainException):
    """Raised when issue data fails validation."""

    def __init__(self, validation_error: str, issue_data: dict = None):
        message = f"Issue validation failed: {validation_error}"
        super().__init__(message, {"validation_error": validation_error, "issue_data": issue_data})


class JiraTransitionNotAvailable(JiraDomainException):
    """Raised when a requested workflow transition is not available."""

    def __init__(self, issue_key: str, transition_name: str, available_transitions: list = None):
        available = ", ".join(available_transitions) if available_transitions else "none"
        message = f"Transition '{transition_name}' not available for issue '{issue_key}'. Available transitions: {available}"
        super().__init__(message, {
            "issue_key": issue_key,
            "transition_name": transition_name,
            "available_transitions": available_transitions
        })


class JiraWorkflowError(JiraDomainException):
    """Raised when there's an error with workflow operations."""

    def __init__(self, workflow_error: str, issue_key: str = None):
        message = f"Workflow error: {workflow_error}"
        if issue_key:
            message += f" (Issue: {issue_key})"
        super().__init__(message, {"workflow_error": workflow_error, "issue_key": issue_key})


class JiraAssigneeError(JiraDomainException):
    """Raised when there's an error with assignee operations."""

    def __init__(self, assignee_error: str, issue_key: str, assignee: str = None):
        message = f"Assignee error for issue '{issue_key}': {assignee_error}"
        super().__init__(message, {"assignee_error": assignee_error, "issue_key": issue_key, "assignee": assignee})


class JiraCommentError(JiraDomainException):
    """Raised when there's an error with comment operations."""

    def __init__(self, comment_error: str, issue_key: str):
        message = f"Comment error for issue '{issue_key}': {comment_error}"
        super().__init__(message, {"comment_error": comment_error, "issue_key": issue_key})


class JiraPermissionError(JiraDomainException):
    """Raised when the user lacks permission for an operation."""

    def __init__(self, operation: str, resource: str, instance_name: str):
        message = f"Permission denied for operation '{operation}' on resource '{resource}' in instance '{instance_name}'"
        super().__init__(message, {"operation": operation, "resource": resource, "instance_name": instance_name})


class JiraCustomFieldError(JiraDomainException):
    """Raised when there's an error with custom field operations."""

    def __init__(self, field_error: str, field_id: str = None):
        message = f"Custom field error: {field_error}"
        if field_id:
            message += f" (Field ID: {field_id})"
        super().__init__(message, {"field_error": field_error, "field_id": field_id})


class JiraSearchError(JiraDomainException):
    """Raised when there's an error with search operations."""

    def __init__(self, search_error: str, jql: str = None):
        message = f"Search error: {search_error}"
        if jql:
            message += f" (JQL: {jql})"
        super().__init__(message, {"search_error": search_error, "jql": jql})


class JiraGraphGenerationError(JiraDomainException):
    """Raised when there's an error generating workflow graphs."""

    def __init__(self, graph_error: str, project_key: str = None, issue_type: str = None):
        message = f"Graph generation error: {graph_error}"
        if project_key and issue_type:
            message += f" (Project: {project_key}, Issue Type: {issue_type})"
        super().__init__(message, {
            "graph_error": graph_error,
            "project_key": project_key,
            "issue_type": issue_type
        })


class JiraGraphLibraryNotAvailable(JiraDomainException):
    """Raised when graph generation libraries are not available."""

    def __init__(self, missing_libraries: list = None):
        libraries = ", ".join(missing_libraries) if missing_libraries else "graphviz and/or networkx"
        message = f"Graph generation libraries not available: {libraries}"
        super().__init__(message, {"missing_libraries": missing_libraries})


class JiraRateLimitError(JiraDomainException):
    """Raised when Jira API rate limits are exceeded."""

    def __init__(self, instance_name: str, retry_after: int = None):
        message = f"Rate limit exceeded for Jira instance '{instance_name}'"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, {"instance_name": instance_name, "retry_after": retry_after})


class JiraTimeoutError(JiraDomainException):
    """Raised when Jira operations timeout."""

    def __init__(self, operation: str, instance_name: str, timeout_seconds: int):
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds for instance '{instance_name}'"
        super().__init__(message, {
            "operation": operation,
            "instance_name": instance_name,
            "timeout_seconds": timeout_seconds
        })


class JiraConfigurationMissingError(JiraDomainException):
    """Raised when required configuration is missing."""

    def __init__(self, missing_config: str):
        message = f"Required configuration missing: {missing_config}"
        super().__init__(message, {"missing_config": missing_config})


class JiraValidationError(JiraDomainException):
    """Raised when input validation fails."""

    def __init__(self, validation_errors: list):
        message = f"Validation failed: {'; '.join(validation_errors)}"
        super().__init__(message, {"validation_errors": validation_errors})


class InvalidLinkTypeError(JiraDomainException):
    """Raised when an invalid link type is specified."""

    def __init__(self, link_type: str, valid_types: list = None):
        valid = ", ".join(valid_types) if valid_types else "unknown"
        message = f"Invalid link type '{link_type}'. Valid types: {valid}"
        super().__init__(message, {"link_type": link_type, "valid_types": valid_types})


class CircularLinkError(JiraDomainException):
    """Raised when attempting to create a circular link relationship."""

    def __init__(self, source_issue: str, target_issue: str, link_type: str):
        message = f"Circular link detected: cannot link '{source_issue}' to '{target_issue}' with type '{link_type}'"
        super().__init__(message, {
            "source_issue": source_issue,
            "target_issue": target_issue,
            "link_type": link_type
        })


class InvalidJQLError(JiraDomainException):
    """Raised when JQL syntax is invalid."""

    def __init__(self, jql: str, syntax_error: str):
        message = f"Invalid JQL syntax: {syntax_error}. JQL: {jql}"
        super().__init__(message, {"jql": jql, "syntax_error": syntax_error})


class IssueUpdateError(JiraDomainException):
    """Raised when issue update operation fails."""

    def __init__(self, issue_key: str, update_error: str, failed_fields: list = None):
        message = f"Failed to update issue '{issue_key}': {update_error}"
        if failed_fields:
            message += f". Failed fields: {', '.join(failed_fields)}"
        super().__init__(message, {
            "issue_key": issue_key,
            "update_error": update_error,
            "failed_fields": failed_fields
        })


class IssueLinkError(JiraDomainException):
    """Raised when issue linking operation fails."""

    def __init__(self, source_issue: str, target_issue: str, link_type: str, link_error: str):
        message = f"Failed to link '{source_issue}' to '{target_issue}' with type '{link_type}': {link_error}"
        super().__init__(message, {
            "source_issue": source_issue,
            "target_issue": target_issue,
            "link_type": link_type,
            "link_error": link_error
        })


class LinkNotFoundError(JiraDomainException):
    """Raised when a requested issue link is not found."""

    def __init__(self, link_id: str = None, source_issue: str = None, target_issue: str = None):
        if link_id:
            message = f"Issue link with ID '{link_id}' not found"
        elif source_issue and target_issue:
            message = f"No link found between '{source_issue}' and '{target_issue}'"
        else:
            message = "Issue link not found"
        super().__init__(message, {
            "link_id": link_id,
            "source_issue": source_issue,
            "target_issue": target_issue
        })


class JQLSecurityError(JiraDomainException):
    """Raised when JQL contains potentially unsafe content."""

    def __init__(self, jql: str, security_issue: str):
        message = f"JQL security violation: {security_issue}. JQL: {jql}"
        super().__init__(message, {"jql": jql, "security_issue": security_issue})


class SearchLimitExceededError(JiraDomainException):
    """Raised when search parameters exceed allowed limits."""

    def __init__(self, limit_type: str, requested: int, maximum: int):
        message = f"Search {limit_type} limit exceeded: requested {requested}, maximum allowed {maximum}"
        super().__init__(message, {
            "limit_type": limit_type,
            "requested": requested,
            "maximum": maximum
        })


class EpicLinkError(JiraDomainException):
    """Raised when Epic linking operation fails."""

    def __init__(self, epic_key: str, story_key: str, epic_error: str):
        message = f"Failed to link story '{story_key}' to epic '{epic_key}': {epic_error}"
        super().__init__(message, {
            "epic_key": epic_key,
            "story_key": story_key,
            "epic_error": epic_error
        })


class LinkTypeNotSupportedError(JiraDomainException):
    """Raised when a link type is not supported by the Jira instance."""

    def __init__(self, link_type: str, instance_name: str, supported_types: list = None):
        supported = ", ".join(supported_types) if supported_types else "unknown"
        message = f"Link type '{link_type}' not supported by instance '{instance_name}'. Supported types: {supported}"
        super().__init__(message, {
            "link_type": link_type,
            "instance_name": instance_name,
            "supported_types": supported_types
        })


class IssueFieldUpdateError(JiraDomainException):
    """Raised when a specific field cannot be updated."""

    def __init__(self, issue_key: str, field_name: str, field_error: str):
        message = f"Cannot update field '{field_name}' on issue '{issue_key}': {field_error}"
        super().__init__(message, {
            "issue_key": issue_key,
            "field_name": field_name,
            "field_error": field_error
        })


class ConcurrentUpdateError(JiraDomainException):
    """Raised when an issue is updated concurrently by another user."""

    def __init__(self, issue_key: str, conflict_details: str):
        message = f"Concurrent update conflict for issue '{issue_key}': {conflict_details}"
        super().__init__(message, {
            "issue_key": issue_key,
            "conflict_details": conflict_details
        })


class TimeTrackingError(JiraDomainException):
    """Raised when there's an error with time tracking operations."""

    def __init__(self, issue_key: str, time_error: str):
        message = f"Time tracking error for issue '{issue_key}': {time_error}"
        super().__init__(message, {
            "issue_key": issue_key,
            "time_error": time_error
        })


class InvalidTimeFormatError(JiraDomainException):
    """Raised when time format is invalid."""

    def __init__(self, time_value: str, expected_format: str):
        message = f"Invalid time format '{time_value}'. Expected format: {expected_format}"
        super().__init__(message, {
            "time_value": time_value,
            "expected_format": expected_format
        })


class WorkLogError(JiraDomainException):
    """Raised when work log operations fail."""

    def __init__(self, issue_key: str, work_log_error: str):
        message = f"Work log error for issue '{issue_key}': {work_log_error}"
        super().__init__(message, {
            "issue_key": issue_key,
            "work_log_error": work_log_error
        })


class TimeEstimateError(JiraDomainException):
    """Raised when time estimate operations fail."""

    def __init__(self, issue_key: str, estimate_error: str):
        message = f"Time estimate error for issue '{issue_key}': {estimate_error}"
        super().__init__(message, {
            "issue_key": issue_key,
            "estimate_error": estimate_error
        })


class NegativeTimeError(JiraDomainException):
    """Raised when negative time values are provided."""

    def __init__(self, time_value: str, operation: str):
        message = f"Negative time value '{time_value}' not allowed for operation '{operation}'"
        super().__init__(message, {
            "time_value": time_value,
            "operation": operation
        })


class WorkLogNotFoundError(JiraDomainException):
    """Raised when a work log entry is not found."""

    def __init__(self, work_log_id: str, issue_key: str):
        message = f"Work log '{work_log_id}' not found for issue '{issue_key}'"
        super().__init__(message, {
            "work_log_id": work_log_id,
            "issue_key": issue_key
        })


class TimeTrackingNotEnabledError(JiraDomainException):
    """Raised when time tracking is not enabled for a project or issue type."""

    def __init__(self, project_key: str, issue_type: str = None):
        if issue_type:
            message = f"Time tracking not enabled for issue type '{issue_type}' in project '{project_key}'"
        else:
            message = f"Time tracking not enabled for project '{project_key}'"
        super().__init__(message, {
            "project_key": project_key,
            "issue_type": issue_type
        })
