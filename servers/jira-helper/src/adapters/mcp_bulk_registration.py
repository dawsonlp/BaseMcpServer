"""
Tool Configuration and Registration

This module handles tool configuration processing and dependency injection
for both Jira and Confluence tools.
Uses mcp-commons for the actual bulk registration to eliminate code duplication.
"""

import logging
from collections.abc import Callable
from typing import Any

from mcp_commons import create_mcp_adapter
from mcp_commons.bulk_registration import bulk_register_tuple_format, BulkRegistrationError
from adapters.mcp_tool_config import JIRA_TOOLS, CONFLUENCE_TOOLS, validate_tool_config

logger = logging.getLogger(__name__)


def prepare_jira_tools_for_registration(context) -> list[tuple[Callable, str, str]]:
    """
    Prepare Jira tools from metadata configuration for bulk registration.

    Handles Jira-specific use case instantiation and dependency injection,
    then returns tuples that can be registered via mcp-commons.

    Args:
        context: JiraHelperContext containing all initialized services

    Returns:
        List of tuples (function, name, description) for mcp-commons registration

    Raises:
        BulkRegistrationError: If preparation fails for any tool
    """
    logger.info("Preparing Jira MCP tools for bulk registration...")
    return _prepare_tools_from_config(JIRA_TOOLS, context, "Jira")


def prepare_confluence_tools_for_registration(context) -> list[tuple[Callable, str, str]]:
    """
    Prepare Confluence tools from metadata configuration for bulk registration.

    Handles Confluence-specific use case instantiation and dependency injection,
    then returns tuples that can be registered via mcp-commons.

    Args:
        context: JiraHelperContext containing all initialized services

    Returns:
        List of tuples (function, name, description) for mcp-commons registration

    Raises:
        BulkRegistrationError: If preparation fails for any tool
    """
    logger.info("Preparing Confluence MCP tools for bulk registration...")
    return _prepare_tools_from_config(CONFLUENCE_TOOLS, context, "Confluence")


def _prepare_tools_from_config(
    tools_config: dict[str, dict[str, Any]], 
    context, 
    tool_type: str
) -> list[tuple[Callable, str, str]]:
    """
    Generic function to prepare tools from a configuration dict.

    Args:
        tools_config: Dictionary of tool configurations
        context: JiraHelperContext containing all initialized services
        tool_type: Type of tools being prepared (for logging)

    Returns:
        List of tuples (function, name, description) for mcp-commons registration

    Raises:
        BulkRegistrationError: If preparation fails for any tool
    """
    logger.info(f"Preparing {len(tools_config)} {tool_type} tools from configuration...")

    tools = []
    preparation_errors = []

    for tool_name, config in tools_config.items():
        try:
            tool = _prepare_single_tool(tool_name, config, context)
            tools.append(tool)
            logger.debug(f"Successfully prepared tool: {tool_name}")

        except Exception as e:
            error_msg = f"Failed to prepare tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            preparation_errors.append(error_msg)

    # Report results
    if preparation_errors:
        error_summary = f"Preparation failed for {len(preparation_errors)} {tool_type} tools: {preparation_errors}"
        logger.error(error_summary)
        raise BulkRegistrationError(error_summary)

    logger.info(f"Successfully prepared {len(tools)} {tool_type} MCP tools for registration")
    return tools


def _prepare_single_tool(tool_name: str, config: dict[str, Any], context) -> tuple[Callable, str, str]:
    """
    Prepare a single MCP tool from configuration.

    Args:
        tool_name: Name of the tool
        config: Tool configuration dictionary  
        context: JiraHelperContext containing services

    Returns:
        Tuple of (function, name, description) for registration

    Raises:
        BulkRegistrationError: If preparation fails
    """
    try:
        # Get use case class and dependencies
        use_case_class = config['use_case_class']
        dependencies = config['dependencies']
        description = config['description']

        # Resolve dependencies from context
        resolved_deps = {}
        for dep_name in dependencies:
            if not hasattr(context, dep_name):
                raise BulkRegistrationError(f"Missing dependency '{dep_name}' in context for tool '{tool_name}'")
            resolved_deps[dep_name] = getattr(context, dep_name)

        # Create use case instance with dependencies
        use_case = use_case_class(**resolved_deps)

        # Create MCP-adapted method
        adapted_method = create_mcp_adapter(use_case.execute)

        # Return function, name, description tuple for mcp-commons registration
        return (adapted_method, tool_name, description)

    except Exception as e:
        raise BulkRegistrationError(f"Error preparing tool '{tool_name}': {str(e)}") from e


def bulk_register_all_tools(srv, context) -> list[tuple[str, str]]:
    """
    Bulk register both Jira and Confluence tools using mcp-commons infrastructure.

    This function combines tool configuration processing with
    generic mcp-commons bulk registration to eliminate code duplication.

    Args:
        srv: FastMCP server instance to register tools with
        context: JiraHelperContext containing all initialized services

    Returns:
        List of tuples (tool_name, description) for registered tools

    Raises:
        BulkRegistrationError: If registration fails for any tool
    """
    logger.info("Starting MCP tools bulk registration (Jira + Confluence)...")

    # Prepare both Jira and Confluence tools
    jira_tuples = prepare_jira_tools_for_registration(context)
    confluence_tuples = prepare_confluence_tools_for_registration(context)
    
    # Combine all tool tuples
    all_tool_tuples = jira_tuples + confluence_tuples

    # Use mcp-commons for actual registration
    registered_tools = bulk_register_tuple_format(srv, all_tool_tuples)

    logger.info(f"Successfully registered {len(registered_tools)} MCP tools ({len(jira_tuples)} Jira + {len(confluence_tuples)} Confluence) using mcp-commons")
    return registered_tools


# Backwards compatibility alias
def bulk_register_jira_tools(srv, context) -> list[tuple[str, str]]:
    """
    Backwards compatibility wrapper for bulk_register_all_tools.
    
    Deprecated: Use bulk_register_all_tools() instead.
    """
    return bulk_register_all_tools(srv, context)


def validate_context_dependencies(context) -> dict[str, Any]:
    """
    Validate that the context has all required dependencies for tool registration.

    Args:
        context: JiraHelperContext to validate

    Returns:
        Validation results with missing dependencies
    """
    missing_deps = []
    available_deps = []

    # Get all unique dependencies from both Jira and Confluence tool configurations
    all_dependencies = set()
    for config in JIRA_TOOLS.values():
        all_dependencies.update(config.get('dependencies', []))
    for config in CONFLUENCE_TOOLS.values():
        all_dependencies.update(config.get('dependencies', []))

    # Check each dependency
    for dep_name in all_dependencies:
        if hasattr(context, dep_name):
            available_deps.append(dep_name)
        else:
            missing_deps.append(dep_name)

    return {
        'valid': len(missing_deps) == 0,
        'total_dependencies': len(all_dependencies),
        'available_dependencies': available_deps,
        'missing_dependencies': missing_deps
    }
