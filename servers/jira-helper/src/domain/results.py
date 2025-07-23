"""
Generic result patterns for type-safe operation results.

This module provides standardized result types that preserve specific data types
while providing consistent success/failure handling across all operations.
"""

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar('T')


@dataclass
class OperationResult(Generic[T]):
    """
    Generic result type that preserves specific data types.
    
    This replaces multiple specific result types while maintaining type safety.
    The generic parameter T preserves the specific type information.
    """
    
    success: bool
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def is_success(self) -> bool:
        """Check if the operation was successful."""
        return self.success
    
    def is_failure(self) -> bool:
        """Check if the operation failed."""
        return not self.success
    
    def has_data(self) -> bool:
        """Check if result contains data."""
        return self.data is not None
    
    def has_error(self) -> bool:
        """Check if result contains an error."""
        return self.error is not None and self.error.strip() != ""
    
    def get_data(self) -> T | None:
        """Get the result data."""
        return self.data
    
    def get_error(self) -> str:
        """Get the error message, or empty string if no error."""
        return self.error if self.error else ""
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value by key."""
        return self.metadata.get(key, default)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the result."""
        self.metadata[key] = value
    
    @classmethod
    def success_with(cls, data: T, **metadata) -> "OperationResult[T]":
        """Create a successful result with data."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def failure_with(cls, error: str, **metadata) -> "OperationResult[T]":
        """Create a failed result with error message."""
        return cls(success=False, error=error, metadata=metadata)
    
    @classmethod
    def success_empty(cls, **metadata) -> "OperationResult[None]":
        """Create a successful result without data."""
        return cls(success=True, data=None, metadata=metadata)
    
    def map(self, func) -> "OperationResult":
        """
        Transform the data if the result is successful.
        
        Args:
            func: Function to transform the data
            
        Returns:
            New OperationResult with transformed data, or the same error result
        """
        if self.is_failure():
            return OperationResult.failure_with(self.get_error(), **self.metadata)
        
        try:
            transformed_data = func(self.data) if self.data is not None else None
            return OperationResult.success_with(transformed_data, **self.metadata)
        except Exception as e:
            return OperationResult.failure_with(f"Transformation failed: {str(e)}", **self.metadata)
    
    def flat_map(self, func) -> "OperationResult":
        """
        Transform the data with a function that returns an OperationResult.
        
        Args:
            func: Function that takes data and returns OperationResult
            
        Returns:
            The result of the function, or the original error result
        """
        if self.is_failure():
            return self
        
        try:
            return func(self.data)
        except Exception as e:
            return OperationResult.failure_with(f"Operation failed: {str(e)}", **self.metadata)
    
    def or_else(self, default: T) -> T:
        """Get the data or return a default value if the result failed."""
        return self.data if self.is_success() and self.data is not None else default
    
    def or_else_get(self, supplier) -> T:
        """Get the data or return the result of a supplier function if the result failed."""
        return self.data if self.is_success() and self.data is not None else supplier()


@dataclass
class ValidationResult:
    """
    Result type specifically for validation operations.
    
    This provides detailed validation feedback with multiple error/warning messages.
    """
    
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are validation warnings."""
        return len(self.warnings) > 0
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def add_errors(self, errors: list[str]) -> None:
        """Add multiple validation errors."""
        self.errors.extend(errors)
        if errors:
            self.is_valid = False
    
    def add_warnings(self, warnings: list[str]) -> None:
        """Add multiple validation warnings."""
        self.warnings.extend(warnings)
    
    def get_all_messages(self) -> list[str]:
        """Get all error and warning messages combined."""
        return self.errors + self.warnings
    
    def get_error_summary(self) -> str:
        """Get a summary of all errors as a single string."""
        return "; ".join(self.errors) if self.errors else ""
    
    def get_warning_summary(self) -> str:
        """Get a summary of all warnings as a single string."""
        return "; ".join(self.warnings) if self.warnings else ""
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        merged = ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            metadata={**self.metadata, **other.metadata}
        )
        return merged
    
    @classmethod
    def valid(cls, **metadata) -> "ValidationResult":
        """Create a valid result."""
        return cls(is_valid=True, metadata=metadata)
    
    @classmethod
    def invalid(cls, errors: list[str], warnings: list[str] | None = None, **metadata) -> "ValidationResult":
        """Create an invalid result with errors."""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            metadata=metadata
        )
    
    @classmethod
    def with_error(cls, error: str, **metadata) -> "ValidationResult":
        """Create an invalid result with a single error."""
        return cls.invalid([error], **metadata)
    
    @classmethod
    def with_warning(cls, warning: str, **metadata) -> "ValidationResult":
        """Create a valid result with a warning."""
        return cls(is_valid=True, warnings=[warning], metadata=metadata)


