"""
Main entry point for the WorldContext MCP Server.

Consolidated to use mcp-commons utilities for standardized server startup.
"""

import sys
from mcp_commons import run_mcp_server, create_mcp_app, print_mcp_help

from config import config
from tool_config import get_tools_config


def main() -> None:
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_mcp_help("WorldContext", "- Context Provider")
        return
    
    # Get config values
    server_name = config.get("server", "name", default="worldcontext")
    host = config.get("server", "host", default="localhost")
    port = config.get("server", "port", default=7501)
    
    if sys.argv[1] == "sse":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="sse",
            host=host,
            port=port
        )
    elif sys.argv[1] == "stdio":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="stdio"
        )
    else:
        print(f"Unknown transport mode: {sys.argv[1]}")
        print("Use 'sse', 'stdio', or 'help' for usage information.")
        sys.exit(1)


def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    server_name = config.get("server", "name", default="worldcontext")
    
    return create_mcp_app(
        server_name=server_name,
        tools_config=get_tools_config()
    )


if __name__ == "__main__":
    main()
