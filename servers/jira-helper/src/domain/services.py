"""
Domain services for the Jira Helper.

This module contains domain services that implement core business logic.
These services orchestrate domain entities and enforce business rules.
"""

from typing import List, Optional, Dict, Any
from .models import (
    JiraInstance, JiraProject, JiraIssue, JiraComment, WorkflowTransition,
    WorkflowGraph, WorkflowNode, WorkflowEdge, CustomFieldMapping,
    IssueCreateRequest, IssueTransitionRequest, AssigneeChangeRequest,
    CommentAddRequest, StatusCategory
)
from .ports import (
    JiraRepository, ConfigurationProvider, GraphGenerator, WorkflowAnalyzer,
    Logger, EventPublisher
)
from .exceptions import (
    JiraInstanceNotFound, JiraIssueNotFound, JiraTransitionNotAvailable,
    JiraWorkflowError, JiraValidationError, JiraGraphGenerationError,
    JiraGraphLibraryNotAvailable
)


class IssueService:
    """Domain service for issue-related operations."""

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger,
        event_publisher: Optional[EventPublisher] = None
    ):
        self._repository = repository
        self._config_provider = config_provider
        self._logger = logger
        self._event_publisher = event_publisher

    async def get_issue(self, issue_key: str, instance_name: Optional[str] = None) -> JiraIssue:
        """Get a single issue by key."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)
        
        try:
            issue = await self._repository.get_issue(issue_key, instance_name)
            self._logger.debug(f"Retrieved issue {issue_key} from instance {instance_name}")
            return issue
        except Exception as e:
            self._logger.error(f"Failed to get issue {issue_key}: {str(e)}")
            raise JiraIssueNotFound(issue_key, instance_name)

    async def get_issue_with_comments(self, issue_key: str, instance_name: Optional[str] = None) -> JiraIssue:
        """Get a single issue with all its comments."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)
        
        try:
            issue = await self._repository.get_issue_with_comments(issue_key, instance_name)
            self._logger.debug(f"Retrieved issue {issue_key} with {len(issue.comments)} comments from instance {instance_name}")
            return issue
        except Exception as e:
            self._logger.error(f"Failed to get issue with comments {issue_key}: {str(e)}")
            raise JiraIssueNotFound(issue_key, instance_name)

    async def create_issue(self, request: IssueCreateRequest, instance_name: Optional[str] = None) -> JiraIssue:
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

    async def add_comment(self, request: CommentAddRequest, instance_name: Optional[str] = None) -> JiraComment:
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

    async def search_issues(
        self,
        project_key: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50,
        instance_name: Optional[str] = None
    ) -> List[JiraIssue]:
        """Search for issues in a project."""
        self._validate_project_key(project_key)
        self._validate_max_results(max_results)
        instance_name = self._resolve_instance_name(instance_name)
        
        try:
            issues = await self._repository.search_issues(
                project_key, status, issue_type, max_results, instance_name
            )
            self._logger.debug(f"Found {len(issues)} issues in project {project_key}")
            return issues
        except Exception as e:
            self._logger.error(f"Failed to search issues in project {project_key}: {str(e)}")
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

    def _resolve_instance_name(self, instance_name: Optional[str]) -> str:
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
        event_publisher: Optional[EventPublisher] = None
    ):
        self._repository = repository
        self._config_provider = config_provider
        self._logger = logger
        self._event_publisher = event_publisher

    async def get_available_transitions(self, issue_key: str, instance_name: Optional[str] = None) -> List[WorkflowTransition]:
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

    async def transition_issue(self, request: IssueTransitionRequest, instance_name: Optional[str] = None) -> JiraIssue:
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

    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: Optional[str] = None) -> JiraIssue:
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

    def _resolve_instance_name(self, instance_name: Optional[str]) -> str:
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

    async def get_projects(self, instance_name: Optional[str] = None) -> List[JiraProject]:
        """Get all projects from a Jira instance."""
        instance_name = self._resolve_instance_name(instance_name)
        
        try:
            projects = await self._repository.get_projects(instance_name)
            self._logger.debug(f"Retrieved {len(projects)} projects from instance {instance_name}")
            return projects
        except Exception as e:
            self._logger.error(f"Failed to get projects from instance {instance_name}: {str(e)}")
            raise

    async def get_custom_field_mappings(self, reverse: bool = False, instance_name: Optional[str] = None) -> List[CustomFieldMapping]:
        """Get custom field mappings."""
        instance_name = self._resolve_instance_name(instance_name)
        
        try:
            mappings = await self._repository.get_custom_field_mappings(reverse, instance_name)
            self._logger.debug(f"Retrieved {len(mappings)} custom field mappings from instance {instance_name}")
            return mappings
        except Exception as e:
            self._logger.error(f"Failed to get custom field mappings from instance {instance_name}: {str(e)}")
            raise

    def _resolve_instance_name(self, instance_name: Optional[str]) -> str:
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
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
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

    def _workflow_to_dict(self, workflow: WorkflowGraph) -> Dict[str, Any]:
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

    def _resolve_instance_name(self, instance_name: Optional[str]) -> str:
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

    def get_instances(self) -> List[JiraInstance]:
        """Get all configured Jira instances."""
        try:
            instances_dict = self._config_provider.get_instances()
            instances = list(instances_dict.values())
            self._logger.debug(f"Retrieved {len(instances)} configured instances")
            return instances
        except Exception as e:
            self._logger.error(f"Failed to get instances: {str(e)}")
            raise

    def get_default_instance(self) -> Optional[JiraInstance]:
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
