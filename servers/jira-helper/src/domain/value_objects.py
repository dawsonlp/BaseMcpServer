"""
Value objects for the Jira Helper domain.

This module contains type-safe value objects that replace primitive obsession
and provide validation, parsing, and rich behavior for domain concepts.
"""

import re
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class IssueKey:
    """Type-safe wrapper for Jira issue keys (e.g., PROJ-123)."""
    
    value: str
    
    # Pattern for valid issue keys: PROJECT-NUMBER
    _PATTERN: ClassVar[re.Pattern] = re.compile(r'^[A-Z][A-Z0-9]*-\d+$')
    
    def __post_init__(self):
        """Validate issue key format on creation."""
        if not self._PATTERN.match(self.value):
            raise ValueError(
                f"Invalid issue key format: '{self.value}'. "
                f"Expected format: PROJECT-NUMBER (e.g., PROJ-123)"
            )
    
    @property
    def project_key(self) -> str:
        """Extract the project key portion (e.g., 'PROJ' from 'PROJ-123')."""
        return self.value.split('-')[0]
    
    @property
    def issue_number(self) -> int:
        """Extract the issue number portion (e.g., 123 from 'PROJ-123')."""
        return int(self.value.split('-')[1])
    
    def __str__(self) -> str:
        """String representation of the issue key."""
        return self.value
    
    @classmethod
    def from_string(cls, key_str: str) -> "IssueKey":
        """Create IssueKey from string with validation."""
        return cls(key_str.strip().upper())
    
    def is_valid(self) -> bool:
        """Check if the issue key format is valid."""
        return bool(self._PATTERN.match(self.value))


@dataclass(frozen=True)
class ProjectKey:
    """Type-safe wrapper for Jira project keys (e.g., PROJ, DEV, TEST)."""
    
    value: str
    
    # Pattern for valid project keys: 2-10 uppercase letters/numbers
    _PATTERN: ClassVar[re.Pattern] = re.compile(r'^[A-Z][A-Z0-9]{1,9}$')
    
    def __post_init__(self):
        """Validate project key format on creation."""
        if not self._PATTERN.match(self.value):
            raise ValueError(
                f"Invalid project key format: '{self.value}'. "
                f"Expected: 2-10 uppercase letters/numbers starting with letter"
            )
    
    def __str__(self) -> str:
        """String representation of the project key."""
        return self.value
    
    @classmethod
    def from_string(cls, key_str: str) -> "ProjectKey":
        """Create ProjectKey from string with validation."""
        return cls(key_str.strip().upper())
    
    def is_valid(self) -> bool:
        """Check if the project key format is valid."""
        return bool(self._PATTERN.match(self.value))


