"""Tool configuration for the MCP Server Creator.

Bulk-registered with mcp-commons; no per-tool @srv.tool() decorator needed.
"""

from typing import Any, Dict

from server import MCPServerCreatorImplementation


_implementation = MCPServerCreatorImplementation()


# Single source of truth for all MCP Server Creator tools.
MCPSERVERCREATOR_TOOLS: Dict[str, Dict[str, Any]] = {
    "help": {
        "function": _implementation.help,
        "description": "Get detailed help and security information about the MCP Server Creator.",
    },
    "create_mcp_server": {
        "function": _implementation.create_mcp_server,
        "description": "Create and install a new MCP server from a Python code snippet.",
    },
    "list_installed_servers": {
        "function": _implementation.list_installed_servers,
        "description": "List all installed MCP servers.",
    },
}


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    return MCPSERVERCREATOR_TOOLS
