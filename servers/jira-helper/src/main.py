"""
Main entry point for the Jira Helper MCP server.

Supports stdio, sse, and streamable-http transports via mcp-commons.
"""

import sys
import logging

from mcp_commons import run_mcp_server, create_mcp_app, print_mcp_help

from config import settings
from tool_config import get_tools_config


# Configure logging to file (avoid stdout corruption with stdio transport)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(settings.log_file, mode="a")],
)


def main() -> None:
    """Parse CLI arguments and start the server."""
    if len(sys.argv) <= 1 or sys.argv[1] in ("help", "--help", "-h"):
        print_mcp_help("Jira Helper", "- Jira & Confluence Integration MCP Server")
        return

    # Parse transport argument
    if sys.argv[1] == "--transport" and len(sys.argv) > 2:
        transport = sys.argv[2]
    else:
        transport = sys.argv[1]

    logger = logging.getLogger(__name__)

    if transport in ("stdio", "sse", "streamable-http"):
        logger.info(f"Starting Jira Helper with {transport} transport")
        kwargs = {
            "server_name": settings.server_name,
            "tools_config": get_tools_config(),
            "transport": transport,
        }
        if transport != "stdio":
            kwargs["host"] = settings.host
            kwargs["port"] = settings.port
        run_mcp_server(**kwargs)
    else:
        print(f"Unknown transport: {transport}", file=sys.stderr)
        print("Use 'stdio', 'sse', 'streamable-http', or 'help'.", file=sys.stderr)
        sys.exit(1)


def create_app():
    """Create an ASGI application for external ASGI servers."""
    return create_mcp_app(
        server_name=settings.server_name,
        tools_config=get_tools_config(),
    )


if __name__ == "__main__":
    main()