@dataclass(frozen=True)
class TimeSpan:
    """Type-safe wrapper for time durations with parsing support."""
    
    total_seconds: int
    
    # Common time unit conversions
    _UNITS: ClassVar[dict[str, int]] = {
        'm': 60,           # minutes
        'h': 3600,         # hours  
        'd': 28800,        # days (8 hours)
        'w': 144000,       # weeks (5 days * 8 hours)
    }
    
    def __post_init__(self):
        """Validate that total_seconds is non-negative."""
        if self.total_seconds < 0:
            raise ValueError(f"Time span cannot be negative: {self.total_seconds} seconds")
    
    @property
    def minutes(self) -> int:
        """Get total minutes."""
        return self.total_seconds // 60
    
    @property
    def hours(self) -> int:
        """Get total hours."""
        return self.total_seconds // 3600
    
    @property
    def days(self) -> int:
        """Get total days (8-hour work days)."""
        return self.total_seconds // 28800
    
    @property
    def weeks(self) -> int:
        """Get total weeks (5-day work weeks)."""
        return self.total_seconds // 144000
    
    def __str__(self) -> str:
        """Format as human-readable string (e.g., '2h 30m', '1d', '45m')."""
        if self.total_seconds == 0:
            return "0m"
        
        parts = []
        remaining = self.total_seconds
        
        # Weeks
        if remaining >= self._UNITS['w']:
            weeks = remaining // self._UNITS['w']
            parts.append(f"{weeks}w")
            remaining %= self._UNITS['w']
        
        # Days
        if remaining >= self._UNITS['d']:
            days = remaining // self._UNITS['d']
            parts.append(f"{days}d")
            remaining %= self._UNITS['d']
        
        # Hours
        if remaining >= self._UNITS['h']:
            hours = remaining // self._UNITS['h']
            parts.append(f"{hours}h")
            remaining %= self._UNITS['h']
        
        # Minutes
        if remaining >= self._UNITS['m']:
            minutes = remaining // self._UNITS['m']
            parts.append(f"{minutes}m")
        
        return " ".join(parts)
    
    @classmethod
    def from_string(cls, time_str: str) -> "TimeSpan":
        """
        Parse time string into TimeSpan.
        
        Supports formats like:
        - '2h 30m' -> 2.5 hours
        - '1d' -> 1 day (8 hours)
        - '45m' -> 45 minutes
        - '1w 2d 3h' -> 1 week, 2 days, 3 hours
        """
        if not time_str or not time_str.strip():
            return cls(0)
        
        # Pattern to match time components: number + unit
        pattern = re.compile(r'(\d+)([wdhm])')
        matches = pattern.findall(time_str.lower().strip())
        
        if not matches:
            raise ValueError(
                f"Invalid time format: '{time_str}'. "
                f"Expected format: '2h 30m', '1d', '45m', etc."
            )
        
        total_seconds = 0
        for amount_str, unit in matches:
            amount = int(amount_str)
            if unit not in cls._UNITS:
                raise ValueError(f"Unknown time unit: '{unit}'. Valid units: w, d, h, m")
            total_seconds += amount * cls._UNITS[unit]
        
        return cls(total_seconds)
    
    @classmethod
    def from_minutes(cls, minutes: int) -> "TimeSpan":
        """Create TimeSpan from minutes."""
        return cls(minutes * 60)
    
    @classmethod
    def from_hours(cls, hours: int) -> "TimeSpan":
        """Create TimeSpan from hours."""
        return cls(hours * 3600)
    
    @classmethod
    def from_days(cls, days: int) -> "TimeSpan":
        """Create TimeSpan from days (8-hour work days)."""
        return cls(days * 28800)
    
    def add(self, other: "TimeSpan") -> "TimeSpan":
        """Add two time spans together."""
        return TimeSpan(self.total_seconds + other.total_seconds)
    
    def subtract(self, other: "TimeSpan") -> "TimeSpan":
        """Subtract another time span from this one."""
        result_seconds = self.total_seconds - other.total_seconds
        if result_seconds < 0:
            result_seconds = 0
        return TimeSpan(result_seconds)


@dataclass(frozen=True)
class JqlQuery:
    """Type-safe wrapper for JQL queries with basic validation."""
    
    query: str
    
    # Common JQL keywords for basic validation
    _KEYWORDS: ClassVar[set[str]] = {
        'project', 'key', 'summary', 'description', 'status', 'assignee', 
        'reporter', 'created', 'updated', 'priority', 'type', 'labels',
        'and', 'or', 'not', 'in', 'is', 'was', 'order', 'by', 'asc', 'desc'
    }
    
    def __post_init__(self):
        """Basic validation of JQL query."""
        if not self.query or not self.query.strip():
            raise ValueError("JQL query cannot be empty")
        
        # Check for potential SQL injection patterns
        dangerous_patterns = ['drop', 'delete', 'insert', 'update', 'create', 'alter']
        query_lower = self.query.lower()
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                raise ValueError(f"Potentially dangerous pattern detected in JQL: '{pattern}'")
    
    def __str__(self) -> str:
        """String representation of the JQL query."""
        return self.query
    
    @classmethod
    def from_string(cls, query_str: str) -> "JqlQuery":
        """Create JqlQuery from string with validation."""
        return cls(query_str.strip())
    
    def has_keyword(self, keyword: str) -> bool:
        """Check if query contains a specific JQL keyword."""
        return keyword.lower() in self.query.lower()
    
    def is_simple_project_query(self) -> bool:
        """Check if this is a simple project-based query."""
        return self.has_keyword('project') and '=' in self.query


