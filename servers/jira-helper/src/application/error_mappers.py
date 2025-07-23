"""
Error mapping utilities for the application layer.

This module provides centralized error mapping from infrastructure errors
to domain errors, ensuring consistent error handling across the application.
"""

import logging
from typing import Any, Type

from domain.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraInstanceNotFound,
    JiraIssueNotFound,
    JiraTimeoutError,
    JiraValidationError,
    JiraWorkflowError,
    InvalidJQLError,
    JQLSecurityError,
)

logger = logging.getLogger(__name__)


class ErrorMapper:
    """Maps infrastructure errors to appropriate domain errors."""

    @staticmethod
    def map_infrastructure_error(error: Exception, context: dict[str, Any] | None = None) -> Exception:
        """
        Map an infrastructure error to the appropriate domain error.
        
        Args:
            error: The original infrastructure error
            context: Additional context about the operation that failed
            
        Returns:
            The mapped domain error
        """
        error_msg = str(error).lower()
        context = context or {}
        
        # Authentication errors
        if any(keyword in error_msg for keyword in ["authentication", "unauthorized", "401", "forbidden", "403"]):
            instance_name = context.get("instance_name", "unknown")
            return JiraAuthenticationError(instance_name, str(error))
        
        # Connection errors
        if any(keyword in error_msg for keyword in ["connection", "network", "timeout", "unreachable"]):
            instance_name = context.get("instance_name", "unknown")
            if "timeout" in error_msg:
                operation = context.get("operation", "unknown")
                timeout_seconds = context.get("timeout_seconds", 30)
                return JiraTimeoutError(operation, instance_name, timeout_seconds)
            else:
                return JiraConnectionError(instance_name, str(error))
        
        # Issue not found errors
        if any(keyword in error_msg for keyword in ["does not exist", "not found", "404"]):
            issue_key = context.get("issue_key")
            instance_name = context.get("instance_name", "unknown")
            if issue_key:
                return JiraIssueNotFound(issue_key, instance_name)
        
        # Instance not found errors
        if "instance" in error_msg and "not found" in error_msg:
            instance_name = context.get("instance_name", "unknown")
            available_instances = context.get("available_instances", [])
            return JiraInstanceNotFound(instance_name, available_instances)
        
        # Validation errors
        if any(keyword in error_msg for keyword in ["validation", "invalid", "required", "missing"]):
            validation_errors = context.get("validation_errors", [str(error)])
            return JiraValidationError(validation_errors)
        
        # Workflow errors
        if any(keyword in error_msg for keyword in ["transition", "workflow", "status"]):
            issue_key = context.get("issue_key", "unknown")
            return JiraWorkflowError(str(error), issue_key)
        
        # JQL errors
        if any(keyword in error_msg for keyword in ["jql", "query", "syntax"]):
            jql = context.get("jql", "unknown")
            if "security" in error_msg or "permission" in error_msg:
                return JQLSecurityError(jql, str(error))
            else:
                return InvalidJQLError(jql, str(error))
        
        # Default: return the original error
        logger.warning(f"Could not map infrastructure error to domain error: {error}")
        return error

    @staticmethod
    def map_validation_errors(validation_errors: list[str], operation: str | None = None) -> JiraValidationError:
        """
        Map a list of validation errors to a JiraValidationError.
        
        Args:
            validation_errors: List of validation error messages
            operation: The operation that failed validation
            
        Returns:
            JiraValidationError with the validation messages
        """
        if operation:
            logger.info(f"Validation failed for operation '{operation}': {validation_errors}")
        
        return JiraValidationError(validation_errors)

    @staticmethod
    def map_http_status_error(status_code: int, response_text: str, context: dict[str, Any] | None = None) -> Exception:
        """
        Map HTTP status codes to appropriate domain errors.
        
        Args:
            status_code: HTTP status code
            response_text: Response body text
            context: Additional context about the request
            
        Returns:
            The mapped domain error
        """
        context = context or {}
        
        if status_code == 401:
            instance_name = context.get("instance_name", "unknown")
            return JiraAuthenticationError(instance_name, f"HTTP 401: {response_text}")
        
        elif status_code == 403:
            instance_name = context.get("instance_name", "unknown")
            return JiraAuthenticationError(instance_name, f"HTTP 403: {response_text}")
        
        elif status_code == 404:
            issue_key = context.get("issue_key")
            instance_name = context.get("instance_name", "unknown")
            if issue_key:
                return JiraIssueNotFound(issue_key, instance_name)
            else:
                return JiraConnectionError(instance_name, f"HTTP 404: {response_text}")
        
        elif status_code == 400:
            validation_errors = [f"Bad Request: {response_text}"]
            return JiraValidationError(validation_errors)
        
        elif status_code >= 500:
            instance_name = context.get("instance_name", "unknown")
            return JiraConnectionError(instance_name, f"HTTP {status_code}: {response_text}")
        
        else:
            # Generic error for other status codes
            instance_name = context.get("instance_name", "unknown")
            return JiraConnectionError(instance_name, f"HTTP {status_code}: {response_text}")


class ErrorContext:
    """Helper class for building error context."""
    
    def __init__(self):
        self._context: dict[str, Any] = {}
    
    def with_instance(self, instance_name: str) -> "ErrorContext":
        """Add instance name to context."""
        self._context["instance_name"] = instance_name
        return self
    
    def with_issue_key(self, issue_key: str) -> "ErrorContext":
        """Add issue key to context."""
        self._context["issue_key"] = issue_key
        return self
    
    def with_operation(self, operation: str) -> "ErrorContext":
        """Add operation name to context."""
        self._context["operation"] = operation
        return self
    
    def with_jql(self, jql: str) -> "ErrorContext":
        """Add JQL query to context."""
        self._context["jql"] = jql
        return self
    
    def with_timeout(self, timeout_seconds: int) -> "ErrorContext":
        """Add timeout information to context."""
        self._context["timeout_seconds"] = timeout_seconds
        return self
    
    def with_validation_errors(self, errors: list[str]) -> "ErrorContext":
        """Add validation errors to context."""
        self._context["validation_errors"] = errors
        return self
    
    def with_available_instances(self, instances: list[str]) -> "ErrorContext":
        """Add available instances to context."""
        self._context["available_instances"] = instances
        return self
    
    def build(self) -> dict[str, Any]:
        """Build the context dictionary."""
        return self._context.copy()


def map_error(error: Exception, context: dict[str, Any] | None = None) -> Exception:
    """
    Convenience function for mapping errors.
    
    Args:
        error: The original error
        context: Additional context
        
    Returns:
        The mapped domain error
    """
    return ErrorMapper.map_infrastructure_error(error, context)


def create_context() -> ErrorContext:
    """
    Create a new error context builder.
    
    Returns:
        ErrorContext builder instance
    """
    return ErrorContext()
