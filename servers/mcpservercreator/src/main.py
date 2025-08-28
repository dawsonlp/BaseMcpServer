"""
Main entry point for the MCP Server Creator.

This module uses mcp-commons for streamlined server creation and bulk tool registration,
eliminating boilerplate code and providing a clean, maintainable server implementation.
"""

import sys
from mcp_commons import run_mcp_server, create_mcp_app, print_mcp_help
from tool_config import get_tools_config

def main():
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_mcp_help("MCP Server Creator", "- Create and manage MCP servers")
        return
    
    # Server configuration
    server_name = "mcpservercreator"
    host = "localhost"
    port = 7502  # Different port from worldcontext
    
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
    return create_mcp_app(
        server_name="mcpservercreator",
        tools_config=get_tools_config()
    )

if __name__ == "__main__":
    main()