@dataclass(frozen=True)
class InstanceName:
    """Type-safe wrapper for Jira instance names with validation."""
    
    name: str
    
    # Pattern for valid instance names: alphanumeric, hyphens, underscores
    _PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')
    
    def __post_init__(self):
        """Validate instance name format on creation."""
        if not self.name or not self.name.strip():
            raise ValueError("Instance name cannot be empty")
        
        if not self._PATTERN.match(self.name):
            raise ValueError(
                f"Invalid instance name format: '{self.name}'. "
                f"Must contain only letters, numbers, hyphens, and underscores. "
                f"Cannot start or end with hyphen/underscore."
            )
    
    def __str__(self) -> str:
        """String representation of the instance name."""
        return self.name
    
    @classmethod
    def from_string(cls, name_str: str) -> "InstanceName":
        """Create InstanceName from string with validation."""
        return cls(name_str.strip().lower())
    
    def is_valid(self) -> bool:
        """Check if the instance name format is valid."""
        return bool(self._PATTERN.match(self.name))


# Flexible value objects for configurable Jira values
@dataclass(frozen=True)
class IssueType:
    """Type-safe wrapper for issue types that handles custom values."""
    
    name: str
    
    # Common issue types as class constants for convenience
    STORY: ClassVar[str] = "Story"
    TASK: ClassVar[str] = "Task"
    BUG: ClassVar[str] = "Bug"
    EPIC: ClassVar[str] = "Epic"
    SUBTASK: ClassVar[str] = "Sub-task"
    
    def __post_init__(self):
        """Validate issue type name."""
        if not self.name or not self.name.strip():
            raise ValueError("Issue type name cannot be empty")
    
    def __str__(self) -> str:
        """String representation of the issue type."""
        return self.name
    
    @classmethod
    def from_string(cls, type_str: str) -> "IssueType":
        """Create IssueType from string."""
        return cls(type_str.strip())
    
    def is_standard_type(self) -> bool:
        """Check if this is a standard Jira issue type."""
        return self.name in {self.STORY, self.TASK, self.BUG, self.EPIC, self.SUBTASK}
    
    @classmethod
    def story(cls) -> "IssueType":
        """Create a Story issue type."""
        return cls(cls.STORY)
    
    @classmethod
    def task(cls) -> "IssueType":
        """Create a Task issue type."""
        return cls(cls.TASK)
    
    @classmethod
    def bug(cls) -> "IssueType":
        """Create a Bug issue type."""
        return cls(cls.BUG)
    
    @classmethod
    def epic(cls) -> "IssueType":
        """Create an Epic issue type."""
        return cls(cls.EPIC)


@dataclass(frozen=True)
class Priority:
    """Type-safe wrapper for priorities that handles custom values."""
    
    name: str
    
    # Common priorities as class constants for convenience
    HIGHEST: ClassVar[str] = "Highest"
    HIGH: ClassVar[str] = "High"
    MEDIUM: ClassVar[str] = "Medium"
    LOW: ClassVar[str] = "Low"
    LOWEST: ClassVar[str] = "Lowest"
    
    def __post_init__(self):
        """Validate priority name."""
        if not self.name or not self.name.strip():
            raise ValueError("Priority name cannot be empty")
    
    def __str__(self) -> str:
        """String representation of the priority."""
        return self.name
    
    @classmethod
    def from_string(cls, priority_str: str) -> "Priority":
        """Create Priority from string."""
        return cls(priority_str.strip())
    
    def is_standard_priority(self) -> bool:
        """Check if this is a standard Jira priority."""
        return self.name in {self.HIGHEST, self.HIGH, self.MEDIUM, self.LOW, self.LOWEST}
    
    @classmethod
    def high(cls) -> "Priority":
        """Create a High priority."""
        return cls(cls.HIGH)
    
    @classmethod
    def medium(cls) -> "Priority":
        """Create a Medium priority."""
        return cls(cls.MEDIUM)
    
    @classmethod
    def low(cls) -> "Priority":
        """Create a Low priority."""
        return cls(cls.LOW)


