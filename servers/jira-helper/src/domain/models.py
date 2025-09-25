"""
Domain models for the Jira Helper.

This module contains the core domain entities that represent Jira concepts.
These models are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from domain.base import validate_required_fields
from domain.enums import LinkDirection


@validate_required_fields('name', 'url', 'user', 'token')
@dataclass
class JiraInstance:
    """Represents a Jira instance configuration."""
    name: str
    url: str
    user: str
    token: str
    description: str = ""
    is_default: bool = False


@validate_required_fields('key', 'name', 'id')
@dataclass
class JiraProject:
    """Represents a Jira project."""
    key: str
    name: str
    id: str
    lead_name: str | None = None
    lead_email: str | None = None
    url: str | None = None


@validate_required_fields('id', 'author_name', 'body', 'created')
@dataclass
class JiraComment:
    """Represents a Jira issue comment."""
    id: str
    author_name: str
    author_key: str | None
    body: str
    created: str
    updated: str | None = None


@validate_required_fields('id', 'name', 'to_status')
@dataclass
class WorkflowTransition:
    """Represents a Jira workflow transition."""
    id: str
    name: str
    to_status: str
    from_status: str | None = None


@validate_required_fields('key', 'id', 'summary', 'status', 'issue_type', 'priority')
@dataclass
class JiraIssue:
    """Represents a Jira issue with all its properties."""
    key: str
    id: str
    summary: str
    description: str
    status: str
    issue_type: str
    priority: str
    assignee: str | None = None
    reporter: str | None = None
    created: str | None = None
    updated: str | None = None
    components: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)
    comments: list[JiraComment] = field(default_factory=list)
    url: str | None = None

    def add_comment(self, comment: JiraComment) -> None:
        """Add a comment to the issue."""
        self.comments.append(comment)

    def get_latest_comment(self) -> JiraComment | None:
        """Get the most recent comment."""
        if not self.comments:
            return None
        return max(self.comments, key=lambda c: c.created)

    def is_assigned(self) -> bool:
        """Check if the issue is assigned to someone."""
        return self.assignee is not None and self.assignee != "Unassigned"

    def has_labels(self) -> bool:
        """Check if the issue has any labels."""
        return len(self.labels) > 0

    def has_components(self) -> bool:
        """Check if the issue has any components."""
        return len(self.components) > 0


@validate_required_fields('id', 'name', 'category', 'color')
@dataclass
class WorkflowNode:
    """Represents a node in a workflow graph."""
    id: str
    name: str
    category: str
    color: str


@validate_required_fields('from_node', 'to_node', 'label')
@dataclass
class WorkflowEdge:
    """Represents an edge in a workflow graph."""
    from_node: str
    to_node: str
    label: str


@validate_required_fields('project_key', 'issue_type')
@dataclass
class WorkflowGraph:
    """Represents a complete workflow graph."""
    project_key: str
    issue_type: str
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the graph."""
        # Check for duplicate nodes
        if any(n.id == node.id for n in self.nodes):
            raise ValueError(f"Node with ID '{node.id}' already exists")
        self.nodes.append(node)

    def add_edge(self, edge: WorkflowEdge) -> None:
        """Add an edge to the graph."""
        # Validate that both nodes exist
        from_exists = any(n.id == edge.from_node for n in self.nodes)
        to_exists = any(n.id == edge.to_node for n in self.nodes)

        if not from_exists:
            raise ValueError(f"From node '{edge.from_node}' does not exist")
        if not to_exists:
            raise ValueError(f"To node '{edge.to_node}' does not exist")

        self.edges.append(edge)

    def get_node_by_id(self, node_id: str) -> WorkflowNode | None:
        """Get a node by its ID."""
        return next((n for n in self.nodes if n.id == node_id), None)

    def get_outgoing_edges(self, node_id: str) -> list[WorkflowEdge]:
        """Get all edges going out from a node."""
        return [e for e in self.edges if e.from_node == node_id]

    def get_incoming_edges(self, node_id: str) -> list[WorkflowEdge]:
        """Get all edges coming into a node."""
        return [e for e in self.edges if e.to_node == node_id]


@validate_required_fields('field_id', 'name')
@dataclass
class CustomFieldMapping:
    """Represents a mapping between custom field ID and human-readable name."""
    field_id: str
    name: str
    description: str = ""


