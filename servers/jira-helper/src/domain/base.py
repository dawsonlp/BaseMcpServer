"""
Base classes for domain layer to eliminate boilerplate.
"""

from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from abc import ABC, abstractmethod


@dataclass
class BaseResult:
    """Base result class with common success/error patterns."""
    success: bool = True
    error: Optional[str] = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def is_successful(self) -> bool:
        """Check if operation was successful."""
        return self.success and self.error is None

    def add_detail(self, key: str, value: Any) -> None:
        """Add detail information."""
        self.details[key] = value


class FieldValidator:
    """Common field validation utilities."""
    
    @staticmethod
    def validate_non_empty(value: str, field_name: str) -> None:
        """Validate that a field is not empty."""
        if not value or not value.strip():
            raise ValueError(f"{field_name} cannot be empty")
    
    @staticmethod
    def validate_issue_key(issue_key: str) -> None:
        """Validate Jira issue key format."""
        if not issue_key or not issue_key.strip():
            raise ValueError("Issue key cannot be empty")
        if "-" not in issue_key:
            raise ValueError("Issue key must contain project key and number (e.g., PROJ-123)")
        
        # Validate format: PROJECT-NUMBER
        parts = issue_key.split("-")
        if len(parts) != 2:
            raise ValueError("Issue key must be in format PROJECT-NUMBER (e.g., PROJ-123)")
        
        project_part, number_part = parts
        if not project_part or not project_part.strip():
            raise ValueError("Issue key must have a project part (e.g., PROJ-123)")
        if not number_part or not number_part.isdigit():
            raise ValueError("Issue key must have a numeric part (e.g., PROJ-123)")
    
    @staticmethod
    def validate_project_key(project_key: str) -> None:
        """Validate Jira project key format."""
        if not project_key or not project_key.strip():
            raise ValueError("Project key cannot be empty")
    
    @staticmethod
    def validate_max_results(max_results: int) -> None:
        """Validate max results parameter."""
        if max_results <= 0:
            raise ValueError("Max results must be greater than 0")
        if max_results > 1000:
            raise ValueError("Max results cannot exceed 1000")


def validate_required_fields(*field_names):
    """Decorator to add field validation to dataclass by wrapping __init__."""
    def decorator(cls):
        # Store the original __init__ method
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            # Call the original __init__ first to set all fields
            original_init(self, *args, **kwargs)
            
            # Then validate required fields
            for field_name in field_names:
                value = getattr(self, field_name, None)
                if value is None:
                    raise ValueError(f"{field_name} cannot be None")
                if isinstance(value, str) and not value.strip():
                    raise ValueError(f"{field_name} cannot be empty")
        
        # Replace the __init__ method
        cls.__init__ = new_init
        
        # Return the modified class
        return cls
    
    return decorator
