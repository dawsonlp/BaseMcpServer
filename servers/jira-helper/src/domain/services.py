"""
Domain services for the Jira Helper.

This module contains domain services that implement core business logic.
These services orchestrate domain entities and enforce business rules.
"""

from typing import Any

from utils.decorators import log_operation, validate_issue_key

from .base_service import BaseJiraService
from .exceptions import (
    CircularLinkError,
    EpicLinkError,
    InvalidJQLError,
    InvalidTimeFormatError,
    IssueLinkError,
    IssueUpdateError,
    JiraGraphGenerationError,
    JiraGraphLibraryNotAvailable,
    JiraInstanceNotFound,
    JiraIssueNotFound,
    JiraTransitionNotAvailable,
    JiraValidationError,
    JiraWorkflowError,
    JQLSecurityError,
    LinkNotFoundError,
    LinkTypeNotSupportedError,
    NegativeTimeError,
    TimeEstimateError,
    TimeTrackingError,
    TimeTrackingNotEnabledError,
    WorkLogError,
    WorkLogNotFoundError,
)
from .jql_builder import JQLBuilderFactory, validate_jql_safety
from .models import (
    AssigneeChangeRequest,
    CommentAddRequest,
    CustomFieldMapping,
    IssueCreateRequest,
    IssueLink,
    IssueLinkResult,
    IssueTransitionRequest,
    IssueUpdate,
    IssueUpdateResult,
    JiraComment,
    JiraInstance,
    JiraIssue,
    JiraProject,
    LinkDirection,
    LinkType,
    SearchFilters,
    SearchQuery,
    SearchResult,
    TimeEstimateResult,
    TimeEstimateUpdate,
    TimeTrackingInfo,
    WorkflowGraph,
    WorkflowTransition,
    WorkLog,
    WorkLogRequest,
    WorkLogResult,
)
from .ports import (
    ConfigurationProvider,
    EventPublisher,
    GraphGenerator,
    IssueLinkPort,
    IssueSearchPort,
    IssueUpdatePort,
    JiraRepository,
    JQLValidator,
    LinkTypeMapper,
    Logger,
    TimeFormatValidator,
    TimeTrackingPort,
    WorkflowAnalyzer,
)


class IssueService(BaseJiraService):
    """Domain service for issue-related operations."""

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        super().__init__(config_provider, logger, repository=repository, event_publisher=event_publisher)

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


    def _validate_issue_key(self, issue_key: str) -> None:
        """Validate issue key format."""
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

        if "-" not in issue_key:
            raise JiraValidationError(["Issue key must contain project key and number (e.g., PROJ-123)"])

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

    def _validate_project_key(self, project_key: str) -> None:
        """Validate project key."""
        if not project_key or not project_key.strip():
            raise JiraValidationError(["Project key cannot be empty"])

    def _validate_max_results(self, max_results: int) -> None:
        """Validate max results parameter."""
        if max_results <= 0:
            raise JiraValidationError(["Max results must be greater than 0"])

        if max_results > 1000:
            raise JiraValidationError(["Max results cannot exceed 1000"])

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance


