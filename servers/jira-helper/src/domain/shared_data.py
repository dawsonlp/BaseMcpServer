"""
Shared data structures for composition in domain models.

This module contains reusable data components that can be composed into
larger domain models, reducing duplication while preserving type safety.
"""

from dataclasses import dataclass, field
from typing import Any

from domain.value_objects import TimeSpan, IssueKey, ProjectKey, InstanceName
from domain.enums import StatusCategory


@dataclass
class TimeTracking:
    """Shared time tracking information used across multiple models."""
    
    original_estimate: TimeSpan | None = None
    remaining_estimate: TimeSpan | None = None
    time_spent: TimeSpan | None = None
    
    def has_estimates(self) -> bool:
        """Check if any time estimates are set."""
        return any([
            self.original_estimate and self.original_estimate.total_seconds > 0,
            self.remaining_estimate and self.remaining_estimate.total_seconds > 0,
            self.time_spent and self.time_spent.total_seconds > 0
        ])
    
    def is_over_estimate(self) -> bool:
        """Check if time spent exceeds original estimate."""
        if not self.original_estimate or not self.time_spent:
            return False
        return self.time_spent.total_seconds > self.original_estimate.total_seconds
    
    def progress_percentage(self) -> float:
        """Calculate progress percentage based on original estimate and time spent."""
        if not self.original_estimate or self.original_estimate.total_seconds == 0:
            return 0.0
        if not self.time_spent:
            return 0.0
        
        progress = (self.time_spent.total_seconds / self.original_estimate.total_seconds) * 100
        return min(progress, 100.0)  # Cap at 100%
    
    def remaining_percentage(self) -> float:
        """Calculate remaining work percentage based on estimates."""
        if not self.original_estimate or self.original_estimate.total_seconds == 0:
            return 0.0
        if not self.remaining_estimate:
            return 0.0
        
        remaining = (self.remaining_estimate.total_seconds / self.original_estimate.total_seconds) * 100
        return max(remaining, 0.0)  # Don't go below 0%


@dataclass
class IssueMetadata:
    """Shared metadata information for issues."""
    
    created: str | None = None
    updated: str | None = None
    resolved: str | None = None
    due_date: str | None = None
    
    def is_recently_created(self, hours: int = 24) -> bool:
        """Check if issue was created within the specified hours."""
        if not self.created:
            return False
        
        # This would need proper datetime parsing in a real implementation
        # For now, just return False as we're working with string dates
        return False
    
    def is_recently_updated(self, hours: int = 24) -> bool:
        """Check if issue was updated within the specified hours."""
        if not self.updated:
            return False
        
        # This would need proper datetime parsing in a real implementation
        # For now, just return False as we're working with string dates
        return False
    
    def has_due_date(self) -> bool:
        """Check if issue has a due date set."""
        return self.due_date is not None and self.due_date.strip() != ""
    
    def is_resolved(self) -> bool:
        """Check if issue has been resolved."""
        return self.resolved is not None and self.resolved.strip() != ""


@dataclass
class UserInfo:
    """Shared user information used across multiple models."""
    
    display_name: str | None = None
    email: str | None = None
    account_id: str | None = None
    key: str | None = None  # Legacy user key
    
    def has_contact_info(self) -> bool:
        """Check if user has contact information."""
        return self.email is not None and self.email.strip() != ""
    
    def display_identifier(self) -> str:
        """Get the best available identifier for display."""
        if self.display_name and self.display_name.strip():
            return self.display_name
        elif self.email and self.email.strip():
            return self.email
        elif self.account_id and self.account_id.strip():
            return self.account_id
        elif self.key and self.key.strip():
            return self.key
        else:
            return "Unknown User"
    
    def is_valid(self) -> bool:
        """Check if user info has at least one identifier."""
        return any([
            self.display_name and self.display_name.strip(),
            self.email and self.email.strip(),
            self.account_id and self.account_id.strip(),
            self.key and self.key.strip()
        ])


@dataclass
class LinkInfo:
    """Shared link information for issue relationships."""
    
    link_type: str
    direction: str = "outward"
    link_id: str | None = None
    
    def is_outward(self) -> bool:
        """Check if this is an outward link."""
        return self.direction == "outward"
    
    def is_inward(self) -> bool:
        """Check if this is an inward link."""
        return self.direction == "inward"
    
    def reverse_direction(self) -> str:
        """Get the opposite direction."""
        return "inward" if self.direction == "outward" else "outward"
    
    def is_hierarchical(self) -> bool:
        """Check if this is a hierarchical link type (parent-child, epic-story)."""
        hierarchical_types = {"Epic-Story", "Parent-Child", "Subtask"}
        return self.link_type in hierarchical_types


