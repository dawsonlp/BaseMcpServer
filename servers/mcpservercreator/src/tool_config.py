"""
Tool configuration for the MCP Server Creator.

This module defines the configuration for all MCP tools that will be bulk registered
with the mcp-commons system, eliminating the need for individual @srv.tool() decorators.
"""

from typing import Dict, Any
from server import MCPServerCreatorImplementation


# Create implementation instance for tool functions
_implementation = MCPServerCreatorImplementation()


# Tool configuration - single source of truth for all MCP Server Creator tools
MCPSERVERCREATOR_TOOLS: Dict[str, Dict[str, Any]] = {
    'help': {
        'function': _implementation.help,
        'description': 'Get detailed help and security information about the MCP Server Creator.'
    },
    
    'create_mcp_server': {
        'function': _implementation.create_mcp_server,
        'description': 'Create and install a new MCP server from a Python code snippet.'
    },
    
    'list_installed_servers': {
        'function': _implementation.list_installed_servers,
        'description': 'List all installed MCP servers.'
    }
}


def get_tool_count() -> int:
    """Get the total number of configured tools."""
    return len(MCPSERVERCREATOR_TOOLS)


def get_tool_names() -> list[str]:
    """Get list of all tool names."""
    return list(MCPSERVERCREATOR_TOOLS.keys())


def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool configuration dictionary

    Raises:
        KeyError: If tool name not found
    """
    if tool_name not in MCPSERVERCREATOR_TOOLS:
        raise KeyError(f"Tool '{tool_name}' not found in configuration")
    
    return MCPSERVERCREATOR_TOOLS[tool_name].copy()


def validate_tool_config() -> Dict[str, Any]:
    """
    Validate the tool configuration for completeness and correctness.

    Returns:
        Validation results with any issues found
    """
    issues = []
    warnings = []
    
    required_keys = ['function', 'description']
    
    for tool_name, config in MCPSERVERCREATOR_TOOLS.items():
        # Check required keys
        for key in required_keys:
            if key not in config:
                issues.append(f"Tool '{tool_name}' missing required key: {key}")
        
        # Check function is callable
        if 'function' in config:
            if not callable(config['function']):
                issues.append(f"Tool '{tool_name}' function must be callable")
        
        # Check description is non-empty string
        if 'description' in config:
            if not isinstance(config['description'], str) or not config['description'].strip():
                issues.append(f"Tool '{tool_name}' description must be non-empty string")
    
    return {
        'valid': len(issues) == 0,
        'tool_count': len(MCPSERVERCREATOR_TOOLS),
        'issues': issues,
        'warnings': warnings
    }


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """
    Get the tools configuration for registration.
    
    Returns:
        Dictionary mapping tool names to their configuration
    """
    return MCPSERVERCREATOR_TOOLS


def get_config_stats() -> Dict[str, Any]:
    """
    Get statistics about the tool configuration.

    Returns:
        Configuration statistics
    """
    validation = validate_tool_config()
    
    return {
        'total_tools': len(MCPSERVERCREATOR_TOOLS),
        'validation': validation,
        'description': 'Metadata-driven tool configuration for MCP Server Creator'
    }