class TimeTrackingService:
    """Domain service for time tracking operations."""

    def __init__(
        self,
        time_tracking_port: TimeTrackingPort,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        time_format_validator: TimeFormatValidator,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        self._time_tracking_port = time_tracking_port
        self._repository = repository
        self._config_provider = config_provider
        self._time_format_validator = time_format_validator
        self._logger = logger
        self._event_publisher = event_publisher

    async def log_work(self, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Log work on an issue with validation."""
        self._validate_work_log_request(work_log_request)
        instance_name = self._resolve_instance_name(instance_name)

        # Validate issue exists
        await self._validate_issue_exists(work_log_request.issue_key, instance_name)

        # Validate time tracking is enabled
        await self._validate_time_tracking_enabled(work_log_request.issue_key, instance_name)

        # Validate time format
        await self._validate_time_format(work_log_request.time_spent)

        try:
            result = await self._time_tracking_port.log_work(work_log_request, instance_name)
            self._logger.info(f"Logged {work_log_request.time_spent} work on issue {work_log_request.issue_key}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to log work on issue {work_log_request.issue_key}: {str(e)}")
            raise WorkLogError(work_log_request.issue_key, str(e))

    async def get_work_logs(self, issue_key: str, instance_name: str | None = None) -> list[WorkLog]:
        """Get all work logs for an issue."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            work_logs = await self._time_tracking_port.get_work_logs(issue_key, instance_name)
            self._logger.debug(f"Retrieved {len(work_logs)} work logs for issue {issue_key}")
            return work_logs
        except Exception as e:
            self._logger.error(f"Failed to get work logs for issue {issue_key}: {str(e)}")
            raise

    async def update_work_log(self, work_log_id: str, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Update an existing work log."""
        if not work_log_id or not work_log_id.strip():
            raise JiraValidationError(["Work log ID cannot be empty"])

        self._validate_work_log_request(work_log_request)
        instance_name = self._resolve_instance_name(instance_name)

        # Validate time format
        await self._validate_time_format(work_log_request.time_spent)

        try:
            result = await self._time_tracking_port.update_work_log(work_log_id, work_log_request, instance_name)
            self._logger.info(f"Updated work log {work_log_id} for issue {work_log_request.issue_key}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to update work log {work_log_id}: {str(e)}")
            raise WorkLogError(work_log_request.issue_key, str(e))

    async def delete_work_log(self, issue_key: str, work_log_id: str, instance_name: str | None = None) -> bool:
        """Delete a work log entry."""
        self._validate_issue_key(issue_key)
        if not work_log_id or not work_log_id.strip():
            raise JiraValidationError(["Work log ID cannot be empty"])

        instance_name = self._resolve_instance_name(instance_name)

        try:
            result = await self._time_tracking_port.delete_work_log(issue_key, work_log_id, instance_name)
            if result:
                self._logger.info(f"Deleted work log {work_log_id} from issue {issue_key}")
            else:
                self._logger.warning(f"Work log {work_log_id} not found or could not be deleted")
            return result
        except Exception as e:
            self._logger.error(f"Failed to delete work log {work_log_id}: {str(e)}")
            raise WorkLogNotFoundError(work_log_id, issue_key)

    async def get_time_tracking_info(self, issue_key: str, instance_name: str | None = None) -> TimeTrackingInfo:
        """Get time tracking information for an issue."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            time_info = await self._time_tracking_port.get_time_tracking_info(issue_key, instance_name)
            self._logger.debug(f"Retrieved time tracking info for issue {issue_key}")
            return time_info
        except Exception as e:
            self._logger.error(f"Failed to get time tracking info for issue {issue_key}: {str(e)}")
            raise TimeTrackingError(issue_key, str(e))

    async def update_time_estimates(self, estimate_update: TimeEstimateUpdate, instance_name: str | None = None) -> TimeEstimateResult:
        """Update time estimates for an issue."""
        self._validate_estimate_update(estimate_update)
        instance_name = self._resolve_instance_name(instance_name)

        # Validate issue exists
        await self._validate_issue_exists(estimate_update.issue_key, instance_name)

        # Validate time tracking is enabled
        await self._validate_time_tracking_enabled(estimate_update.issue_key, instance_name)

        # Validate time formats
        if estimate_update.original_estimate:
            await self._validate_time_format(estimate_update.original_estimate)
        if estimate_update.remaining_estimate:
            await self._validate_time_format(estimate_update.remaining_estimate)

        try:
            result = await self._time_tracking_port.update_time_estimates(estimate_update, instance_name)
            self._logger.info(f"Updated time estimates for issue {estimate_update.issue_key}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to update time estimates for issue {estimate_update.issue_key}: {str(e)}")
            raise TimeEstimateError(estimate_update.issue_key, str(e))

    async def validate_time_format(self, time_string: str) -> list[str]:
        """Validate time format without performing any operations."""
        try:
            validation_errors = self._time_format_validator.validate_time_format(time_string)
            return validation_errors
        except Exception as e:
            self._logger.error(f"Failed to validate time format '{time_string}': {str(e)}")
            return [f"Could not validate time format: {str(e)}"]

    async def parse_time_to_seconds(self, time_string: str) -> int:
        """Parse time string to seconds."""
        # First validate the format
        validation_errors = await self.validate_time_format(time_string)
        if validation_errors:
            raise InvalidTimeFormatError(time_string, "Valid Jira time format (e.g., '2h 30m', '1d', '45m')")

        try:
            seconds = self._time_format_validator.parse_time_to_seconds(time_string)
            if seconds < 0:
                raise NegativeTimeError(time_string, "time parsing")
            return seconds
        except Exception as e:
            self._logger.error(f"Failed to parse time '{time_string}': {str(e)}")
            raise InvalidTimeFormatError(time_string, str(e))

    async def format_seconds_to_time(self, seconds: int) -> str:
        """Format seconds to Jira time format."""
        if seconds < 0:
            raise NegativeTimeError(str(seconds), "time formatting")

        try:
            time_string = self._time_format_validator.format_seconds_to_time(seconds)
            return time_string
        except Exception as e:
            self._logger.error(f"Failed to format seconds {seconds}: {str(e)}")
            raise

    def _validate_work_log_request(self, work_log_request: WorkLogRequest) -> None:
        """Validate work log request."""
        errors = []

        if not work_log_request.issue_key or not work_log_request.issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not work_log_request.time_spent or not work_log_request.time_spent.strip():
            errors.append("Time spent cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    def _validate_estimate_update(self, estimate_update: TimeEstimateUpdate) -> None:
        """Validate time estimate update."""
        errors = []

        if not estimate_update.issue_key or not estimate_update.issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not estimate_update.original_estimate and not estimate_update.remaining_estimate:
            errors.append("At least one estimate must be provided")

        if errors:
            raise JiraValidationError(errors)

    async def _validate_issue_exists(self, issue_key: str, instance_name: str) -> None:
        """Validate that the issue exists."""
        try:
            await self._repository.get_issue(issue_key, instance_name)
        except Exception:
            raise JiraIssueNotFound(issue_key, instance_name)

    async def _validate_time_tracking_enabled(self, issue_key: str, instance_name: str) -> None:
        """Validate that time tracking is enabled for the issue."""
        try:
            # Get issue to determine project and issue type
            issue = await self._repository.get_issue(issue_key, instance_name)
            project_key = issue.key.split('-')[0]  # Extract project key from issue key

            is_enabled = await self._time_tracking_port.is_time_tracking_enabled(
                project_key, issue.issue_type, instance_name
            )

            if not is_enabled:
                raise TimeTrackingNotEnabledError(project_key, issue.issue_type)
        except TimeTrackingNotEnabledError:
            raise
        except Exception as e:
            # If we can't check, log warning but continue
            self._logger.warning(f"Could not verify time tracking is enabled for issue {issue_key}: {str(e)}")

    async def _validate_time_format(self, time_string: str) -> None:
        """Validate time format and raise exception if invalid."""
        validation_errors = await self.validate_time_format(time_string)
        if validation_errors:
            raise InvalidTimeFormatError(time_string, "; ".join(validation_errors))

    def _validate_issue_key(self, issue_key: str) -> None:
        """Validate issue key format."""
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance


class WorkflowService:
    """Domain service for workflow-related operations."""

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        self._repository = repository
        self._config_provider = config_provider
        self._logger = logger
        self._event_publisher = event_publisher

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

    def _validate_issue_key(self, issue_key: str) -> None:
        """Validate issue key format."""
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

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

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance


class ProjectService:
    """Domain service for project-related operations."""

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger
    ):
        self._repository = repository
        self._config_provider = config_provider
        self._logger = logger

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

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance


class VisualizationService:
    """Domain service for workflow visualization."""

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        graph_generator: GraphGenerator,
        workflow_analyzer: WorkflowAnalyzer,
        logger: Logger
    ):
        self._repository = repository
        self._config_provider = config_provider
        self._graph_generator = graph_generator
        self._workflow_analyzer = workflow_analyzer
        self._logger = logger

    async def generate_workflow_graph(
        self,
        project_key: str,
        issue_type: str = "Story",
        format: str = "svg",
        instance_name: str | None = None
    ) -> dict[str, Any]:
        """Generate a workflow graph for a project and issue type."""
        self._validate_graph_request(project_key, issue_type, format)
        instance_name = self._resolve_instance_name(instance_name)

        if not self._graph_generator.is_available():
            raise JiraGraphLibraryNotAvailable(["graphviz", "networkx"])

        try:
            # Get workflow data
            workflow_data = await self._repository.get_workflow_data(project_key, issue_type, instance_name)

            # Analyze workflow and create graph
            workflow_graph = await self._workflow_analyzer.analyze_workflow(workflow_data, project_key, issue_type)

            # Generate output in requested format
            if format.lower() == "json":
                return {
                    "success": True,
                    "project": project_key,
                    "issue_type": issue_type,
                    "workflow": self._workflow_to_dict(workflow_graph),
                    "instance": instance_name,
                    "format": "json"
                }
            elif format.lower() == "dot":
                dot_content = await self._graph_generator.generate_dot_graph(workflow_graph)
                return {
                    "success": True,
                    "project": project_key,
                    "issue_type": issue_type,
                    "dot_content": dot_content,
                    "instance": instance_name,
                    "format": "dot"
                }
            else:
                # Generate visual graph (SVG or PNG)
                graph_data = await self._graph_generator.generate_visual_graph(workflow_graph, format)
                return {
                    "success": True,
                    "project": project_key,
                    "issue_type": issue_type,
                    "graph_data": graph_data,
                    "instance": instance_name,
                    "format": format,
                    "encoding": "base64"
                }

        except Exception as e:
            self._logger.error(f"Failed to generate workflow graph for {project_key}/{issue_type}: {str(e)}")
            raise JiraGraphGenerationError(str(e), project_key, issue_type)

    def _validate_graph_request(self, project_key: str, issue_type: str, format: str) -> None:
        """Validate graph generation request."""
        errors = []

        if not project_key or not project_key.strip():
            errors.append("Project key cannot be empty")

        if not issue_type or not issue_type.strip():
            errors.append("Issue type cannot be empty")

        valid_formats = ["svg", "png", "dot", "json"]
        if format.lower() not in valid_formats:
            errors.append(f"Format must be one of: {', '.join(valid_formats)}")

        if errors:
            raise JiraValidationError(errors)

    def _workflow_to_dict(self, workflow: WorkflowGraph) -> dict[str, Any]:
        """Convert workflow graph to dictionary."""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "category": node.category,
                    "color": node.color
                }
                for node in workflow.nodes
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "label": edge.label
                }
                for edge in workflow.edges
            ],
            "metadata": workflow.metadata
        }

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance


