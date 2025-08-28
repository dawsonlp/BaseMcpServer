"""
Application layer now uses mcp-commons for standardized infrastructure.

This module provides application-specific patterns while leveraging
the shared mcp-commons library for core use case infrastructure.
"""

import logging
from collections.abc import Callable
from typing import Any

from mcp_commons import UseCaseResult, BaseUseCase as McpBaseUseCase
from domain.results import ValidationResult
from application.error_mappers import ErrorMapper, create_context

logger = logging.getLogger(__name__)

# Import UseCaseResult from mcp-commons for compatibility
# This allows existing code to continue working
UseCaseResult = UseCaseResult


class BaseUseCase(McpBaseUseCase):
    """Application base use case extending mcp-commons BaseUseCase."""

    def __init__(self, **dependencies):
        """Initialize use case with dependencies."""
        super().__init__(**dependencies)
        self._logger = logging.getLogger(self.__class__.__name__)

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
        """Validate that required parameters are provided using universal validator."""
        from application.validation import validate
        
        # Extract parameter names as required fields
        required_fields = list(params.keys())
        
        # Use universal validator
        validate(required=required_fields, **params)

    def _build_context(self, **kwargs) -> dict[str, Any]:
        """Build context dictionary for result details."""
        return {k: v for k, v in kwargs.items() if v is not None}

    def _validate_with_validator(self, validator: Callable, data: Any, operation: str | None = None) -> ValidationResult:
        """
        Validate data using a validator function.
        
        Args:
            validator: Validator function to use
            data: Data to validate
            operation: Operation name for context
            
        Returns:
            ValidationResult with validation outcome
        """
        try:
            return validator(data)
        except Exception as e:
            self._logger.error(f"Validation failed for {operation or 'operation'}: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )

    def _map_infrastructure_error(self, error: Exception, **context) -> Exception:
        """
        Map infrastructure error to domain error using error mapper.
        
        Args:
            error: Original infrastructure error
            **context: Additional context for error mapping
            
        Returns:
            Mapped domain error
        """
        error_context = create_context()
        
        # Add common context
        for key, value in context.items():
            if key == "instance_name":
                error_context.with_instance(value)
            elif key == "issue_key":
                error_context.with_issue_key(value)
            elif key == "operation":
                error_context.with_operation(value)
            elif key == "jql":
                error_context.with_jql(value)
            elif key == "timeout_seconds":
                error_context.with_timeout(value)
        
        return ErrorMapper.map_infrastructure_error(error, error_context.build())


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
            error_mapper=lambda e: str(self._map_infrastructure_error(e, **context)),
            **context
        )

    async def execute_with_validation(
        self,
        command_operation: Callable,
        validator: Callable,
        data: Any,
        success_mapper: Callable | None = None,
        **context
    ) -> UseCaseResult[Any]:
        """
        Execute command with integrated validation using application validators.
        
        Args:
            command_operation: The command to execute
            validator: Validator function from application layer
            data: Data to validate
            success_mapper: Optional success result mapper
            **context: Additional context for error mapping
            
        Returns:
            UseCaseResult with validation and error mapping
        """
        # Validate input data
        operation_name = context.get("operation", "command")
        validation_result = self._validate_with_validator(validator, data, operation_name)
        
        if not validation_result.is_valid:
            self._logger.warning(f"Validation failed for {operation_name}: {validation_result.errors}")
            
            # Safely handle errors - ensure it's always iterable
            if hasattr(validation_result, 'errors') and validation_result.errors:
                if isinstance(validation_result.errors, (list, tuple)):
                    error_message = f"Validation failed: {'; '.join(str(e) for e in validation_result.errors)}"
                else:
                    error_message = f"Validation failed: {str(validation_result.errors)}"
            else:
                error_message = "Validation failed: Unknown validation error"
            
            return UseCaseResult(
                success=False,
                error=error_message,
                details=context
            )
        
        # Execute command with error mapping
        return await self.execute_with_result(
            command_operation,
            success_mapper=success_mapper,
            error_mapper=lambda e: str(self._map_infrastructure_error(e, **context)),
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
