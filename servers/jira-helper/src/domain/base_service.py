"""
Base service class for all Jira domain services.
Eliminates code duplication and provides common functionality.
"""

import logging
from typing import Any

from .exceptions import JiraInstanceNotFound, JiraValidationError
from .ports import ConfigurationProvider, Logger


class BaseJiraService:
    """Base class for all Jira services with common functionality."""

    def __init__(
        self,
        config_provider: ConfigurationProvider,
        logger: Logger,
        **kwargs
    ):
        """Initialize base service with common dependencies."""
        self._config_provider = config_provider
        self._logger = logger
        
        # Store additional dependencies passed by subclasses
        for key, value in kwargs.items():
            setattr(self, f"_{key}", value)

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """
        Resolve instance name to use.
        
        This method eliminates duplication across 8+ service classes.
        """
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance

    def _validate_issue_key(self, issue_key: str) -> None:
        """
        Validate issue key format.
        
        This method eliminates duplication across multiple service classes.
        """
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

        if "-" not in issue_key:
            raise JiraValidationError([
                "Issue key must contain project key and number (e.g., PROJ-123)"
            ])

    def _validate_non_empty_string(self, value: str, field_name: str) -> None:
        """Validate that a string field is not empty."""
        if not value or not value.strip():
            raise JiraValidationError([f"{field_name} cannot be empty"])

    def _validate_positive_integer(self, value: int, field_name: str) -> None:
        """Validate that an integer field is positive."""
        if value <= 0:
            raise JiraValidationError([f"{field_name} must be greater than 0"])

    def _validate_max_results(self, max_results: int) -> None:
        """Validate max results parameter."""
        if max_results <= 0:
            raise JiraValidationError(["Max results must be greater than 0"])

        if max_results > 1000:
            raise JiraValidationError(["Max results cannot exceed 1000"])

    def _log_operation_start(self, operation: str, **context) -> None:
        """Log the start of an operation with context."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self._logger.info(f"Starting {operation}: {context_str}")

    def _log_operation_success(self, operation: str, **context) -> None:
        """Log successful completion of an operation."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self._logger.info(f"Completed {operation}: {context_str}")

    def _log_operation_error(self, operation: str, error: Exception, **context) -> None:
        """Log operation failure with context."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self._logger.error(f"Failed {operation}: {context_str} - {str(error)}")