@validate_required_fields('project_key', 'summary', 'description', 'issue_type')
@dataclass
class IssueCreateRequest:
    """Represents a request to create a new Jira issue."""
    project_key: str
    summary: str
    description: str
    issue_type: str = "Story"
    priority: str | None = None
    assignee: str | None = None
    labels: list[str] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the issue create request."""
        # Validate custom fields structure if provided
        if self.custom_fields:
            self._validate_custom_fields()

    def _validate_custom_fields(self) -> None:
        """Validate custom fields structure."""
        if not isinstance(self.custom_fields, dict):
            raise ValueError("Custom fields must be a dictionary")
        
        for field_id, field_value in self.custom_fields.items():
            if not isinstance(field_id, str):
                raise ValueError(f"Custom field ID must be a string, got {type(field_id)}")
            
            if not field_id.startswith("customfield_"):
                raise ValueError(f"Custom field ID must start with 'customfield_', got '{field_id}'")
            
            # Field value can be various types depending on the field type
            # We'll let Jira validate the specific structure
            if field_value is None:
                raise ValueError(f"Custom field value cannot be None for field '{field_id}'")

    def has_custom_fields(self) -> bool:
        """Check if this request includes custom fields."""
        return len(self.custom_fields) > 0

    def get_custom_field_ids(self) -> list[str]:
        """Get list of custom field IDs in this request."""
        return list(self.custom_fields.keys())


@validate_required_fields('issue_key', 'transition_name')
@dataclass
class IssueTransitionRequest:
    """Represents a request to transition a Jira issue."""
    issue_key: str
    transition_name: str
    comment: str | None = None


@validate_required_fields('issue_key')
@dataclass
class AssigneeChangeRequest:
    """Represents a request to change an issue's assignee."""
    issue_key: str
    assignee: str | None = None  # None means unassign


@validate_required_fields('issue_key', 'comment')
@dataclass
class CommentAddRequest:
    """Represents a request to add a comment to an issue."""
    issue_key: str
    comment: str


@validate_required_fields('link_type', 'source_issue', 'target_issue')
@dataclass
class IssueLink:
    """Represents a link between two Jira issues."""
    link_type: str
    source_issue: str
    target_issue: str
    direction: str = LinkDirection.OUTWARD.value
    link_id: str | None = None

    def __post_init__(self):
        """Validate the issue link."""
        if self.source_issue == self.target_issue:
            raise ValueError("Cannot link an issue to itself")
        if self.direction not in [LinkDirection.INWARD.value, LinkDirection.OUTWARD.value]:
            raise ValueError(f"Invalid link direction: {self.direction}")

    def is_epic_link(self) -> bool:
        """Check if this is an Epic-Story link."""
        return self.link_type == "Epic-Story"

    def is_parent_child_link(self) -> bool:
        """Check if this is a Parent-Child link."""
        return self.link_type == "Parent-Child"

    def get_reverse_direction(self) -> str:
        """Get the reverse direction of this link."""
        return LinkDirection.INWARD.value if self.direction == LinkDirection.OUTWARD.value else LinkDirection.OUTWARD.value


@validate_required_fields('issue_key')
@dataclass
class IssueUpdate:
    """Represents an update to an existing Jira issue."""
    issue_key: str
    fields: dict[str, Any] = field(default_factory=dict)
    summary: str | None = None
    description: str | None = None
    priority: str | None = None
    assignee: str | None = None
    labels: list[str] | None = None

    def __post_init__(self):
        """Validate and prepare the issue update."""
        # Build fields dictionary from individual properties
        if self.summary is not None:
            self.fields['summary'] = self.summary
        if self.description is not None:
            self.fields['description'] = self.description
        if self.priority is not None:
            self.fields['priority'] = self.priority
        if self.assignee is not None:
            self.fields['assignee'] = self.assignee
        if self.labels is not None:
            self.fields['labels'] = self.labels

        if not self.fields:
            raise ValueError("At least one field must be provided for update")

    def has_field(self, field_name: str) -> bool:
        """Check if a specific field is being updated."""
        return field_name in self.fields

    def get_field_value(self, field_name: str) -> Any:
        """Get the value for a specific field."""
        return self.fields.get(field_name)

    def get_updated_fields(self) -> list[str]:
        """Get a list of all fields being updated."""
        return list(self.fields.keys())


