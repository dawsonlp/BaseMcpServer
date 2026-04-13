"""
Main entry point for the WorldContext MCP Server.

Uses mcp-commons utilities for standardized server startup.
"""

import logging
import sys

from mcp_commons import create_mcp_app, print_mcp_help, run_mcp_server

from config import config
from tool_config import get_tools_config

# Single logging configuration for the entire server — stderr only
# to avoid interfering with stdio JSON-RPC transport.
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)


def main() -> None:
    """Process command-line arguments and start the server."""
    if len(sys.argv) <= 1 or sys.argv[1] in ("help", "--help", "-h"):
        print_mcp_help("WorldContext", "- Context Provider")
        return

    server_name = config.get("server", "name", default="worldcontext")
    host = config.get("server", "host", default="localhost")
    port = config.get("server", "port", default=7501)

    transport = sys.argv[1]

    if transport == "sse":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="sse",
            host=host,
            port=port,
        )
    elif transport == "stdio":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="stdio",
        )
    else:
        print(f"Unknown transport mode: {transport}", file=sys.stderr)
        print("Use 'sse', 'stdio', or 'help' for usage information.", file=sys.stderr)
        sys.exit(1)


def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    server_name = config.get("server", "name", default="worldcontext")
    return create_mcp_app(server_name=server_name, tools_config=get_tools_config())


if __name__ == "__main__":
    main()