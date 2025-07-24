"""
Consolidated Jira service combining core CRUD operations.

This service consolidates IssueService, ProjectService, and WorkflowService
into a single, focused service following KISS principles.
"""

from typing import Any

from utils.decorators import log_operation, validate_issue_key

from domain.base_service import BaseJiraService
from domain.exceptions import (
    JiraTransitionNotAvailable,
    JiraValidationError,
    JiraWorkflowError,
)
from domain.models import (
    AssigneeChangeRequest,
    CommentAddRequest,
    CustomFieldMapping,
    IssueCreateRequest,
    IssueTransitionRequest,
    JiraComment,
    JiraIssue,
    JiraProject,
    WorkflowTransition,
)
from domain.ports import (
    ConfigurationProvider,
    EventPublisher,
    JiraRepository,
    Logger,
)


class JiraService(BaseJiraService):
    """
    Consolidated service for core Jira operations.
    
    Combines issue management, project operations, and workflow functionality
    into a single, cohesive service following KISS principles.
    """

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        super().__init__(
            config_provider,
            logger,
            repository=repository,
            event_publisher=event_publisher
        )

    # ========================================
    # Issue Operations
    # ========================================

    @validate_issue_key
    @log_operation("get_issue")
    async def get_issue(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
        """Get a single issue by key."""
        instance_name = self._resolve_instance_name(instance_name)
        return await self._repository.get_issue(issue_key, instance_name)

    @validate_issue_key
    @log_operation("get_issue_with_comments")
    async def get_issue_with_comments(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
        """Get a single issue with all its comments."""
        instance_name = self._resolve_instance_name(instance_name)
        return await self._repository.get_issue_with_comments(issue_key, instance_name)

    async def create_issue(self, request: IssueCreateRequest, instance_name: str | None = None) -> JiraIssue:
        """Create a new issue."""
        self._validate_create_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            issue = await self._repository.create_issue(request, instance_name)
            self._logger.info(f"Created issue {issue.key} in project {request.project_key}")

            if self._event_publisher:
                await self._event_publisher.publish_issue_created(issue, instance_name)

            return issue
        except Exception as e:
            self._logger.error(f"Failed to create issue in project {request.project_key}: {str(e)}")
            raise

    async def add_comment(self, request: CommentAddRequest, instance_name: str | None = None) -> JiraComment:
        """Add a comment to an issue."""
        self._validate_comment_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            comment = await self._repository.add_comment(request, instance_name)
            self._logger.info(f"Added comment to issue {request.issue_key}")

            if self._event_publisher:
                await self._event_publisher.publish_comment_added(request.issue_key, comment, instance_name)

            return comment
        except Exception as e:
            self._logger.error(f"Failed to add comment to issue {request.issue_key}: {str(e)}")
            raise

    # ========================================
    # Project Operations
    # ========================================

    async def get_projects(self, instance_name: str | None = None) -> list[JiraProject]:
        """Get all projects from a Jira instance."""
        instance_name = self._resolve_instance_name(instance_name)

        try:
            projects = await self._repository.get_projects(instance_name)
            self._logger.debug(f"Retrieved {len(projects)} projects from instance {instance_name}")
            return projects
        except Exception as e:
            self._logger.error(f"Failed to get projects from instance {instance_name}: {str(e)}")
            raise

    async def get_custom_field_mappings(self, reverse: bool = False, instance_name: str | None = None) -> list[CustomFieldMapping]:
        """Get custom field mappings."""
        instance_name = self._resolve_instance_name(instance_name)

        try:
            mappings = await self._repository.get_custom_field_mappings(reverse, instance_name)
            self._logger.debug(f"Retrieved {len(mappings)} custom field mappings from instance {instance_name}")
            return mappings
        except Exception as e:
            self._logger.error(f"Failed to get custom field mappings from instance {instance_name}: {str(e)}")
            raise

    # ========================================
    # Workflow Operations
    # ========================================

    async def get_available_transitions(self, issue_key: str, instance_name: str | None = None) -> list[WorkflowTransition]:
        """Get available transitions for an issue."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            transitions = await self._repository.get_available_transitions(issue_key, instance_name)
            self._logger.debug(f"Found {len(transitions)} available transitions for issue {issue_key}")
            return transitions
        except Exception as e:
            self._logger.error(f"Failed to get transitions for issue {issue_key}: {str(e)}")
            raise

    async def transition_issue(self, request: IssueTransitionRequest, instance_name: str | None = None) -> JiraIssue:
        """Transition an issue through workflow."""
        self._validate_transition_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        # Get current issue state
        current_issue = await self._repository.get_issue(request.issue_key, instance_name)
        old_status = current_issue.status

        # Get available transitions
        available_transitions = await self._repository.get_available_transitions(request.issue_key, instance_name)

        # Validate transition is available
        transition_names = [t.name for t in available_transitions]
        if request.transition_name not in transition_names:
            raise JiraTransitionNotAvailable(request.issue_key, request.transition_name, transition_names)

        try:
            updated_issue = await self._repository.transition_issue(request, instance_name)
            self._logger.info(f"Transitioned issue {request.issue_key} from {old_status} to {updated_issue.status}")

            if self._event_publisher:
                await self._event_publisher.publish_issue_transitioned(
                    updated_issue, old_status, updated_issue.status, instance_name
                )

            return updated_issue
        except Exception as e:
            self._logger.error(f"Failed to transition issue {request.issue_key}: {str(e)}")
            raise JiraWorkflowError(str(e), request.issue_key)

    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: str | None = None) -> JiraIssue:
        """Change the assignee of an issue."""
        self._validate_assignee_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        # Get current issue state
        current_issue = await self._repository.get_issue(request.issue_key, instance_name)
        old_assignee = current_issue.assignee

        try:
            updated_issue = await self._repository.change_assignee(request, instance_name)
            self._logger.info(f"Changed assignee for issue {request.issue_key} from {old_assignee} to {updated_issue.assignee}")

            if self._event_publisher:
                await self._event_publisher.publish_assignee_changed(
                    updated_issue, old_assignee, updated_issue.assignee, instance_name
                )

            return updated_issue
        except Exception as e:
            self._logger.error(f"Failed to change assignee for issue {request.issue_key}: {str(e)}")
            raise

    # ========================================
    # Private Validation Methods
    # ========================================

    def _validate_create_request(self, request: IssueCreateRequest) -> None:
        """Validate issue creation request."""
        errors = []

        if not request.project_key or not request.project_key.strip():
            errors.append("Project key cannot be empty")

        if not request.summary or not request.summary.strip():
            errors.append("Summary cannot be empty")

        if not request.description or not request.description.strip():
            errors.append("Description cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    def _validate_comment_request(self, request: CommentAddRequest) -> None:
        """Validate comment addition request."""
        errors = []

        if not request.issue_key or not request.issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not request.comment or not request.comment.strip():
            errors.append("Comment cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    def _validate_transition_request(self, request: IssueTransitionRequest) -> None:
        """Validate transition request."""
        errors = []

        if not request.issue_key or not request.issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not request.transition_name or not request.transition_name.strip():
            errors.append("Transition name cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    def _validate_assignee_request(self, request: AssigneeChangeRequest) -> None:
        """Validate assignee change request."""
        if not request.issue_key or not request.issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])
