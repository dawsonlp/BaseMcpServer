"""
MCP Result Adapter

This module provides the core adapter function that converts use case results
to MCP-compatible format. This single function replaces 500+ lines of
boilerplate wrapper functions in mcp_tools.py.
"""

import inspect
import logging
from collections.abc import Callable
from typing import Any

from application.base_use_case import UseCaseResult

logger = logging.getLogger(__name__)


def create_mcp_adapter(use_case_method: Callable) -> Callable:
    """
    Create an MCP-compatible adapter for a use case method.

    This is the ONLY wrapper function needed - it adapts UseCaseResult to MCP format.
    Replaces all individual wrapper functions in mcp_tools.py.

    Args:
        use_case_method: The use case execute method to adapt

    Returns:
        An async function compatible with MCP SDK that returns data directly

    Example:
        >>> use_case = ListProjectsUseCase(project_service)
        >>> adapted_method = create_mcp_adapter(use_case.execute)
        >>> tool = Tool.from_function(adapted_method, name="list_projects")
    """
    # Get the original function signature for MCP SDK
    sig = inspect.signature(use_case_method)

    async def mcp_adapted_method(**kwargs) -> dict[str, Any]:
        """Execute use case and adapt result for MCP."""
        try:
            # Call the original use case method
            result = await use_case_method(**kwargs)

            # Handle UseCaseResult objects
            if isinstance(result, UseCaseResult):
                if result.success:
                    # Return the data directly for successful results
                    return result.data
                else:
                    # Return error in MCP-compatible format
                    return {
                        "success": False,
                        "error": result.error,
                        "details": result.details
                    }
            else:
                # If not UseCaseResult, return as-is (shouldn't happen with current use cases)
                logger.warning(f"Use case method returned non-UseCaseResult: {type(result)}")
                return result

        except Exception as e:
            # Handle any unexpected exceptions
            logger.error(f"Error in MCP adapter for {use_case_method.__name__}: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "details": {"method": use_case_method.__name__, "kwargs": kwargs}
            }

    # Preserve function metadata for MCP SDK
    mcp_adapted_method.__name__ = use_case_method.__name__
    mcp_adapted_method.__doc__ = use_case_method.__doc__
    mcp_adapted_method.__annotations__ = getattr(use_case_method, '__annotations__', {})
    mcp_adapted_method.__signature__ = sig

    return mcp_adapted_method


def validate_use_case_result(result: Any) -> bool:
    """
    Validate that a result is a proper UseCaseResult.

    Args:
        result: The result to validate

    Returns:
        True if result is a valid UseCaseResult, False otherwise
    """
    if not isinstance(result, UseCaseResult):
        return False

    # Check required attributes
    required_attrs = ['success', 'data', 'error', 'details']
    for attr in required_attrs:
        if not hasattr(result, attr):
            return False

    # Validate types
    if not isinstance(result.success, bool):
        return False

    if result.error is not None and not isinstance(result.error, str):
        return False

    if not isinstance(result.details, dict):
        return False

    return True


def get_adapter_stats() -> dict[str, Any]:
    """
    Get statistics about the adapter usage.

    Returns:
        Dictionary with adapter statistics
    """
    return {
        "adapter_version": "1.0.0",
        "replaces_lines": 500,  # Lines eliminated from mcp_tools.py
        "description": "Single adapter function replacing all MCP wrapper boilerplate"
    }