@dataclass(frozen=True)
class Status:
    """Type-safe wrapper for statuses that handles custom values."""
    
    name: str
    category: str = "To Do"  # Default category
    
    # Common statuses as class constants for convenience
    TODO: ClassVar[str] = "To Do"
    IN_PROGRESS: ClassVar[str] = "In Progress"
    DONE: ClassVar[str] = "Done"
    OPEN: ClassVar[str] = "Open"
    CLOSED: ClassVar[str] = "Closed"
    RESOLVED: ClassVar[str] = "Resolved"
    
    def __post_init__(self):
        """Validate status name."""
        if not self.name or not self.name.strip():
            raise ValueError("Status name cannot be empty")
        
        # Validate category is one of the three fixed categories
        valid_categories = {"To Do", "In Progress", "Done"}
        if self.category not in valid_categories:
            raise ValueError(f"Invalid status category: '{self.category}'. Must be one of: {valid_categories}")
    
    def __str__(self) -> str:
        """String representation of the status."""
        return self.name
    
    @classmethod
    def from_string(cls, status_str: str, category: str = "To Do") -> "Status":
        """Create Status from string with optional category."""
        return cls(status_str.strip(), category)
    
    def is_standard_status(self) -> bool:
        """Check if this is a standard Jira status."""
        return self.name in {self.TODO, self.IN_PROGRESS, self.DONE, self.OPEN, self.CLOSED, self.RESOLVED}
    
    def is_todo(self) -> bool:
        """Check if status is in 'To Do' category."""
        return self.category == "To Do"
    
    def is_in_progress(self) -> bool:
        """Check if status is in 'In Progress' category."""
        return self.category == "In Progress"
    
    def is_done(self) -> bool:
        """Check if status is in 'Done' category."""
        return self.category == "Done"


@dataclass(frozen=True)
class LinkType:
    """Type-safe wrapper for link types that handles custom values."""
    
    name: str
    direction: str = "outward"  # Default direction
    
    # Common link types as class constants for convenience
    EPIC_STORY: ClassVar[str] = "Epic-Story"
    PARENT_CHILD: ClassVar[str] = "Parent-Child"
    BLOCKS: ClassVar[str] = "Blocks"
    CLONES: ClassVar[str] = "Clones"
    DUPLICATES: ClassVar[str] = "Duplicates"
    RELATES: ClassVar[str] = "Relates"
    
    def __post_init__(self):
        """Validate link type name and direction."""
        if not self.name or not self.name.strip():
            raise ValueError("Link type name cannot be empty")
        
        # Validate direction is one of the two fixed directions
        valid_directions = {"inward", "outward"}
        if self.direction not in valid_directions:
            raise ValueError(f"Invalid link direction: '{self.direction}'. Must be one of: {valid_directions}")
    
    def __str__(self) -> str:
        """String representation of the link type."""
        return self.name
    
    @classmethod
    def from_string(cls, type_str: str, direction: str = "outward") -> "LinkType":
        """Create LinkType from string with optional direction."""
        return cls(type_str.strip(), direction)
    
    def is_standard_type(self) -> bool:
        """Check if this is a standard Jira link type."""
        return self.name in {self.EPIC_STORY, self.PARENT_CHILD, self.BLOCKS, self.CLONES, self.DUPLICATES, self.RELATES}
    
    def is_outward(self) -> bool:
        """Check if this is an outward link."""
        return self.direction == "outward"
    
    def is_inward(self) -> bool:
        """Check if this is an inward link."""
        return self.direction == "inward"
    
    def reverse(self) -> "LinkType":
        """Create a reversed link type (inward <-> outward)."""
        new_direction = "inward" if self.direction == "outward" else "outward"
        return LinkType(self.name, new_direction)
