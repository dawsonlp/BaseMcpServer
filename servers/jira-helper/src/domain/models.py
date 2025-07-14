"""
Domain models for the Jira Helper.

This module contains the core domain entities that represent Jira concepts.
These models are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


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


@dataclass
class JiraInstance:
    """Represents a Jira instance configuration."""
    name: str
    url: str
    user: str
    token: str
    description: str = ""
    is_default: bool = False

    def __post_init__(self):
        """Validate the instance configuration."""
        if not self.name:
            raise ValueError("Instance name cannot be empty")
        if not self.url:
            raise ValueError("Instance URL cannot be empty")
        if not self.user:
            raise ValueError("Instance user cannot be empty")
        if not self.token:
            raise ValueError("Instance token cannot be empty")


@dataclass
class JiraProject:
    """Represents a Jira project."""
    key: str
    name: str
    id: str
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        """Validate the project data."""
        if not self.key:
            raise ValueError("Project key cannot be empty")
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if not self.id:
            raise ValueError("Project ID cannot be empty")


@dataclass
class JiraComment:
    """Represents a Jira issue comment."""
    id: str
    author_name: str
    author_key: Optional[str]
    body: str
    created: str
    updated: Optional[str] = None

    def __post_init__(self):
        """Validate the comment data."""
        if not self.id:
            raise ValueError("Comment ID cannot be empty")
        if not self.author_name:
            raise ValueError("Comment author name cannot be empty")
        if not self.body:
            raise ValueError("Comment body cannot be empty")
        if not self.created:
            raise ValueError("Comment created date cannot be empty")


@dataclass
class WorkflowTransition:
    """Represents a Jira workflow transition."""
    id: str
    name: str
    to_status: str
    from_status: Optional[str] = None

    def __post_init__(self):
        """Validate the transition data."""
        if not self.id:
            raise ValueError("Transition ID cannot be empty")
        if not self.name:
            raise ValueError("Transition name cannot be empty")
        if not self.to_status:
            raise ValueError("Transition to_status cannot be empty")


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

    def __post_init__(self):
        """Validate the issue data."""
        if not self.key:
            raise ValueError("Issue key cannot be empty")
        if not self.id:
            raise ValueError("Issue ID cannot be empty")
        if not self.summary:
            raise ValueError("Issue summary cannot be empty")
        if not self.status:
            raise ValueError("Issue status cannot be empty")
        if not self.issue_type:
            raise ValueError("Issue type cannot be empty")
        if not self.priority:
            raise ValueError("Issue priority cannot be empty")

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


@dataclass
class WorkflowNode:
    """Represents a node in a workflow graph."""
    id: str
    name: str
    category: str
    color: str

    def __post_init__(self):
        """Validate the node data."""
        if not self.id:
            raise ValueError("Node ID cannot be empty")
        if not self.name:
            raise ValueError("Node name cannot be empty")
        if not self.category:
            raise ValueError("Node category cannot be empty")
        if not self.color:
            raise ValueError("Node color cannot be empty")


@dataclass
class WorkflowEdge:
    """Represents an edge in a workflow graph."""
    from_node: str
    to_node: str
    label: str

    def __post_init__(self):
        """Validate the edge data."""
        if not self.from_node:
            raise ValueError("Edge from_node cannot be empty")
        if not self.to_node:
            raise ValueError("Edge to_node cannot be empty")
        if not self.label:
            raise ValueError("Edge label cannot be empty")


@dataclass
class WorkflowGraph:
    """Represents a complete workflow graph."""
    project_key: str
    issue_type: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the graph data."""
        if not self.project_key:
            raise ValueError("Graph project_key cannot be empty")
        if not self.issue_type:
            raise ValueError("Graph issue_type cannot be empty")

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


@dataclass
class CustomFieldMapping:
    """Represents a mapping between custom field ID and human-readable name."""
    field_id: str
    name: str
    description: str = ""

    def __post_init__(self):
        """Validate the mapping data."""
        if not self.field_id:
            raise ValueError("Field ID cannot be empty")
        if not self.name:
            raise ValueError("Field name cannot be empty")


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

    def __post_init__(self):
        """Validate the create request."""
        if not self.project_key:
            raise ValueError("Project key cannot be empty")
        if not self.summary:
            raise ValueError("Summary cannot be empty")
        if not self.description:
            raise ValueError("Description cannot be empty")
        if not self.issue_type:
            raise ValueError("Issue type cannot be empty")


@dataclass
class IssueTransitionRequest:
    """Represents a request to transition a Jira issue."""
    issue_key: str
    transition_name: str
    comment: Optional[str] = None

    def __post_init__(self):
        """Validate the transition request."""
        if not self.issue_key:
            raise ValueError("Issue key cannot be empty")
        if not self.transition_name:
            raise ValueError("Transition name cannot be empty")


@dataclass
class AssigneeChangeRequest:
    """Represents a request to change an issue's assignee."""
    issue_key: str
    assignee: Optional[str] = None  # None means unassign

    def __post_init__(self):
        """Validate the assignee change request."""
        if not self.issue_key:
            raise ValueError("Issue key cannot be empty")


@dataclass
class CommentAddRequest:
    """Represents a request to add a comment to an issue."""
    issue_key: str
    comment: str

    def __post_init__(self):
        """Validate the comment add request."""
        if not self.issue_key:
            raise ValueError("Issue key cannot be empty")
        if not self.comment:
            raise ValueError("Comment cannot be empty")