@validate_required_fields('project_key')
@dataclass
class SearchFilters:
    """Represents search filters for simple project-based searches."""
    project_key: str
    status: str | None = None
    issue_type: str | None = None
    max_results: int = 50
    start_at: int = 0

    def __post_init__(self):
        """Validate the search filters."""
        if not self.project_key or not self.project_key.strip():
            raise ValueError("Project key cannot be empty")
        if self.max_results <= 0:
            raise ValueError("Max results must be greater than 0")
        if self.max_results > 1000:
            raise ValueError("Max results cannot exceed 1000")
        if self.start_at < 0:
            raise ValueError("Start at cannot be negative")

    def has_status_filter(self) -> bool:
        """Check if status filter is applied."""
        return self.status is not None and self.status.strip() != ""

    def has_issue_type_filter(self) -> bool:
        """Check if issue type filter is applied."""
        return self.issue_type is not None and self.issue_type.strip() != ""

    def has_pagination(self) -> bool:
        """Check if this filter uses pagination."""
        return self.start_at > 0

    def get_next_page_filters(self) -> 'SearchFilters':
        """Get filters for the next page of results."""
        return SearchFilters(
            project_key=self.project_key,
            status=self.status,
            issue_type=self.issue_type,
            max_results=self.max_results,
            start_at=self.start_at + self.max_results
        )

    def get_active_filters(self) -> dict[str, str]:
        """Get a dictionary of active (non-None) filters."""
        filters = {"project": self.project_key}
        if self.has_status_filter():
            filters["status"] = self.status
        if self.has_issue_type_filter():
            filters["issuetype"] = self.issue_type
        return filters


@validate_required_fields('jql')
@dataclass
class SearchQuery:
    """Represents a JQL search query."""
    jql: str
    max_results: int = 50
    start_at: int = 0
    fields: list[str] | None = None

    def __post_init__(self):
        """Validate the search query."""
        if self.max_results <= 0:
            raise ValueError("Max results must be greater than 0")
        if self.max_results > 1000:
            raise ValueError("Max results cannot exceed 1000")
        if self.start_at < 0:
            raise ValueError("Start at cannot be negative")

    def has_pagination(self) -> bool:
        """Check if this query uses pagination."""
        return self.start_at > 0

    def get_next_page_query(self) -> 'SearchQuery':
        """Get a query for the next page of results."""
        return SearchQuery(
            jql=self.jql,
            max_results=self.max_results,
            start_at=self.start_at + self.max_results,
            fields=self.fields
        )


@validate_required_fields('jql')
@dataclass
class SearchResult:
    """Represents the result of a JQL search."""
    jql: str
    total_results: int
    start_at: int
    max_results: int
    issues: list[JiraIssue] = field(default_factory=list)

    def __post_init__(self):
        """Validate the search result."""
        if self.total_results < 0:
            raise ValueError("Total results cannot be negative")
        if self.start_at < 0:
            raise ValueError("Start at cannot be negative")
        if self.max_results <= 0:
            raise ValueError("Max results must be greater than 0")

    def has_more_results(self) -> bool:
        """Check if there are more results available."""
        return self.start_at + len(self.issues) < self.total_results

    def get_next_start_at(self) -> int:
        """Get the start_at value for the next page."""
        return self.start_at + len(self.issues)


@validate_required_fields('issue_key')
@dataclass
class IssueUpdateResult:
    """Represents the result of an issue update operation."""
    issue_key: str
    updated: bool
    updated_fields: list[str] = field(default_factory=list)
    error: str | None = None

    def is_successful(self) -> bool:
        """Check if the update was successful."""
        return self.updated and self.error is None


@validate_required_fields('source_issue', 'target_issue', 'link_type')
@dataclass
class IssueLinkResult:
    """Represents the result of an issue link operation."""
    source_issue: str
    target_issue: str
    link_type: str
    created: bool
    link_id: str | None = None
    error: str | None = None

    def is_successful(self) -> bool:
        """Check if the link creation was successful."""
        return self.created and self.error is None


@validate_required_fields('project_key', 'summary', 'description', 'issue_type')
@dataclass
class IssueCreateWithLinksRequest:
    """Represents a request to create a new issue with links."""
    project_key: str
    summary: str
    description: str
    issue_type: str = "Story"
    priority: str | None = None
    assignee: str | None = None
    labels: list[str] = field(default_factory=list)
    links: list[IssueLink] = field(default_factory=list)

    def has_links(self) -> bool:
        """Check if this request includes links."""
        return len(self.links) > 0

    def get_epic_links(self) -> list[IssueLink]:
        """Get all Epic-Story links from this request."""
        return [link for link in self.links if link.is_epic_link()]

    def get_parent_child_links(self) -> list[IssueLink]:
        """Get all Parent-Child links from this request."""
        return [link for link in self.links if link.is_parent_child_link()]


