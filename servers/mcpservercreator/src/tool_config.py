"""Tool configuration for the MCP Server Creator.

Registered by ``create_server()`` through ``MCPServer.add_tool()``.
"""

from typing import Any, Dict

from mcp.types import ToolAnnotations

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

for _name, _spec in MCPSERVERCREATOR_TOOLS.items():
    _read_only = _name != "create_mcp_server"
    _spec["title"] = _name.replace("_", " ").title()
    _spec["annotations"] = ToolAnnotations(
        readOnlyHint=_read_only,
        destructiveHint=_name == "create_mcp_server",
        idempotentHint=_read_only,
        openWorldHint=_name == "create_mcp_server",
    )


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    return MCPSERVERCREATOR_TOOLS
