"""
Base service class to eliminate common service boilerplate.
"""

from abc import ABC

from .base import FieldValidator
from .exceptions import JiraInstanceNotFound
from .ports import ConfigurationProvider, Logger


class BaseJiraService(ABC):
    """Base class for all Jira services with common functionality."""

    def __init__(
        self,
        config_provider: ConfigurationProvider,
        logger: Logger,
        **kwargs
    ):
        self._config_provider = config_provider
        self._logger = logger

        # Store additional dependencies
        for key, value in kwargs.items():
            setattr(self, f"_{key}", value)

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use - SINGLE IMPLEMENTATION."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance

    def _validate_issue_key(self, issue_key: str) -> None:
        """Validate issue key - SINGLE IMPLEMENTATION."""
        FieldValidator.validate_issue_key(issue_key)

    def _validate_project_key(self, project_key: str) -> None:
        """Validate project key - SINGLE IMPLEMENTATION."""
        FieldValidator.validate_project_key(project_key)

    def _validate_max_results(self, max_results: int) -> None:
        """Validate max results - SINGLE IMPLEMENTATION."""
        FieldValidator.validate_max_results(max_results)

    async def _execute_with_logging(
        self,
        operation_name: str,
        operation,
        success_message: str = None,
        error_message: str = None
    ):
        """Execute operation with consistent logging and error handling."""
        try:
            result = await operation()

            if success_message:
                self._logger.info(success_message)
            else:
                self._logger.debug(f"{operation_name} completed successfully")

            return result

        except Exception as e:
            if error_message:
                self._logger.error(f"{error_message}: {str(e)}")
            else:
                self._logger.error(f"{operation_name} failed: {str(e)}")
            raise