@dataclass
class WorkLog:
    """Represents a work log entry on a Jira issue."""
    id: str | None = None
    author: str | None = None
    time_spent: str = ""  # e.g., "2h 30m", "1d", "45m"
    time_spent_seconds: int = 0
    comment: str = ""
    started: str | None = None  # ISO datetime string
    created: str | None = None
    updated: str | None = None

    def __post_init__(self):
        """Validate the work log entry."""
        if not self.time_spent and self.time_spent_seconds <= 0:
            raise ValueError("Either time_spent or time_spent_seconds must be provided")

        if self.time_spent_seconds < 0:
            raise ValueError("Time spent cannot be negative")

    def get_time_in_hours(self) -> float:
        """Get time spent in hours as a float."""
        if self.time_spent_seconds > 0:
            return self.time_spent_seconds / 3600.0
        return 0.0

    def get_time_in_minutes(self) -> int:
        """Get time spent in minutes as an integer."""
        if self.time_spent_seconds > 0:
            return self.time_spent_seconds // 60
        return 0


@dataclass
class TimeTrackingInfo:
    """Represents time tracking information for an issue."""
    original_estimate: str | None = None  # e.g., "1w 2d 3h"
    remaining_estimate: str | None = None
    time_spent: str | None = None
    original_estimate_seconds: int = 0
    remaining_estimate_seconds: int = 0
    time_spent_seconds: int = 0

    def __post_init__(self):
        """Validate time tracking information."""
        if self.original_estimate_seconds < 0:
            raise ValueError("Original estimate cannot be negative")
        if self.remaining_estimate_seconds < 0:
            raise ValueError("Remaining estimate cannot be negative")
        if self.time_spent_seconds < 0:
            raise ValueError("Time spent cannot be negative")

    def get_progress_percentage(self) -> float:
        """Calculate progress percentage based on original estimate and time spent."""
        if self.original_estimate_seconds <= 0:
            return 0.0
        return min(100.0, (self.time_spent_seconds / self.original_estimate_seconds) * 100.0)

    def is_over_estimate(self) -> bool:
        """Check if time spent exceeds original estimate."""
        return self.original_estimate_seconds > 0 and self.time_spent_seconds > self.original_estimate_seconds

    def get_remaining_hours(self) -> float:
        """Get remaining estimate in hours."""
        return self.remaining_estimate_seconds / 3600.0 if self.remaining_estimate_seconds > 0 else 0.0


@validate_required_fields('issue_key', 'time_spent')
@dataclass
class WorkLogRequest:
    """Represents a request to log work on an issue."""
    issue_key: str
    time_spent: str  # e.g., "2h 30m", "1d", "45m"
    comment: str = ""
    started: str | None = None  # ISO datetime string, defaults to now
    adjust_estimate: str = "auto"  # "new", "leave", "manual", "auto"
    new_estimate: str | None = None  # Required if adjust_estimate is "new" or "manual"
    reduce_by: str | None = None  # Required if adjust_estimate is "manual"

    def __post_init__(self):
        """Validate the work log request."""
        valid_adjust_options = ["new", "leave", "manual", "auto"]
        if self.adjust_estimate not in valid_adjust_options:
            # Ensure we have a proper list for joining
            options_str = ", ".join(str(option) for option in valid_adjust_options)
            raise ValueError(f"Adjust estimate must be one of: {options_str}")

        if self.adjust_estimate == "new" and not self.new_estimate:
            raise ValueError("New estimate is required when adjust_estimate is 'new'")

        if self.adjust_estimate == "manual" and not self.reduce_by:
            raise ValueError("Reduce by is required when adjust_estimate is 'manual'")

    def is_auto_adjust(self) -> bool:
        """Check if this request uses automatic estimate adjustment."""
        return self.adjust_estimate == "auto"

    def is_manual_adjust(self) -> bool:
        """Check if this request uses manual estimate adjustment."""
        return self.adjust_estimate == "manual"


@validate_required_fields('issue_key')
@dataclass
class TimeEstimateUpdate:
    """Represents a request to update time estimates on an issue."""
    issue_key: str
    original_estimate: str | None = None
    remaining_estimate: str | None = None

    def __post_init__(self):
        """Validate the time estimate update."""
        if not self.original_estimate and not self.remaining_estimate:
            raise ValueError("At least one estimate must be provided")

    def has_original_estimate(self) -> bool:
        """Check if original estimate is being updated."""
        return self.original_estimate is not None

    def has_remaining_estimate(self) -> bool:
        """Check if remaining estimate is being updated."""
        return self.remaining_estimate is not None


