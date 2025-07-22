"""
Simplified domain models for the Jira Helper.

This module contains pure data containers without validation logic,
following proper hexagonal architecture principles.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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


@dataclass
class JiraInstance:
    """Represents a Jira instance configuration."""
    name: str
    url: str
    user: str
    token: str
    description: str = ""
    is_default: bool = False


@dataclass
class JiraProject:
    """Represents a Jira project."""
    key: str
    name: str
    id: str
    lead_name: str | None = None
    lead_email: str | None = None
    url: str | None = None


@dataclass
class JiraComment:
    """Represents a Jira issue comment."""
    id: str
    author_name: str
    body: str
    created: str
    author_key: str | None = None
    updated: str | None = None


@dataclass
class WorkflowTransition:
    """Represents a Jira workflow transition."""
    id: str
    name: str
    to_status: str
    from_status: str | None = None


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


@dataclass
class WorkflowNode:
    """Represents a node in a workflow graph."""
    id: str
    name: str
    category: str
    color: str


@dataclass
class WorkflowEdge:
    """Represents an edge in a workflow graph."""
    from_node: str
    to_node: str
    label: str


@dataclass
class WorkflowGraph:
    """Represents a complete workflow graph."""
    project_key: str
    issue_type: str
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomFieldMapping:
    """Represents a mapping between custom field ID and human-readable name."""
    field_id: str
    name: str
    description: str = ""


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


@dataclass
class IssueTransitionRequest:
    """Represents a request to transition a Jira issue."""
    issue_key: str
    transition_name: str
    comment: str | None = None


@dataclass
class AssigneeChangeRequest:
    """Represents a request to change an issue's assignee."""
    issue_key: str
    assignee: str | None = None  # None means unassign


@dataclass
class CommentAddRequest:
    """Represents a request to add a comment to an issue."""
    issue_key: str
    comment: str


@dataclass
class IssueLink:
    """Represents a link between two Jira issues."""
    link_type: str
    source_issue: str
    target_issue: str
    direction: str = LinkDirection.OUTWARD.value
    link_id: str | None = None


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


@dataclass
class SearchFilters:
    """Represents search filters for simple project-based searches."""
    project_key: str
    status: str | None = None
    issue_type: str | None = None
    max_results: int = 50
    start_at: int = 0


@dataclass
class SearchQuery:
    """Represents a JQL search query."""
    jql: str
    max_results: int = 50
    start_at: int = 0
    fields: list[str] | None = None


@dataclass
class SearchResult:
    """Represents the result of a JQL search."""
    jql: str
    total_results: int
    start_at: int
    max_results: int
    issues: list[JiraIssue] = field(default_factory=list)


@dataclass
class IssueUpdateResult:
    """Represents the result of an issue update operation."""
    issue_key: str
    updated: bool
    updated_fields: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class IssueLinkResult:
    """Represents the result of an issue link operation."""
    source_issue: str
    target_issue: str
    link_type: str
    created: bool
    link_id: str | None = None
    error: str | None = None


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


@dataclass
class TimeTrackingInfo:
    """Represents time tracking information for an issue."""
    original_estimate: str | None = None  # e.g., "1w 2d 3h"
    remaining_estimate: str | None = None
    time_spent: str | None = None
    original_estimate_seconds: int = 0
    remaining_estimate_seconds: int = 0
    time_spent_seconds: int = 0


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


@dataclass
class TimeEstimateUpdate:
    """Represents a request to update time estimates on an issue."""
    issue_key: str
    original_estimate: str | None = None
    remaining_estimate: str | None = None


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


@dataclass
class TimeEstimateResult:
    """Represents the result of a time estimate update operation."""
    issue_key: str
    updated: bool = False
    original_estimate: str | None = None
    remaining_estimate: str | None = None
    error: str | None = None