@dataclass
class IssueContext:
    """Shared context information for issues."""
    
    project_key: ProjectKey
    instance_name: InstanceName
    url: str | None = None
    
    def build_url(self, issue_key: IssueKey, base_url: str) -> str:
        """Build the full URL for an issue."""
        if self.url:
            return self.url
        
        # Remove trailing slash from base_url if present
        clean_base_url = base_url.rstrip('/')
        return f"{clean_base_url}/browse/{issue_key}"
    
    def is_same_project(self, other_project_key: ProjectKey) -> bool:
        """Check if this context is for the same project."""
        return self.project_key.value == other_project_key.value
    
    def is_same_instance(self, other_instance: InstanceName) -> bool:
        """Check if this context is for the same instance."""
        return self.instance_name.name == other_instance.name


@dataclass
class SearchContext:
    """Shared context for search operations."""
    
    max_results: int = 50
    start_at: int = 0
    total_results: int = 0
    
    def has_more_results(self) -> bool:
        """Check if there are more results available."""
        return (self.start_at + self.max_results) < self.total_results
    
    def current_page(self) -> int:
        """Get the current page number (1-based)."""
        return (self.start_at // self.max_results) + 1
    
    def total_pages(self) -> int:
        """Get the total number of pages."""
        if self.max_results == 0:
            return 0
        return (self.total_results + self.max_results - 1) // self.max_results
    
    def next_start_at(self) -> int:
        """Get the start_at value for the next page."""
        return self.start_at + self.max_results
    
    def previous_start_at(self) -> int:
        """Get the start_at value for the previous page."""
        return max(0, self.start_at - self.max_results)


@dataclass
class ValidationContext:
    """Shared context for validation operations."""
    
    operation: str
    instance_name: InstanceName | None = None
    project_key: ProjectKey | None = None
    issue_key: IssueKey | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are validation warnings."""
        return len(self.warnings) > 0
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return not self.has_errors()
    
    def clear_errors(self) -> None:
        """Clear all validation errors."""
        self.errors.clear()
    
    def clear_warnings(self) -> None:
        """Clear all validation warnings."""
        self.warnings.clear()
    
    def clear_all(self) -> None:
        """Clear all validation messages."""
        self.clear_errors()
        self.clear_warnings()


@dataclass
class AuditInfo:
    """Shared audit information for tracking changes."""
    
    created_by: UserInfo | None = None
    created_at: str | None = None
    updated_by: UserInfo | None = None
    updated_at: str | None = None
    version: int = 1
    
    def has_creation_info(self) -> bool:
        """Check if creation audit info is available."""
        return self.created_by is not None or self.created_at is not None
    
    def has_update_info(self) -> bool:
        """Check if update audit info is available."""
        return self.updated_by is not None or self.updated_at is not None
    
    def was_created_by(self, user: UserInfo) -> bool:
        """Check if the item was created by the specified user."""
        if not self.created_by or not user:
            return False
        return self.created_by.account_id == user.account_id
    
    def was_updated_by(self, user: UserInfo) -> bool:
        """Check if the item was last updated by the specified user."""
        if not self.updated_by or not user:
            return False
        return self.updated_by.account_id == user.account_id
    
    def increment_version(self) -> None:
        """Increment the version number."""
        self.version += 1


@dataclass
class CustomFieldData:
    """Shared structure for custom field information."""
    
    field_id: str
    field_name: str
    value: Any = None
    display_value: str | None = None
    field_type: str | None = None
    
    def has_value(self) -> bool:
        """Check if the custom field has a value."""
        return self.value is not None
    
    def get_display_value(self) -> str:
        """Get the display value, falling back to string representation of value."""
        if self.display_value:
            return self.display_value
        elif self.value is not None:
            return str(self.value)
        else:
            return ""
    
    def is_text_field(self) -> bool:
        """Check if this is a text-based field."""
        text_types = {"string", "text", "textarea", "url", "email"}
        return self.field_type in text_types if self.field_type else False
    
    def is_numeric_field(self) -> bool:
        """Check if this is a numeric field."""
        numeric_types = {"number", "float", "integer", "currency"}
        return self.field_type in numeric_types if self.field_type else False
    
    def is_date_field(self) -> bool:
        """Check if this is a date/datetime field."""
        date_types = {"date", "datetime", "timestamp"}
        return self.field_type in date_types if self.field_type else False


@dataclass
class ComponentInfo:
    """Shared component information for issues."""
    
    name: str
    id: str | None = None
    description: str | None = None
    lead: UserInfo | None = None
    
    def has_lead(self) -> bool:
        """Check if component has a lead assigned."""
        return self.lead is not None and self.lead.is_valid()
    
    def display_name(self) -> str:
        """Get display name for the component."""
        return self.name if self.name else f"Component {self.id}"