@validate_required_fields('issue_key')
@dataclass
class WorkLogResult:
    """Represents the result of a work log operation."""
    issue_key: str
    work_log_id: str | None = None
    logged: bool = False
    time_spent: str = ""
    time_spent_seconds: int = 0
    new_remaining_estimate: str | None = None
    error: str | None = None

    def is_successful(self) -> bool:
        """Check if the work log was successful."""
        return self.logged and self.error is None

    def get_time_in_hours(self) -> float:
        """Get logged time in hours."""
        return self.time_spent_seconds / 3600.0 if self.time_spent_seconds > 0 else 0.0


@validate_required_fields('issue_key')
@dataclass
class TimeEstimateResult:
    """Represents the result of a time estimate update operation."""
    issue_key: str
    updated: bool = False
    original_estimate: str | None = None
    remaining_estimate: str | None = None
    error: str | None = None

    def is_successful(self) -> bool:
        """Check if the estimate update was successful."""
        return self.updated and self.error is None


# Confluence Domain Models

@validate_required_fields('id', 'title', 'space_key')
@dataclass
class ConfluencePage:
    """Represents a Confluence page."""
    id: str
    title: str
    space_key: str
    content: str | None = None
    version: int = 1
    created_date: str | None = None
    modified_date: str | None = None
    author: str | None = None
    url: str | None = None

    def has_content(self) -> bool:
        """Check if the page has content."""
        return self.content is not None and len(self.content.strip()) > 0

    def is_recently_updated(self, days: int = 7) -> bool:
        """Check if the page was updated recently (requires modified_date)."""
        if not self.modified_date:
            return False
        # This would need actual date parsing in a real implementation
        return True  # Simplified for now

    def get_content_length(self) -> int:
        """Get the length of the page content."""
        return len(self.content) if self.content else 0


@validate_required_fields('key', 'name')
@dataclass
class ConfluenceSpace:
    """Represents a Confluence space."""
    key: str
    name: str
    description: str | None = None
    homepage_id: str | None = None
    type: str = "global"  # personal, global, etc.

    def is_personal_space(self) -> bool:
        """Check if this is a personal space."""
        return self.type == "personal"

    def has_homepage(self) -> bool:
        """Check if the space has a homepage defined."""
        return self.homepage_id is not None


@validate_required_fields('pages', 'total_results')
@dataclass
class ConfluenceSearchResult:
    """Represents the result of a Confluence search."""
    pages: list[ConfluencePage]
    total_results: int
    limit: int = 50
    start: int = 0

    def __post_init__(self):
        """Validate the search result."""
        if self.total_results < 0:
            raise ValueError("Total results cannot be negative")
        if self.start < 0:
            raise ValueError("Start cannot be negative")
        if self.limit <= 0:
            raise ValueError("Limit must be greater than 0")

    def has_more_results(self) -> bool:
        """Check if there are more results available."""
        return self.start + len(self.pages) < self.total_results

    def get_next_start(self) -> int:
        """Get the start value for the next page."""
        return self.start + len(self.pages)

    def is_empty(self) -> bool:
        """Check if the search returned no results."""
        return len(self.pages) == 0


@validate_required_fields('space_key', 'title', 'content')
@dataclass
class ConfluencePageCreateRequest:
    """Represents a request to create a new Confluence page."""
    space_key: str
    title: str
    content: str
    parent_page_id: str | None = None

    def __post_init__(self):
        """Validate the page create request."""
        if not self.title.strip():
            raise ValueError("Page title cannot be empty")
        if not self.content.strip():
            raise ValueError("Page content cannot be empty")

    def has_parent(self) -> bool:
        """Check if this page has a parent page."""
        return self.parent_page_id is not None


@validate_required_fields('page_id', 'title', 'content', 'version')
@dataclass
class ConfluencePageUpdateRequest:
    """Represents a request to update an existing Confluence page."""
    page_id: str
    title: str
    content: str
    version: int

    def __post_init__(self):
        """Validate the page update request."""
        if not self.title.strip():
            raise ValueError("Page title cannot be empty")
        if not self.content.strip():
            raise ValueError("Page content cannot be empty")
        if self.version <= 0:
            raise ValueError("Version must be greater than 0")

    def get_next_version(self) -> int:
        """Get the next version number for the update."""
        return self.version + 1
