"""
Base adapter class to eliminate infrastructure boilerplate.
"""

from typing import Optional, Callable, Any, Dict
import logging
from abc import ABC

from domain.ports import JiraClientFactory, ConfigurationProvider
from domain.exceptions import (
    JiraConnectionError, JiraAuthenticationError, JiraIssueNotFound,
    JiraTimeoutError, JiraPermissionError
)


class BaseJiraAdapter(ABC):
    """Base class for all Jira infrastructure adapters."""
    
    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def _execute_jira_operation(
        self, 
        operation_name: str, 
        operation: Callable,
        instance_name: Optional[str] = None,
        error_mappings: Dict[str, Exception] = None
    ) -> Any:
        """Execute Jira operation with common error handling."""
        try:
            client = self._client_factory.create_client(instance_name)
            result = await operation(client)
            self._logger.debug(f"{operation_name} completed successfully")
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Apply custom error mappings
            if error_mappings:
                for pattern, exception_class in error_mappings.items():
                    if pattern in error_msg:
                        raise exception_class
            
            # Common error patterns
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound("unknown", instance_name or "default")
            elif "permission" in error_msg or "forbidden" in error_msg:
                raise JiraPermissionError(operation_name, "resource", instance_name or "default")
            elif "timeout" in error_msg:
                raise JiraTimeoutError(operation_name, instance_name or "default", 30)
            elif "authentication" in error_msg or "unauthorized" in error_msg:
                raise JiraAuthenticationError(instance_name or "default")
            elif "connection" in error_msg:
                raise JiraConnectionError(instance_name or "default")
            
            self._logger.error(f"{operation_name} failed: {str(e)}")
            raise
    
    def _convert_to_domain(self, jira_object: Any, converter_func: Callable) -> Any:
        """Generic conversion from Jira objects to domain objects."""
        return converter_func(jira_object, self._config_provider)
    
    def _build_error_mappings(self, custom_mappings: Dict[str, Exception] = None) -> Dict[str, Exception]:
        """Build error mappings with defaults and custom overrides."""
        default_mappings = {
            "issue does not exist": JiraIssueNotFound("unknown", "default"),
            "project does not exist": JiraIssueNotFound("unknown", "default"),
            "access denied": JiraPermissionError("operation", "resource", "default"),
            "forbidden": JiraPermissionError("operation", "resource", "default"),
            "timeout": JiraTimeoutError("operation", "default", 30),
            "connection refused": JiraConnectionError("default"),
            "unauthorized": JiraAuthenticationError("default")
        }
        
        if custom_mappings:
            default_mappings.update(custom_mappings)
        
        return default_mappings
    
    async def _execute_with_retry(
        self,
        operation_name: str,
        operation: Callable,
        max_retries: int = 3,
        instance_name: Optional[str] = None
    ) -> Any:
        """Execute operation with retry logic for transient failures."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await self._execute_jira_operation(operation_name, operation, instance_name)
            except (JiraConnectionError, JiraTimeoutError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    self._logger.warning(f"{operation_name} attempt {attempt + 1} failed, retrying...")
                    continue
                else:
                    self._logger.error(f"{operation_name} failed after {max_retries} attempts")
                    raise
            except Exception as e:
                # Don't retry for non-transient errors
                raise
        
        # This should never be reached, but just in case
        raise last_exception
