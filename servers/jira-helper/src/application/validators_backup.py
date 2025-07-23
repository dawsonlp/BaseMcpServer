"""
Application layer validators.

Minimal validation - let Jira be the authoritative validator for business rules.
Only validate obviously malformed input (null/empty values).
"""

from domain.exceptions import JiraValidationError


class BaseValidator:
    """Base validator with common validation patterns."""

    @staticmethod
    def validate_required_fields(**fields) -> None:
        """Validate that required fields are not empty."""
        errors = []
        
        for field_name, field_value in fields.items():
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                # Convert snake_case to human readable
                readable_name = field_name.replace('_', ' ').title()
                errors.append(f"{readable_name} cannot be empty")
        
        if errors:
            raise JiraValidationError(errors)

    @staticmethod
    def validate_at_least_one(**fields) -> None:
        """Validate that at least one field is provided."""
        if not any(field_value for field_value in fields.values()):
            field_names = ', '.join(field_name.replace('_', ' ') for field_name in fields.keys())
            raise JiraValidationError([f"At least one of the following must be provided: {field_names}"])

    @staticmethod
    def validate_positive_number(value: int, field_name: str) -> None:
        """Validate that a number is positive."""
        if value <= 0:
            readable_name = field_name.replace('_', ' ').title()
            raise JiraValidationError([f"{readable_name} must be greater than 0"])

    @staticmethod
    def validate_non_negative_number(value: int, field_name: str) -> None:
        """Validate that a number is non-negative."""
        if value < 0:
            readable_name = field_name.replace('_', ' ').title()
            raise JiraValidationError([f"{readable_name} cannot be negative"])


# All specific validators now just use the base validator
class IssueValidator(BaseValidator):
    """Validator for issue operations."""

    @staticmethod
    def validate_create_request(project_key: str, summary: str, description: str, issue_type: str) -> None:
        """Only validate required fields are not empty."""
        BaseValidator.validate_required_fields(
            project_key=project_key,
            summary=summary,
            issue_type=issue_type
        )

    @staticmethod
    def validate_issue_key(issue_key: str) -> None:
        """Only validate issue key is not empty."""
        BaseValidator.validate_required_fields(issue_key=issue_key)

    @staticmethod
    def validate_transition_request(issue_key: str, transition_name: str) -> None:
        """Only validate required fields are not empty."""
        BaseValidator.validate_required_fields(
            issue_key=issue_key,
            transition_name=transition_name
        )

    @staticmethod
    def validate_assignee_request(issue_key: str) -> None:
        """Only validate issue key is not empty."""
        BaseValidator.validate_required_fields(issue_key=issue_key)

    @staticmethod
    def validate_comment_request(issue_key: str, comment: str) -> None:
        """Only validate required fields are not empty."""
        BaseValidator.validate_required_fields(
            issue_key=issue_key,
            comment=comment
        )

    @staticmethod
    def validate_update_request(issue_key: str, fields: dict) -> None:
        """Only validate basic requirements."""
        BaseValidator.validate_required_fields(issue_key=issue_key)
        if not fields:
            raise JiraValidationError(["At least one field must be provided for update"])


class ProjectValidator(BaseValidator):
    """Validator for project operations."""

    @staticmethod
    def validate_project_key(project_key: str) -> None:
        """Only validate project key is not empty."""
        BaseValidator.validate_required_fields(project_key=project_key)


class SearchValidator(BaseValidator):
    """Validator for search operations."""

    @staticmethod
    def validate_search_query(jql: str, max_results: int, start_at: int) -> None:
        """Only validate basic requirements."""
        BaseValidator.validate_required_fields(jql=jql)
        BaseValidator.validate_positive_number(max_results, "max_results")
        BaseValidator.validate_non_negative_number(start_at, "start_at")


class LinkValidator(BaseValidator):
    """Validator for issue linking operations."""

    @staticmethod
    def validate_link_request(link_type: str, source_issue: str, target_issue: str) -> None:
        """Only validate required fields are not empty."""
        BaseValidator.validate_required_fields(
            source_issue=source_issue,
            target_issue=target_issue,
            link_type=link_type
        )


class TimeTrackingValidator(BaseValidator):
    """Validator for time tracking operations."""

    @staticmethod
    def validate_work_log_request(issue_key: str, time_spent: str) -> None:
        """Only validate required fields are not empty."""
        BaseValidator.validate_required_fields(
            issue_key=issue_key,
            time_spent=time_spent
        )

    @staticmethod
    def validate_time_estimate_update(issue_key: str, original_estimate: str | None, remaining_estimate: str | None) -> None:
        """Only validate basic requirements."""
        BaseValidator.validate_required_fields(issue_key=issue_key)
        BaseValidator.validate_at_least_one(
            original_estimate=original_estimate,
            remaining_estimate=remaining_estimate
        )


class WorkflowValidator(BaseValidator):
    """Validator for workflow operations."""

    @staticmethod
    def validate_workflow_graph(project_key: str, issue_type: str) -> None:
        """Only validate required fields are not empty."""
        BaseValidator.validate_required_fields(
            project_key=project_key,
            issue_type=issue_type
        )
