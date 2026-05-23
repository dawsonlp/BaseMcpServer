"""Tool implementations and the registration dict for the template MCP server.

Replace the `echo` example with your real tools. Add entries to the
`TEMPLATE_TOOLS` dict at the bottom of this file -- mcp-commons will
bulk-register all of them at startup. There is no need for per-tool
`@srv.tool()` decorators; the dict is the single source of truth.
"""

from typing import Any, Dict

from config import config


# -----------------------------------------------------------------------------
# Tool implementations
# -----------------------------------------------------------------------------

def echo(message: str) -> Dict[str, Any]:
    """Return the message verbatim, prefixed with the server's name from config.

    Replace this with your real tool. A tool is just a function that takes
    JSON-serializable arguments and returns a JSON-serializable dict.

    Args:
        message: The text to echo back.

    Returns:
        A dict with the configured server name and the original message.
    """
    return {
        "server": config.get("server", "name", default="template"),
        "message": message,
    }


# -----------------------------------------------------------------------------
# Tool registration -- single source of truth
# -----------------------------------------------------------------------------

TEMPLATE_TOOLS: Dict[str, Dict[str, Any]] = {
    "echo": {
        "function": echo,
        "description": "Echo a message back with the server name attached. Replace with your real tools.",
    },
}


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """Return the tools configuration for bulk registration."""
    return TEMPLATE_TOOLS
