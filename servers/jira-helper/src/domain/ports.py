"""
Domain ports (interfaces) for the Jira Helper.

This module defines the interfaces that external adapters must implement.
These are the contracts between the domain layer and the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import (
    JiraInstance, JiraProject, JiraIssue, JiraComment, WorkflowTransition,
    WorkflowGraph, CustomFieldMapping, IssueCreateRequest, IssueTransitionRequest,
    AssigneeChangeRequest, CommentAddRequest
)


class JiraRepository(ABC):
    """Interface for Jira data operations."""

    @abstractmethod
    async def get_projects(self, instance_name: Optional[str] = None) -> List[JiraProject]:
        """Get all projects from a Jira instance."""
        pass

    @abstractmethod
    async def get_issue(self, issue_key: str, instance_name: Optional[str] = None) -> JiraIssue:
        """Get a specific issue by key."""
        pass

    @abstractmethod
    async def get_issue_with_comments(self, issue_key: str, instance_name: Optional[str] = None) -> JiraIssue:
        """Get a specific issue with all its comments."""
        pass

    @abstractmethod
    async def create_issue(self, request: IssueCreateRequest, instance_name: Optional[str] = None) -> JiraIssue:
        """Create a new issue."""
        pass

    @abstractmethod
    async def add_comment(self, request: CommentAddRequest, instance_name: Optional[str] = None) -> JiraComment:
        """Add a comment to an issue."""
        pass

    @abstractmethod
    async def get_available_transitions(self, issue_key: str, instance_name: Optional[str] = None) -> List[WorkflowTransition]:
        """Get available transitions for an issue."""
        pass

    @abstractmethod
    async def transition_issue(self, request: IssueTransitionRequest, instance_name: Optional[str] = None) -> JiraIssue:
        """Transition an issue through workflow."""
        pass

    @abstractmethod
    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: Optional[str] = None) -> JiraIssue:
        """Change the assignee of an issue."""
        pass

    @abstractmethod
    async def search_issues(
        self, 
        project_key: str, 
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50,
        instance_name: Optional[str] = None
    ) -> List[JiraIssue]:
        """Search for issues in a project with filters."""
        pass

    @abstractmethod
    async def get_custom_field_mappings(self, reverse: bool = False, instance_name: Optional[str] = None) -> List[CustomFieldMapping]:
        """Get custom field mappings."""
        pass

    @abstractmethod
    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow data for a project and issue type."""
        pass


class ConfigurationProvider(ABC):
    """Interface for configuration access."""

    @abstractmethod
    def get_instances(self) -> Dict[str, JiraInstance]:
        """Get all configured Jira instances."""
        pass

    @abstractmethod
    def get_default_instance_name(self) -> Optional[str]:
        """Get the name of the default instance."""
        pass

    @abstractmethod
    def get_instance(self, instance_name: Optional[str] = None) -> Optional[JiraInstance]:
        """Get a specific instance by name or the default instance."""
        pass


class GraphGenerator(ABC):
    """Interface for graph generation."""

    @abstractmethod
    async def generate_dot_graph(self, workflow: WorkflowGraph) -> str:
        """Generate a DOT format graph."""
        pass

    @abstractmethod
    async def generate_visual_graph(self, workflow: WorkflowGraph, format: str = "svg") -> str:
        """Generate a visual graph in SVG or PNG format (base64 encoded)."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if graph generation is available."""
        pass


class WorkflowAnalyzer(ABC):
    """Interface for workflow analysis."""

    @abstractmethod
    async def analyze_workflow(self, workflow_data: Dict[str, Any], project_key: str, issue_type: str) -> WorkflowGraph:
        """Analyze workflow data and create a workflow graph."""
        pass

    @abstractmethod
    async def create_fallback_workflow(self, transitions: List[WorkflowTransition], current_status: str) -> WorkflowGraph:
        """Create a fallback workflow from available transitions."""
        pass


class JiraClientFactory(ABC):
    """Interface for creating Jira clients."""

    @abstractmethod
    def create_client(self, instance_name: Optional[str] = None):
        """Create a Jira client for the specified instance."""
        pass

    @abstractmethod
    def validate_instance(self, instance_name: str) -> bool:
        """Validate that an instance exists and is properly configured."""
        pass


class Logger(ABC):
    """Interface for logging."""

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        pass

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        pass


class CacheProvider(ABC):
    """Interface for caching operations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass


class EventPublisher(ABC):
    """Interface for publishing domain events."""

    @abstractmethod
    async def publish_issue_created(self, issue: JiraIssue, instance_name: str) -> None:
        """Publish an issue created event."""
        pass

    @abstractmethod
    async def publish_issue_transitioned(self, issue: JiraIssue, old_status: str, new_status: str, instance_name: str) -> None:
        """Publish an issue transitioned event."""
        pass

    @abstractmethod
    async def publish_assignee_changed(self, issue: JiraIssue, old_assignee: Optional[str], new_assignee: Optional[str], instance_name: str) -> None:
        """Publish an assignee changed event."""
        pass

    @abstractmethod
    async def publish_comment_added(self, issue_key: str, comment: JiraComment, instance_name: str) -> None:
        """Publish a comment added event."""
        pass
