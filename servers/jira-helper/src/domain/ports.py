"""
Domain ports (interfaces) for the Jira Helper.

This module defines the interfaces that external adapters must implement.
These are the contracts between the domain layer and the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import Any

from domain.models import (
    AssigneeChangeRequest,
    CommentAddRequest,
    CustomFieldMapping,
    IssueCreateRequest,
    IssueCreateWithLinksRequest,
    IssueLink,
    IssueLinkResult,
    IssueTransitionRequest,
    IssueUpdate,
    IssueUpdateResult,
    JiraComment,
    JiraInstance,
    JiraIssue,
    JiraProject,
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
from domain.file_models import (
    AttachmentDeleteRequest,
    AttachmentDeleteResult,
    AttachmentListRequest,
    AttachmentListResult,
    FileContent,
    FileUploadPolicy,
    FileUploadRequest,
    FileUploadResult,
    JiraAttachment,
)


class JiraRepository(ABC):
    """Interface for Jira data operations."""

    @abstractmethod
    async def get_projects(self, instance_name: str) -> list[JiraProject]:
        """Get all projects from a Jira instance."""
        pass

    @abstractmethod
    async def get_issue(self, issue_key: str, instance_name: str) -> JiraIssue:
        """Get a specific issue by key."""
        pass

    @abstractmethod
    async def get_issue_with_comments(self, issue_key: str, instance_name: str) -> JiraIssue:
        """Get a specific issue with all its comments."""
        pass

    @abstractmethod
    async def create_issue(self, request: IssueCreateRequest, instance_name: str) -> JiraIssue:
        """Create a new issue."""
        pass

    @abstractmethod
    async def add_comment(self, request: CommentAddRequest, instance_name: str) -> JiraComment:
        """Add a comment to an issue."""
        pass

    @abstractmethod
    async def get_available_transitions(self, issue_key: str, instance_name: str) -> list[WorkflowTransition]:
        """Get available transitions for an issue."""
        pass

    @abstractmethod
    async def transition_issue(self, request: IssueTransitionRequest, instance_name: str) -> JiraIssue:
        """Transition an issue through workflow."""
        pass

    @abstractmethod
    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: str) -> JiraIssue:
        """Change the assignee of an issue."""
        pass

    @abstractmethod
    async def search_issues(
        self,
        project_key: str,
        status: str | None,
        issue_type: str | None,
        max_results: int,
        instance_name: str
    ) -> list[JiraIssue]:
        """Search for issues in a project with filters."""
        pass

    @abstractmethod
    async def get_custom_field_mappings(self, reverse: bool, instance_name: str) -> list[CustomFieldMapping]:
        """Get custom field mappings."""
        pass

    @abstractmethod
    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: str) -> dict[str, Any]:
        """Get workflow data for a project and issue type."""
        pass


class ConfigurationProvider(ABC):
    """Interface for configuration access."""

    @abstractmethod
    def get_instances(self) -> dict[str, JiraInstance]:
        """Get all configured Jira instances."""
        pass

    @abstractmethod
    def get_default_instance_name(self) -> str | None:
        """Get the name of the default instance."""
        pass

    @abstractmethod
    def get_instance(self, instance_name: str | None = None) -> JiraInstance | None:
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
    async def analyze_workflow(self, workflow_data: dict[str, Any], project_key: str, issue_type: str) -> WorkflowGraph:
        """Analyze workflow data and create a workflow graph."""
        pass

    @abstractmethod
    async def create_fallback_workflow(self, transitions: list[WorkflowTransition], current_status: str) -> WorkflowGraph:
        """Create a fallback workflow from available transitions."""
        pass


class JiraClientFactory(ABC):
    """Interface for creating Jira clients."""

    @abstractmethod
    def create_client(self, instance_name: str | None = None):
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
    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
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
    async def publish_assignee_changed(self, issue: JiraIssue, old_assignee: str | None, new_assignee: str | None, instance_name: str) -> None:
        """Publish an assignee changed event."""
        pass

    @abstractmethod
    async def publish_comment_added(self, issue_key: str, comment: JiraComment, instance_name: str) -> None:
        """Publish a comment added event."""
        pass


class IssueUpdatePort(ABC):
    """Interface for issue update operations."""

    @abstractmethod
    async def update_issue(self, update_request: IssueUpdate, instance_name: str | None = None) -> IssueUpdateResult:
        """Update an existing issue with new field values."""
        pass

    @abstractmethod
    async def validate_update_fields(self, issue_key: str, fields: dict[str, Any], instance_name: str | None = None) -> list[str]:
        """Validate that the specified fields can be updated. Returns list of validation errors."""
        pass

    @abstractmethod
    async def get_updatable_fields(self, issue_key: str, instance_name: str | None = None) -> list[str]:
        """Get list of fields that can be updated for the given issue."""
        pass


class IssueLinkPort(ABC):
    """Interface for issue linking operations."""

    @abstractmethod
    async def create_link(self, issue_link: IssueLink, instance_name: str | None = None) -> IssueLinkResult:
        """Create a link between two issues."""
        pass

    @abstractmethod
    async def get_links(self, issue_key: str, instance_name: str | None = None) -> list[IssueLink]:
        """Get all links for a specific issue."""
        pass

    @abstractmethod
    async def remove_link(self, link_id: str, instance_name: str | None = None) -> bool:
        """Remove a link between issues."""
        pass

    @abstractmethod
    async def get_available_link_types(self, instance_name: str | None = None) -> list[str]:
        """Get available link types for the Jira instance."""
        pass

    @abstractmethod
    async def validate_link(self, issue_link: IssueLink, instance_name: str | None = None) -> list[str]:
        """Validate a link before creation. Returns list of validation errors."""
        pass


class IssueSearchPort(ABC):
    """Interface for issue search operations."""

    @abstractmethod
    async def search_issues(self, query: SearchQuery, instance_name: str | None = None) -> SearchResult:
        """Execute a JQL search query."""
        pass

    @abstractmethod
    async def validate_jql(self, jql: str, instance_name: str | None = None) -> list[str]:
        """Validate JQL syntax. Returns list of validation errors."""
        pass

    @abstractmethod
    async def get_search_suggestions(self, partial_jql: str, instance_name: str | None = None) -> list[str]:
        """Get JQL completion suggestions for partial queries."""
        pass


class IssueCreationPort(ABC):
    """Interface for enhanced issue creation with links."""

    @abstractmethod
    async def create_issue_with_links(self, request: IssueCreateWithLinksRequest, instance_name: str | None = None) -> JiraIssue:
        """Create a new issue with associated links."""
        pass

    @abstractmethod
    async def create_epic_story_link(self, epic_key: str, story_key: str, instance_name: str | None = None) -> IssueLinkResult:
        """Create a specific Epic-Story link."""
        pass

    @abstractmethod
    async def create_parent_child_link(self, parent_key: str, child_key: str, instance_name: str | None = None) -> IssueLinkResult:
        """Create a specific Parent-Child link."""
        pass


class LinkTypeMapper(ABC):
    """Interface for mapping domain link types to Jira link types."""

    @abstractmethod
    def map_to_jira_link_type(self, domain_link_type: str, instance_name: str | None = None) -> str:
        """Map a domain link type to the corresponding Jira link type."""
        pass

    @abstractmethod
    def map_from_jira_link_type(self, jira_link_type: str, instance_name: str | None = None) -> str:
        """Map a Jira link type to the corresponding domain link type."""
        pass

    @abstractmethod
    def get_supported_link_types(self, instance_name: str | None = None) -> dict[str, str]:
        """Get mapping of supported link types (domain -> jira)."""
        pass


class JQLValidator(ABC):
    """Interface for JQL validation and security."""

    @abstractmethod
    def validate_syntax(self, jql: str) -> list[str]:
        """Validate JQL syntax. Returns list of syntax errors."""
        pass

    @abstractmethod
    def check_security(self, jql: str) -> list[str]:
        """Check JQL for security issues. Returns list of security concerns."""
        pass

    @abstractmethod
    def sanitize_jql(self, jql: str) -> str:
        """Sanitize JQL query to remove potentially harmful content."""
        pass

    @abstractmethod
    def validate_limits(self, max_results: int, start_at: int) -> list[str]:
        """Validate search limits. Returns list of limit violations."""
        pass


class TimeTrackingPort(ABC):
    """Interface for time tracking operations."""

    @abstractmethod
    async def log_work(self, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Log work on an issue."""
        pass

    @abstractmethod
    async def get_work_logs(self, issue_key: str, instance_name: str | None = None) -> list[WorkLog]:
        """Get all work logs for an issue."""
        pass

    @abstractmethod
    async def update_work_log(self, work_log_id: str, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Update an existing work log."""
        pass

    @abstractmethod
    async def delete_work_log(self, issue_key: str, work_log_id: str, instance_name: str | None = None) -> bool:
        """Delete a work log entry."""
        pass

    @abstractmethod
    async def get_time_tracking_info(self, issue_key: str, instance_name: str | None = None) -> TimeTrackingInfo:
        """Get time tracking information for an issue."""
        pass

    @abstractmethod
    async def update_time_estimates(self, estimate_update: TimeEstimateUpdate, instance_name: str | None = None) -> TimeEstimateResult:
        """Update time estimates for an issue."""
        pass

    @abstractmethod
    async def validate_time_format(self, time_string: str) -> list[str]:
        """Validate time format (e.g., '2h 30m', '1d'). Returns list of validation errors."""
        pass

    @abstractmethod
    async def is_time_tracking_enabled(self, project_key: str, issue_type: str = None, instance_name: str | None = None) -> bool:
        """Check if time tracking is enabled for a project/issue type."""
        pass


class TimeFormatValidator(ABC):
    """Interface for time format validation and conversion."""

    @abstractmethod
    def validate_time_format(self, time_string: str) -> list[str]:
        """Validate time format. Returns list of validation errors."""
        pass

    @abstractmethod
    def parse_time_to_seconds(self, time_string: str) -> int:
        """Parse time string to seconds."""
        pass

    @abstractmethod
    def format_seconds_to_time(self, seconds: int) -> str:
        """Format seconds to Jira time format."""
        pass

    @abstractmethod
    def get_supported_time_units(self) -> list[str]:
        """Get list of supported time units."""
        pass

    @abstractmethod
    def normalize_time_format(self, time_string: str) -> str:
        """Normalize time format to standard Jira format."""
        pass


class FileAttachmentPort(ABC):
    """Interface for file attachment operations."""

    @abstractmethod
    async def upload_file(self, request: FileUploadRequest, instance_name: str | None = None) -> FileUploadResult:
        """Upload a file to a Jira issue."""
        pass

    @abstractmethod
    async def upload_file_content(self, issue_key: str, file_content: FileContent, comment: str | None = None, instance_name: str | None = None) -> FileUploadResult:
        """Upload file content directly to a Jira issue."""
        pass

    @abstractmethod
    async def list_attachments(self, request: AttachmentListRequest, instance_name: str | None = None) -> AttachmentListResult:
        """List all attachments for an issue."""
        pass

    @abstractmethod
    async def delete_attachment(self, request: AttachmentDeleteRequest, instance_name: str | None = None) -> AttachmentDeleteResult:
        """Delete an attachment from an issue."""
        pass

    @abstractmethod
    async def get_attachment(self, attachment_id: str, instance_name: str | None = None) -> JiraAttachment | None:
        """Get attachment details by ID."""
        pass

    @abstractmethod
    async def download_attachment(self, attachment_id: str, instance_name: str | None = None) -> bytes | None:
        """Download attachment content by ID."""
        pass


class FileValidationPort(ABC):
    """Interface for file validation operations."""

    @abstractmethod
    def validate_file_path(self, file_path: str) -> list[str]:
        """Validate that a file path is valid and accessible. Returns list of validation errors."""
        pass

    @abstractmethod
    def validate_file_content(self, file_content: FileContent, policy: FileUploadPolicy) -> list[str]:
        """Validate file content against upload policy. Returns list of validation errors."""
        pass

    @abstractmethod
    def detect_mime_type(self, file_path: str) -> str:
        """Detect MIME type of a file."""
        pass

    @abstractmethod
    def detect_mime_type_from_content(self, content: bytes, filename: str) -> str:
        """Detect MIME type from file content and filename."""
        pass

    @abstractmethod
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        pass

    @abstractmethod
    def is_file_readable(self, file_path: str) -> bool:
        """Check if a file is readable."""
        pass


class FileSystemPort(ABC):
    """Interface for file system operations."""

    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        """Read file content from the file system."""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get file information (size, modified time, etc.)."""
        pass

    @abstractmethod
    def resolve_path(self, file_path: str) -> str:
        """Resolve a file path to an absolute path."""
        pass


class FileUploadPolicyProvider(ABC):
    """Interface for file upload policy management."""

    @abstractmethod
    def get_default_policy(self) -> FileUploadPolicy:
        """Get the default file upload policy."""
        pass

    @abstractmethod
    def get_policy_for_instance(self, instance_name: str) -> FileUploadPolicy:
        """Get file upload policy for a specific Jira instance."""
        pass

    @abstractmethod
    def get_policy_for_project(self, project_key: str, instance_name: str | None = None) -> FileUploadPolicy:
        """Get file upload policy for a specific project."""
        pass

    @abstractmethod
    def validate_against_policy(self, filename: str, mime_type: str, size_bytes: int, policy: FileUploadPolicy) -> tuple[bool, str | None]:
        """Validate a file against a policy. Returns (allowed, reason)."""
        pass