@dataclass
class PagedResult(Generic[T]):
    """
    Result type for paginated data.
    
    This provides consistent pagination information along with the data.
    """
    
    items: list[T] = field(default_factory=list)
    total_count: int = 0
    page_size: int = 50
    current_page: int = 1
    start_at: int = 0
    
    def has_items(self) -> bool:
        """Check if there are any items."""
        return len(self.items) > 0
    
    def item_count(self) -> int:
        """Get the number of items in this page."""
        return len(self.items)
    
    def has_next_page(self) -> bool:
        """Check if there are more pages available."""
        return (self.start_at + self.page_size) < self.total_count
    
    def has_previous_page(self) -> bool:
        """Check if there are previous pages."""
        return self.start_at > 0
    
    def total_pages(self) -> int:
        """Get the total number of pages."""
        if self.page_size == 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size
    
    def next_start_at(self) -> int:
        """Get the start_at value for the next page."""
        return self.start_at + self.page_size
    
    def previous_start_at(self) -> int:
        """Get the start_at value for the previous page."""
        return max(0, self.start_at - self.page_size)
    
    def is_first_page(self) -> bool:
        """Check if this is the first page."""
        return self.current_page == 1
    
    def is_last_page(self) -> bool:
        """Check if this is the last page."""
        return self.current_page == self.total_pages()
    
    @classmethod
    def empty(cls, page_size: int = 50) -> "PagedResult[T]":
        """Create an empty paged result."""
        return cls(items=[], total_count=0, page_size=page_size, current_page=1, start_at=0)
    
    @classmethod
    def single_page(cls, items: list[T]) -> "PagedResult[T]":
        """Create a single-page result with all items."""
        return cls(
            items=items,
            total_count=len(items),
            page_size=len(items) if items else 50,
            current_page=1,
            start_at=0
        )


@dataclass
class BulkOperationResult(Generic[T]):
    """
    Result type for bulk operations that process multiple items.
    
    This provides detailed information about successes and failures in bulk operations.
    """
    
    total_processed: int = 0
    successful_items: list[T] = field(default_factory=list)
    failed_items: list[dict[str, Any]] = field(default_factory=list)  # Contains item + error info
    warnings: list[str] = field(default_factory=list)
    
    def success_count(self) -> int:
        """Get the number of successfully processed items."""
        return len(self.successful_items)
    
    def failure_count(self) -> int:
        """Get the number of failed items."""
        return len(self.failed_items)
    
    def has_failures(self) -> bool:
        """Check if any items failed."""
        return self.failure_count() > 0
    
    def has_successes(self) -> bool:
        """Check if any items succeeded."""
        return self.success_count() > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def is_complete_success(self) -> bool:
        """Check if all items were processed successfully."""
        return self.failure_count() == 0 and self.success_count() == self.total_processed
    
    def is_complete_failure(self) -> bool:
        """Check if all items failed."""
        return self.success_count() == 0 and self.failure_count() == self.total_processed
    
    def is_partial_success(self) -> bool:
        """Check if some items succeeded and some failed."""
        return self.has_successes() and self.has_failures()
    
    def success_rate(self) -> float:
        """Get the success rate as a percentage (0.0 to 100.0)."""
        if self.total_processed == 0:
            return 0.0
        return (self.success_count() / self.total_processed) * 100.0
    
    def add_success(self, item: T) -> None:
        """Add a successful item."""
        self.successful_items.append(item)
    
    def add_failure(self, item: Any, error: str) -> None:
        """Add a failed item with error information."""
        self.failed_items.append({
            "item": item,
            "error": error
        })
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def get_failure_summary(self) -> str:
        """Get a summary of all failures."""
        if not self.has_failures():
            return ""
        
        errors = [f"Item {i+1}: {failure['error']}" for i, failure in enumerate(self.failed_items)]
        return "; ".join(errors)
    
    @classmethod
    def empty(cls) -> "BulkOperationResult[T]":
        """Create an empty bulk operation result."""
        return cls(total_processed=0)


# Type aliases for common result patterns
IssueResult = OperationResult["JiraIssue"]  # Will be defined when JiraIssue is updated
ProjectResult = OperationResult["JiraProject"]  # Will be defined when JiraProject is updated
SearchResult = OperationResult[PagedResult["JiraIssue"]]  # Paginated search results
CommentResult = OperationResult["JiraComment"]  # Will be defined when JiraComment is updated
LinkResult = OperationResult["IssueLink"]  # Will be defined when IssueLink is updated
WorkLogResult = OperationResult["WorkLog"]  # Will be defined when WorkLog is updated

# Bulk operation type aliases
BulkIssueResult = BulkOperationResult["JiraIssue"]
BulkLinkResult = BulkOperationResult["IssueLink"]
BulkWorkLogResult = BulkOperationResult["WorkLog"]
