"""
Generic MCP Server Registration Module

This module provides generic tool registration for MCP servers using bulk registration.
Business logic is kept separate from MCP infrastructure.
"""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from mcp_commons import bulk_register_tools, log_registration_summary

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_tools_and_resources(srv: FastMCP, tools_config: Dict[str, Dict[str, Any]], server_name: str = "MCP Server") -> None:
    """
    Register tools and resources with the provided MCP server instance using bulk registration.
    
    This function uses bulk registration to automatically register all tools
    from the provided configuration. This eliminates the need for
    manual @srv.tool() decorations and keeps business logic clean.
    
    Args:
        srv: A FastMCP server instance to register tools and resources with
        tools_config: Dictionary mapping tool names to their configuration
        server_name: Name of the server for logging purposes
    """
    logger.info(f"Starting {server_name} tool registration...")
    
    try:
        # Use bulk registration to register all tools from configuration
        registered_tools = bulk_register_tools(srv, tools_config)
        
        # Log registration summary
        log_registration_summary(registered_tools, len(tools_config), server_name)
        
        logger.info(f"{server_name} tools registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register {server_name} tools: {str(e)}")
        raise
