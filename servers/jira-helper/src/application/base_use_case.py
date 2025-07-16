"""
Base use case class to eliminate application layer boilerplate.

This module provides the foundation for all use cases with standardized
result handling, error management, and consistent patterns.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from domain.base import BaseResult

T = TypeVar('T')

logger = logging.getLogger(__name__)


@dataclass
class UseCaseResult[T](BaseResult):
    """Standardized use case result with generic data type."""
    data: T | None = None

    def get_data(self) -> T | None:
        """Get the result data."""
        return self.data

    def has_data(self) -> bool:
        """Check if result contains data."""
        return self.data is not None


class BaseUseCase:
    """Base class for all use cases with standardized patterns."""

    def __init__(self, **dependencies):
        """Initialize use case with dependencies."""
        self._logger = logging.getLogger(self.__class__.__name__)

        # Store dependencies as private attributes
        for key, value in dependencies.items():
            setattr(self, f"_{key}", value)

    async def execute_with_result(
        self,
        operation: Callable,
        success_mapper: Callable | None = None,
        error_mapper: Callable | None = None,
        **context
    ) -> UseCaseResult[Any]:
        """Execute use case with standardized result handling."""
        try:
            # Execute the main operation
            result = await operation()

            # Apply success mapping if provided
            if success_mapper:
                data = success_mapper(result)
            else:
                data = result

            # Log successful execution
            operation_name = operation.__name__ if hasattr(operation, '__name__') else 'operation'
            self._logger.debug(f"Use case {operation_name} completed successfully")

            return UseCaseResult(
                success=True,
                data=data,
                details=context
            )

        except Exception as e:
            # Apply error mapping if provided
            if error_mapper:
                error_message = error_mapper(e)
            else:
                error_message = str(e)

            # Log error
            self._logger.error(f"Use case failed: {error_message}")

            return UseCaseResult(
                success=False,
                error=error_message,
                details=context
            )

    async def execute_simple(
        self,
        operation: Callable,
        **context
    ) -> UseCaseResult[Any]:
        """Execute simple operation without custom mappers."""
        return await self.execute_with_result(operation, **context)

    def _validate_required_params(self, **params) -> None:
        """Validate that required parameters are provided."""
        for key, value in params.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Parameter '{key}' is required and cannot be empty")

    def _build_context(self, **kwargs) -> dict[str, Any]:
        """Build context dictionary for result details."""
        return {k: v for k, v in kwargs.items() if v is not None}


class BaseQueryUseCase(BaseUseCase):
    """Base class for query use cases (read operations)."""

    async def execute_query(
        self,
        query_operation: Callable,
        result_mapper: Callable | None = None,
        **context
    ) -> UseCaseResult[Any]:
        """Execute query with optional result mapping."""
        return await self.execute_with_result(
            query_operation,
            success_mapper=result_mapper,
            **context
        )


class BaseCommandUseCase(BaseUseCase):
    """Base class for command use cases (write operations)."""

    async def execute_command(
        self,
        command_operation: Callable,
        success_mapper: Callable | None = None,
        validation_func: Callable | None = None,
        **context
    ) -> UseCaseResult[Any]:
        """Execute command with optional validation and mapping."""

        # Run validation if provided
        if validation_func:
            try:
                await validation_func()
            except Exception as e:
                return UseCaseResult(
                    success=False,
                    error=f"Validation failed: {str(e)}",
                    details=context
                )

        return await self.execute_with_result(
            command_operation,
            success_mapper=success_mapper,
            **context
        )


class UseCaseFactory:
    """Factory for creating use cases with dependency injection."""

    def __init__(self, **default_dependencies):
        """Initialize factory with default dependencies."""
        self._default_dependencies = default_dependencies

    def create_use_case(self, use_case_class: type, **additional_dependencies) -> BaseUseCase:
        """Create use case instance with injected dependencies."""
        # Merge default and additional dependencies
        dependencies = {**self._default_dependencies, **additional_dependencies}

        return use_case_class(**dependencies)

    def add_dependency(self, name: str, dependency: Any) -> None:
        """Add a default dependency."""
        self._default_dependencies[name] = dependency

    def get_dependency(self, name: str) -> Any:
        """Get a default dependency."""
        return self._default_dependencies.get(name)


# Common result mappers for reuse across use cases
class CommonMappers:
    """Common mapping functions for use case results."""

    @staticmethod
    def to_dict(obj) -> dict[str, Any]:
        """Convert object to dictionary."""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '_asdict'):  # namedtuple
            return obj._asdict()
        else:
            return {"value": obj}

    @staticmethod
    def to_list_dict(objects) -> list:
        """Convert list of objects to list of dictionaries."""
        return [CommonMappers.to_dict(obj) for obj in objects]

    @staticmethod
    def extract_key(obj, key: str):
        """Extract specific key from object."""
        if hasattr(obj, key):
            return getattr(obj, key)
        elif isinstance(obj, dict):
            return obj.get(key)
        else:
            return None

    @staticmethod
    def success_with_message(result, message: str) -> dict[str, Any]:
        """Create success result with custom message."""
        return {
            "result": CommonMappers.to_dict(result) if result else None,
            "message": message
        }

    @staticmethod
    def paginated_result(items, total: int, page: int, page_size: int) -> dict[str, Any]:
        """Create paginated result structure."""
        return {
            "items": CommonMappers.to_list_dict(items),
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": (page * page_size) < total
            }
        }


# Common error mappers
class CommonErrorMappers:
    """Common error mapping functions."""

    @staticmethod
    def domain_error_mapper(error: Exception) -> str:
        """Map domain exceptions to user-friendly messages."""
        error_name = error.__class__.__name__

        # Map common domain exceptions
        error_mappings = {
            'JiraIssueNotFound': 'The requested issue could not be found',
            'JiraProjectNotFound': 'The requested project could not be found',
            'JiraPermissionError': 'You do not have permission to perform this action',
            'JiraAuthenticationError': 'Authentication failed - please check your credentials',
            'JiraConnectionError': 'Unable to connect to Jira - please check your connection',
            'ValidationError': 'Invalid input provided',
            'ValueError': 'Invalid value provided'
        }

        return error_mappings.get(error_name, str(error))

    @staticmethod
    def technical_error_mapper(error: Exception) -> str:
        """Map errors to technical messages (for debugging)."""
        return f"{error.__class__.__name__}: {str(error)}"
