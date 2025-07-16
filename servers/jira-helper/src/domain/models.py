"""
Domain models for the Jira Helper.

This module contains the core domain entities that represent Jira concepts.
These models are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .base import validate_required_fields


class IssueType(Enum):
    """Enumeration of Jira issue types."""
    STORY = "Story"
    TASK = "Task"
    EPIC = "Epic"
    BUG = "Bug"
    SUBTASK = "Sub-task"


class Priority(Enum):
    """Enumeration of Jira priorities."""
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"


class StatusCategory(Enum):
    """Enumeration of Jira status categories."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class LinkType(Enum):
    """Enumeration of Jira issue link types."""
    EPIC_STORY = "Epic-Story"
    PARENT_CHILD = "Parent-Child"
    BLOCKS = "Blocks"
    CLONES = "Clones"
    DUPLICATES = "Duplicates"
    RELATES = "Relates"
    CUSTOM = "Custom"


class LinkDirection(Enum):
    """Enumeration of link directions."""
    INWARD = "inward"
    OUTWARD = "outward"


class TimeUnit(Enum):
    """Enumeration of time units for work logging."""
    MINUTES = "m"
    HOURS = "h"
    DAYS = "d"
    WEEKS = "w"


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
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    url: Optional[str] = None


@validate_required_fields('id', 'author_name', 'body', 'created')
@dataclass
class JiraComment:
    """Represents a Jira issue comment."""
    id: str
    author_name: str
    author_key: Optional[str]
    body: str
    created: str
    updated: Optional[str] = None


@validate_required_fields('id', 'name', 'to_status')
@dataclass
class WorkflowTransition:
    """Represents a Jira workflow transition."""
    id: str
    name: str
    to_status: str
    from_status: Optional[str] = None


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
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    components: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    comments: List[JiraComment] = field(default_factory=list)
    url: Optional[str] = None

    def add_comment(self, comment: JiraComment) -> None:
        """Add a comment to the issue."""
        self.comments.append(comment)

    def get_latest_comment(self) -> Optional[JiraComment]:
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
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

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

    def get_node_by_id(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by its ID."""
        return next((n for n in self.nodes if n.id == node_id), None)

    def get_outgoing_edges(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges going out from a node."""
        return [e for e in self.edges if e.from_node == node_id]

    def get_incoming_edges(self, node_id: str) -> List[WorkflowEdge]:
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
    priority: Optional[str] = None
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)


@validate_required_fields('issue_key', 'transition_name')
@dataclass
class IssueTransitionRequest:
    """Represents a request to transition a Jira issue."""
    issue_key: str
    transition_name: str
    comment: Optional[str] = None


@validate_required_fields('issue_key')
@dataclass
class AssigneeChangeRequest:
    """Represents a request to change an issue's assignee."""
    issue_key: str
    assignee: Optional[str] = None  # None means unassign


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
    link_id: Optional[str] = None

    def __post_init__(self):
        """Validate the issue link."""
        if self.source_issue == self.target_issue:
            raise ValueError("Cannot link an issue to itself")
        if self.direction not in [LinkDirection.INWARD.value, LinkDirection.OUTWARD.value]:
            raise ValueError(f"Invalid link direction: {self.direction}")

    def is_epic_link(self) -> bool:
        """Check if this is an Epic-Story link."""
        return self.link_type == LinkType.EPIC_STORY.value

    def is_parent_child_link(self) -> bool:
        """Check if this is a Parent-Child link."""
        return self.link_type == LinkType.PARENT_CHILD.value

    def get_reverse_direction(self) -> str:
        """Get the reverse direction of this link."""
        return LinkDirection.INWARD.value if self.direction == LinkDirection.OUTWARD.value else LinkDirection.OUTWARD.value


@validate_required_fields('issue_key')
@dataclass
class IssueUpdate:
    """Represents an update to an existing Jira issue."""
    issue_key: str
    fields: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None

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

    def get_updated_fields(self) -> List[str]:
        """Get a list of all fields being updated."""
        return list(self.fields.keys())


@validate_required_fields('project_key')
@dataclass
class SearchFilters:
    """Represents search filters for simple project-based searches."""
    project_key: str
    status: Optional[str] = None
    issue_type: Optional[str] = None
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

    def get_active_filters(self) -> Dict[str, str]:
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
    fields: Optional[List[str]] = None

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
    issues: List[JiraIssue] = field(default_factory=list)

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
    updated_fields: List[str] = field(default_factory=list)
    error: Optional[str] = None

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
    link_id: Optional[str] = None
    error: Optional[str] = None

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
    priority: Optional[str] = None
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    links: List[IssueLink] = field(default_factory=list)

    def has_links(self) -> bool:
        """Check if this request includes links."""
        return len(self.links) > 0

    def get_epic_links(self) -> List[IssueLink]:
        """Get all Epic-Story links from this request."""
        return [link for link in self.links if link.is_epic_link()]

    def get_parent_child_links(self) -> List[IssueLink]:
        """Get all Parent-Child links from this request."""
        return [link for link in self.links if link.is_parent_child_link()]


@dataclass
class WorkLog:
    """Represents a work log entry on a Jira issue."""
    id: Optional[str] = None
    author: Optional[str] = None
    time_spent: str = ""  # e.g., "2h 30m", "1d", "45m"
    time_spent_seconds: int = 0
    comment: str = ""
    started: Optional[str] = None  # ISO datetime string
    created: Optional[str] = None
    updated: Optional[str] = None

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
    original_estimate: Optional[str] = None  # e.g., "1w 2d 3h"
    remaining_estimate: Optional[str] = None
    time_spent: Optional[str] = None
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
    started: Optional[str] = None  # ISO datetime string, defaults to now
    adjust_estimate: str = "auto"  # "new", "leave", "manual", "auto"
    new_estimate: Optional[str] = None  # Required if adjust_estimate is "new" or "manual"
    reduce_by: Optional[str] = None  # Required if adjust_estimate is "manual"

    def __post_init__(self):
        """Validate the work log request."""
        valid_adjust_options = ["new", "leave", "manual", "auto"]
        if self.adjust_estimate not in valid_adjust_options:
            raise ValueError(f"Adjust estimate must be one of: {', '.join(valid_adjust_options)}")
        
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
    original_estimate: Optional[str] = None
    remaining_estimate: Optional[str] = None

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
    work_log_id: Optional[str] = None
    logged: bool = False
    time_spent: str = ""
    time_spent_seconds: int = 0
    new_remaining_estimate: Optional[str] = None
    error: Optional[str] = None

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
    original_estimate: Optional[str] = None
    remaining_estimate: Optional[str] = None
    error: Optional[str] = None

    def is_successful(self) -> bool:
        """Check if the estimate update was successful."""
        return self.updated and self.error is None
