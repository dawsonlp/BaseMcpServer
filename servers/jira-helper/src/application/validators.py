"""
Application layer validators.

This module contains validation logic extracted from domain models,
following proper hexagonal architecture principles.
"""

from typing import Any

from domain.exceptions import JiraValidationError


class IssueValidator:
    """Validator for issue-related operations."""

    @staticmethod
    def validate_create_request(project_key: str, summary: str, description: str, issue_type: str) -> None:
        """Validate issue creation request."""
        errors = []

        if not project_key or not project_key.strip():
            errors.append("Project key cannot be empty")

        if not summary or not summary.strip():
            errors.append("Summary cannot be empty")

        if not description or not description.strip():
            errors.append("Description cannot be empty")

        if not issue_type or not issue_type.strip():
            errors.append("Issue type cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_issue_key(issue_key: str) -> None:
        """Validate issue key format."""
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

        if "-" not in issue_key:
            raise JiraValidationError([
                "Issue key must contain project key and number (e.g., PROJ-123)"
            ])

    @staticmethod
    def validate_transition_request(issue_key: str, transition_name: str) -> None:
        """Validate transition request."""
        errors = []

        if not issue_key or not issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not transition_name or not transition_name.strip():
            errors.append("Transition name cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_assignee_request(issue_key: str) -> None:
        """Validate assignee change request."""
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

    @staticmethod
    def validate_comment_request(issue_key: str, comment: str) -> None:
        """Validate comment addition request."""
        errors = []

        if not issue_key or not issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not comment or not comment.strip():
            errors.append("Comment cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_update_request(issue_key: str, fields: dict[str, Any]) -> None:
        """Validate issue update request."""
        errors = []

        if not issue_key or not issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not fields:
            errors.append("At least one field must be provided for update")

        if errors:
            raise JiraValidationError(errors)


class ProjectValidator:
    """Validator for project-related operations."""

    @staticmethod
    def validate_project_key(project_key: str) -> None:
        """Validate project key."""
        if not project_key or not project_key.strip():
            raise JiraValidationError(["Project key cannot be empty"])

    @staticmethod
    def validate_required_fields(name: str, url: str, user: str, token: str) -> None:
        """Validate required fields for Jira instance."""
        errors = []

        if not name or not name.strip():
            errors.append("Name cannot be empty")

        if not url or not url.strip():
            errors.append("URL cannot be empty")

        if not user or not user.strip():
            errors.append("User cannot be empty")

        if not token or not token.strip():
            errors.append("Token cannot be empty")

        if errors:
            raise JiraValidationError(errors)


class SearchValidator:
    """Validator for search-related operations."""

    @staticmethod
    def validate_search_query(jql: str, max_results: int, start_at: int) -> None:
        """Validate search query parameters."""
        errors = []

        if not jql or not jql.strip():
            errors.append("JQL query cannot be empty")

        if max_results <= 0:
            errors.append("Max results must be greater than 0")

        if max_results > 1000:
            errors.append("Max results cannot exceed 1000")

        if start_at < 0:
            errors.append("Start at cannot be negative")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_search_filters(project_key: str, max_results: int, start_at: int) -> None:
        """Validate search filters parameters."""
        errors = []

        if not project_key or not project_key.strip():
            errors.append("Project key cannot be empty")

        if max_results <= 0:
            errors.append("Max results must be greater than 0")

        if max_results > 1000:
            errors.append("Max results cannot exceed 1000")

        if start_at < 0:
            errors.append("Start at cannot be negative")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_search_result(total_results: int, start_at: int, max_results: int) -> None:
        """Validate search result parameters."""
        errors = []

        if total_results < 0:
            errors.append("Total results cannot be negative")

        if start_at < 0:
            errors.append("Start at cannot be negative")

        if max_results <= 0:
            errors.append("Max results must be greater than 0")

        if errors:
            raise JiraValidationError(errors)


class LinkValidator:
    """Validator for issue linking operations."""

    @staticmethod
    def validate_link_request(link_type: str, source_issue: str, target_issue: str) -> None:
        """Validate link creation request."""
        errors = []

        if not source_issue or not source_issue.strip():
            errors.append("Source issue cannot be empty")

        if not target_issue or not target_issue.strip():
            errors.append("Target issue cannot be empty")

        if not link_type or not link_type.strip():
            errors.append("Link type cannot be empty")

        if source_issue == target_issue:
            errors.append("Cannot link an issue to itself")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_link_direction(direction: str) -> None:
        """Validate link direction."""
        valid_directions = ["inward", "outward"]
        if direction not in valid_directions:
            raise JiraValidationError([f"Invalid link direction: {direction}"])


class TimeTrackingValidator:
    """Validator for time tracking operations."""

    @staticmethod
    def validate_work_log_request(issue_key: str, time_spent: str) -> None:
        """Validate work log request."""
        errors = []

        if not issue_key or not issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not time_spent or not time_spent.strip():
            errors.append("Time spent cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_time_estimate_update(issue_key: str, original_estimate: str | None, remaining_estimate: str | None) -> None:
        """Validate time estimate update."""
        errors = []

        if not issue_key or not issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not original_estimate and not remaining_estimate:
            errors.append("At least one estimate must be provided")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_adjust_estimate_options(adjust_estimate: str, new_estimate: str | None, reduce_by: str | None) -> None:
        """Validate adjust estimate options."""
        valid_adjust_options = ["new", "leave", "manual", "auto"]
        if adjust_estimate not in valid_adjust_options:
            raise JiraValidationError([f"Adjust estimate must be one of: {', '.join(valid_adjust_options)}"])

        if adjust_estimate == "new" and not new_estimate:
            raise JiraValidationError(["New estimate is required when adjust_estimate is 'new'"])

        if adjust_estimate == "manual" and not reduce_by:
            raise JiraValidationError(["Reduce by is required when adjust_estimate is 'manual'"])

    @staticmethod
    def validate_time_values(time_spent_seconds: int, original_estimate_seconds: int = 0, remaining_estimate_seconds: int = 0) -> None:
        """Validate time values are not negative."""
        errors = []

        if time_spent_seconds < 0:
            errors.append("Time spent cannot be negative")

        if original_estimate_seconds < 0:
            errors.append("Original estimate cannot be negative")

        if remaining_estimate_seconds < 0:
            errors.append("Remaining estimate cannot be negative")

        if errors:
            raise JiraValidationError(errors)


class WorkflowValidator:
    """Validator for workflow operations."""

    @staticmethod
    def validate_workflow_graph(project_key: str, issue_type: str) -> None:
        """Validate workflow graph parameters."""
        errors = []

        if not project_key or not project_key.strip():
            errors.append("Project key cannot be empty")

        if not issue_type or not issue_type.strip():
            errors.append("Issue type cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_workflow_node(node_id: str, name: str, category: str, color: str) -> None:
        """Validate workflow node parameters."""
        errors = []

        if not node_id or not node_id.strip():
            errors.append("Node ID cannot be empty")

        if not name or not name.strip():
            errors.append("Node name cannot be empty")

        if not category or not category.strip():
            errors.append("Node category cannot be empty")

        if not color or not color.strip():
            errors.append("Node color cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_workflow_edge(from_node: str, to_node: str, label: str) -> None:
        """Validate workflow edge parameters."""
        errors = []

        if not from_node or not from_node.strip():
            errors.append("From node cannot be empty")

        if not to_node or not to_node.strip():
            errors.append("To node cannot be empty")

        if not label or not label.strip():
            errors.append("Edge label cannot be empty")

        if errors:
            raise JiraValidationError(errors)


class CommentValidator:
    """Validator for comment operations."""

    @staticmethod
    def validate_comment_fields(comment_id: str, author_name: str, body: str, created: str) -> None:
        """Validate comment required fields."""
        errors = []

        if not comment_id or not comment_id.strip():
            errors.append("Comment ID cannot be empty")

        if not author_name or not author_name.strip():
            errors.append("Author name cannot be empty")

        if not body or not body.strip():
            errors.append("Comment body cannot be empty")

        if not created or not created.strip():
            errors.append("Created date cannot be empty")

        if errors:
            raise JiraValidationError(errors)


class CustomFieldValidator:
    """Validator for custom field operations."""

    @staticmethod
    def validate_custom_field_mapping(field_id: str, name: str) -> None:
        """Validate custom field mapping."""
        errors = []

        if not field_id or not field_id.strip():
            errors.append("Field ID cannot be empty")

        if not name or not name.strip():
            errors.append("Field name cannot be empty")

        if errors:
            raise JiraValidationError(errors)
