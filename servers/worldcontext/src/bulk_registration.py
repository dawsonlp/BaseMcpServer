"""
Generic Bulk Registration System for MCP Servers

This module provides generic bulk registration of MCP tools from function configuration.
Eliminates the need for @srv.tool() decorators and keeps business logic clean.
"""

import logging
from typing import Dict, Any, List, Tuple
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


class BulkRegistrationError(Exception):
    """Exception raised during bulk tool registration."""
    pass


def bulk_register_tools(srv: FastMCP, tools_config: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    """
    Bulk register MCP tools from configuration.

    This function replaces manual @srv.tool() decorations by automatically
    registering the business logic functions directly.

    Args:
        srv: FastMCP server instance to register tools with
        tools_config: Dictionary mapping tool names to their configuration

    Returns:
        List of tuples (tool_name, description) for registered tools

    Raises:
        BulkRegistrationError: If registration fails for any tool
    """
    logger.info(f"Starting bulk registration of {len(tools_config)} MCP tools...")

    registered_tools = []
    registration_errors = []

    for tool_name, config in tools_config.items():
        try:
            # Get function and metadata
            tool_function = config['function']
            description = config['description']

            # Register the tool directly with FastMCP using add_tool
            srv.add_tool(tool_function, name=tool_name, description=description)
            
            registered_tools.append((tool_name, description))
            logger.debug(f"Successfully registered tool: {tool_name}")

        except Exception as e:
            error_msg = f"Failed to register tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            registration_errors.append(error_msg)

    # Report results
    if registration_errors:
        error_summary = f"Registration failed for {len(registration_errors)} tools: {registration_errors}"
        logger.error(error_summary)
        raise BulkRegistrationError(error_summary)

    logger.info(f"Successfully registered {len(registered_tools)} MCP tools")
    return registered_tools


def log_registration_summary(registered_tools: List[Tuple[str, str]], total_configured: int, server_name: str = "MCP Server"):
    """
    Log a summary of the registration process.

    Args:
        registered_tools: List of successfully registered tool tuples (name, description)
        total_configured: Total number of tools that were configured
        server_name: Name of the server for logging
    """
    logger.info(f"=== {server_name} Tool Registration Summary ===")
    logger.info(f"Tools registered: {len(registered_tools)}/{total_configured}")
    logger.info(f"Success rate: {len(registered_tools) / total_configured:.1%}" if total_configured else "N/A")

    logger.info("Registered tools:")
    for tool_name, description in registered_tools:
        logger.info(f"  ✓ {tool_name}: {description}")

    logger.info(f"Lines of @srv.tool() decorators eliminated: {len(registered_tools) * 4}")
    logger.info("=== Registration Complete ===")