class InstanceService:
    """Domain service for instance management."""

    def __init__(self, config_provider: ConfigurationProvider, logger: Logger):
        self._config_provider = config_provider
        self._logger = logger

    def get_instances(self) -> list[JiraInstance]:
        """Get all configured Jira instances."""
        try:
            instances_dict = self._config_provider.get_instances()
            instances = list(instances_dict.values())
            self._logger.debug(f"Retrieved {len(instances)} configured instances")
            return instances
        except Exception as e:
            self._logger.error(f"Failed to get instances: {str(e)}")
            raise

    def get_default_instance(self) -> JiraInstance | None:
        """Get the default Jira instance."""
        try:
            default_instance = self._config_provider.get_instance()
            if default_instance:
                self._logger.debug(f"Retrieved default instance: {default_instance.name}")
            else:
                self._logger.warning("No default instance configured")
            return default_instance
        except Exception as e:
            self._logger.error(f"Failed to get default instance: {str(e)}")
            raise


class IssueLinkService:
    """Domain service for issue linking operations."""

    def __init__(
        self,
        link_port: IssueLinkPort,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        link_type_mapper: LinkTypeMapper,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        self._link_port = link_port
        self._repository = repository
        self._config_provider = config_provider
        self._link_type_mapper = link_type_mapper
        self._logger = logger
        self._event_publisher = event_publisher

    async def create_link(self, issue_link: IssueLink, instance_name: str | None = None) -> IssueLinkResult:
        """Create a link between two issues with validation."""
        self._validate_link_request(issue_link)
        instance_name = self._resolve_instance_name(instance_name)

        # Validate both issues exist
        await self._validate_issues_exist(issue_link.source_issue, issue_link.target_issue, instance_name)

        # Check for circular dependencies
        await self._check_circular_dependency(issue_link, instance_name)

        # Validate link type is supported
        await self._validate_link_type(issue_link.link_type, instance_name)

        try:
            result = await self._link_port.create_link(issue_link, instance_name)
            self._logger.info(f"Created {issue_link.link_type} link from {issue_link.source_issue} to {issue_link.target_issue}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to create link: {str(e)}")
            raise IssueLinkError(issue_link.source_issue, issue_link.target_issue, issue_link.link_type, str(e))

    async def create_epic_story_link(self, epic_key: str, story_key: str, instance_name: str | None = None) -> IssueLinkResult:
        """Create a specific Epic-Story link."""
        epic_link = IssueLink(
            link_type=LinkType.EPIC_STORY.value,
            source_issue=epic_key,
            target_issue=story_key,
            direction=LinkDirection.OUTWARD.value
        )

        try:
            result = await self.create_link(epic_link, instance_name)
            self._logger.info(f"Created Epic-Story link: {epic_key} -> {story_key}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to create Epic-Story link: {str(e)}")
            raise EpicLinkError(epic_key, story_key, str(e))

    async def create_parent_child_link(self, parent_key: str, child_key: str, instance_name: str | None = None) -> IssueLinkResult:
        """Create a specific Parent-Child link."""
        parent_link = IssueLink(
            link_type=LinkType.PARENT_CHILD.value,
            source_issue=parent_key,
            target_issue=child_key,
            direction=LinkDirection.OUTWARD.value
        )

        return await self.create_link(parent_link, instance_name)

    async def get_issue_links(self, issue_key: str, instance_name: str | None = None) -> list[IssueLink]:
        """Get all links for a specific issue."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            links = await self._link_port.get_links(issue_key, instance_name)
            self._logger.debug(f"Retrieved {len(links)} links for issue {issue_key}")
            return links
        except Exception as e:
            self._logger.error(f"Failed to get links for issue {issue_key}: {str(e)}")
            raise

    async def remove_link(self, link_id: str, instance_name: str | None = None) -> bool:
        """Remove a link between issues."""
        if not link_id or not link_id.strip():
            raise JiraValidationError(["Link ID cannot be empty"])

        instance_name = self._resolve_instance_name(instance_name)

        try:
            result = await self._link_port.remove_link(link_id, instance_name)
            if result:
                self._logger.info(f"Removed link {link_id}")
            else:
                self._logger.warning(f"Link {link_id} not found or could not be removed")
            return result
        except Exception as e:
            self._logger.error(f"Failed to remove link {link_id}: {str(e)}")
            raise LinkNotFoundError(link_id=link_id)

    def _validate_link_request(self, issue_link: IssueLink) -> None:
        """Validate link creation request."""
        errors = []

        if not issue_link.source_issue or not issue_link.source_issue.strip():
            errors.append("Source issue cannot be empty")

        if not issue_link.target_issue or not issue_link.target_issue.strip():
            errors.append("Target issue cannot be empty")

        if not issue_link.link_type or not issue_link.link_type.strip():
            errors.append("Link type cannot be empty")

        if issue_link.source_issue == issue_link.target_issue:
            errors.append("Cannot link an issue to itself")

        if errors:
            raise JiraValidationError(errors)

    async def _validate_issues_exist(self, source_issue: str, target_issue: str, instance_name: str) -> None:
        """Validate that both issues exist."""
        try:
            await self._repository.get_issue(source_issue, instance_name)
        except Exception:
            raise JiraIssueNotFound(source_issue, instance_name)

        try:
            await self._repository.get_issue(target_issue, instance_name)
        except Exception:
            raise JiraIssueNotFound(target_issue, instance_name)

    async def _check_circular_dependency(self, issue_link: IssueLink, instance_name: str) -> None:
        """Check for circular link dependencies."""
        # Get existing links for target issue
        try:
            target_links = await self._link_port.get_links(issue_link.target_issue, instance_name)

            # Check if target issue already links back to source issue
            for link in target_links:
                if (link.target_issue == issue_link.source_issue and
                    link.link_type == issue_link.link_type):
                    raise CircularLinkError(
                        issue_link.source_issue,
                        issue_link.target_issue,
                        issue_link.link_type
                    )
        except CircularLinkError:
            raise
        except Exception:
            # If we can't check for circular dependencies, log warning but continue
            self._logger.warning(f"Could not check for circular dependencies between {issue_link.source_issue} and {issue_link.target_issue}")

    async def _validate_link_type(self, link_type: str, instance_name: str) -> None:
        """Validate that the link type is supported."""
        try:
            available_types = await self._link_port.get_available_link_types(instance_name)
            if link_type not in available_types:
                raise LinkTypeNotSupportedError(link_type, instance_name, available_types)
        except LinkTypeNotSupportedError:
            raise
        except Exception:
            # If we can't validate link types, log warning but continue
            self._logger.warning(f"Could not validate link type {link_type} for instance {instance_name}")

    def _validate_issue_key(self, issue_key: str) -> None:
        """Validate issue key format."""
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance


class IssueUpdateService:
    """Domain service for issue update operations."""

    def __init__(
        self,
        update_port: IssueUpdatePort,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        self._update_port = update_port
        self._repository = repository
        self._config_provider = config_provider
        self._logger = logger
        self._event_publisher = event_publisher

    async def update_issue(self, update_request: IssueUpdate, instance_name: str | None = None) -> IssueUpdateResult:
        """Update an existing issue with validation."""
        self._validate_update_request(update_request)
        instance_name = self._resolve_instance_name(instance_name)

        # Validate issue exists
        await self._validate_issue_exists(update_request.issue_key, instance_name)

        # Validate fields can be updated
        await self._validate_updatable_fields(update_request, instance_name)

        try:
            result = await self._update_port.update_issue(update_request, instance_name)
            self._logger.info(f"Updated issue {update_request.issue_key} with fields: {', '.join(update_request.get_updated_fields())}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to update issue {update_request.issue_key}: {str(e)}")
            raise IssueUpdateError(update_request.issue_key, str(e), update_request.get_updated_fields())

    async def validate_update_permissions(self, issue_key: str, fields: dict[str, Any], instance_name: str | None = None) -> list[str]:
        """Validate that the user can update the specified fields."""
        instance_name = self._resolve_instance_name(instance_name)

        try:
            validation_errors = await self._update_port.validate_update_fields(issue_key, fields, instance_name)
            return validation_errors
        except Exception as e:
            self._logger.error(f"Failed to validate update permissions for issue {issue_key}: {str(e)}")
            return [f"Could not validate update permissions: {str(e)}"]

    async def get_updatable_fields(self, issue_key: str, instance_name: str | None = None) -> list[str]:
        """Get list of fields that can be updated for the given issue."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            fields = await self._update_port.get_updatable_fields(issue_key, instance_name)
            self._logger.debug(f"Retrieved {len(fields)} updatable fields for issue {issue_key}")
            return fields
        except Exception as e:
            self._logger.error(f"Failed to get updatable fields for issue {issue_key}: {str(e)}")
            raise

    def _validate_update_request(self, update_request: IssueUpdate) -> None:
        """Validate issue update request."""
        errors = []

        if not update_request.issue_key or not update_request.issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not update_request.fields:
            errors.append("At least one field must be provided for update")

        if errors:
            raise JiraValidationError(errors)

    async def _validate_issue_exists(self, issue_key: str, instance_name: str) -> None:
        """Validate that the issue exists."""
        try:
            await self._repository.get_issue(issue_key, instance_name)
        except Exception:
            raise JiraIssueNotFound(issue_key, instance_name)

    async def _validate_updatable_fields(self, update_request: IssueUpdate, instance_name: str) -> None:
        """Validate that all fields in the update request can be updated."""
        validation_errors = await self._update_port.validate_update_fields(
            update_request.issue_key,
            update_request.fields,
            instance_name
        )

        if validation_errors:
            raise JiraValidationError(validation_errors)

    def _validate_issue_key(self, issue_key: str) -> None:
        """Validate issue key format."""
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance


class SearchService:
    """Domain service for JQL search operations."""

    def __init__(
        self,
        search_port: IssueSearchPort,
        config_provider: ConfigurationProvider,
        jql_validator: JQLValidator,
        logger: Logger
    ):
        self._search_port = search_port
        self._config_provider = config_provider
        self._jql_validator = jql_validator
        self._logger = logger

    async def search_issues(self, query: SearchQuery, instance_name: str | None = None) -> SearchResult:
        """Execute a JQL search with validation."""
        self._validate_search_query(query)
        instance_name = self._resolve_instance_name(instance_name)

        # Validate JQL syntax and security
        await self._validate_jql_query(query.jql, instance_name)

        try:
            result = await self._search_port.search_issues(query, instance_name)
            self._logger.info(f"JQL search returned {len(result.issues)} issues (total: {result.total_results})")
            return result
        except Exception as e:
            self._logger.error(f"Failed to execute JQL search: {str(e)}")
            raise InvalidJQLError(query.jql, str(e))

    async def search_with_filters(self, filters: SearchFilters, instance_name: str | None = None) -> SearchResult:
        """
        Execute a search using simple filters by converting them to JQL.

        This method provides a clean interface for simple project-based searches
        while internally using the robust JQL search infrastructure.
        """
        self._validate_search_filters(filters)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            # Convert filters to JQL using the builder
            jql_builder = JQLBuilderFactory.from_search_filters(filters)
            jql = jql_builder.build()

            # Additional security validation on generated JQL
            security_errors = validate_jql_safety(jql)
            if security_errors:
                raise JQLSecurityError(jql, "; ".join(security_errors))

            # Create SearchQuery from filters and generated JQL
            search_query = SearchQuery(
                jql=jql,
                max_results=filters.max_results,
                start_at=filters.start_at,
                fields=None  # Use default fields for filter-based searches
            )

            # Delegate to the main search method
            result = await self.search_issues(search_query, instance_name)

            self._logger.info(
                f"Filter search for project {filters.project_key} returned {len(result.issues)} issues "
                f"(JQL: {jql})"
            )

            return result

        except Exception as e:
            self._logger.error(
                f"Failed to execute filter search for project {filters.project_key}: {str(e)}"
            )
            # Re-raise with context about the filter conversion
            if isinstance(e, InvalidJQLError | JQLSecurityError):
                raise
            else:
                raise InvalidJQLError(
                    f"Generated from filters: {filters.get_active_filters()}",
                    str(e)
                )

    async def validate_jql_syntax(self, jql: str, instance_name: str | None = None) -> list[str]:
        """Validate JQL syntax without executing the query."""
        instance_name = self._resolve_instance_name(instance_name)

        # First check with local validator
        syntax_errors = self._jql_validator.validate_syntax(jql)
        if syntax_errors:
            return syntax_errors

        # Then check with Jira instance
        try:
            validation_errors = await self._search_port.validate_jql(jql, instance_name)
            return validation_errors
        except Exception as e:
            self._logger.error(f"Failed to validate JQL syntax: {str(e)}")
            return [f"Could not validate JQL: {str(e)}"]

    async def get_search_suggestions(self, partial_jql: str, instance_name: str | None = None) -> list[str]:
        """Get JQL completion suggestions."""
        instance_name = self._resolve_instance_name(instance_name)

        try:
            suggestions = await self._search_port.get_search_suggestions(partial_jql, instance_name)
            self._logger.debug(f"Retrieved {len(suggestions)} JQL suggestions")
            return suggestions
        except Exception as e:
            self._logger.error(f"Failed to get JQL suggestions: {str(e)}")
            return []

    def _validate_search_query(self, query: SearchQuery) -> None:
        """Validate search query parameters."""
        errors = []

        if not query.jql or not query.jql.strip():
            errors.append("JQL query cannot be empty")

        # Validate limits
        limit_errors = self._jql_validator.validate_limits(query.max_results, query.start_at)
        errors.extend(limit_errors)

        if errors:
            raise JiraValidationError(errors)

    def _validate_search_filters(self, filters: SearchFilters) -> None:
        """Validate search filters parameters."""
        errors = []

        if not filters.project_key or not filters.project_key.strip():
            errors.append("Project key cannot be empty")

        # Validate limits (reuse existing validator logic)
        limit_errors = self._jql_validator.validate_limits(filters.max_results, filters.start_at)
        errors.extend(limit_errors)

        if errors:
            raise JiraValidationError(errors)

    async def _validate_jql_query(self, jql: str, instance_name: str) -> None:
        """Validate JQL query for syntax and security."""
        # Check syntax
        syntax_errors = self._jql_validator.validate_syntax(jql)
        if syntax_errors:
            raise InvalidJQLError(jql, "; ".join(syntax_errors))

        # Check security
        security_errors = self._jql_validator.check_security(jql)
        if security_errors:
            raise JQLSecurityError(jql, "; ".join(security_errors))

        # Validate with Jira instance
        validation_errors = await self._search_port.validate_jql(jql, instance_name)
        if validation_errors:
            raise InvalidJQLError(jql, "; ".join(validation_errors))

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance
