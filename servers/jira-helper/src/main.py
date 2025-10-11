"""
Main entry point for the Jira Helper MCP server.

Simplified using mcp-commons while preserving hexagonal architecture.
Migration from FastMCP to mcp-commons direct function mapping.
"""

import sys
import logging
from mcp_commons import run_mcp_server, create_mcp_app, print_mcp_help

from config import settings
from tool_config import get_tools_config

# Configure logging for file output (avoid stdout corruption with stdio transport)
log_file = getattr(settings, 'log_file', '/tmp/jira_helper_debug.log')
log_level = getattr(settings, 'log_level', 'INFO')

logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a')
        # Note: No stdout handler when using stdio transport to avoid corrupting MCP protocol
    ]
)


def main() -> None:
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_mcp_help("Jira Helper", "- Enterprise Jira Integration with Hexagonal Architecture")
        return
    
    # Get config values
    server_name = getattr(settings, 'server_name', 'jira-helper')
    host = getattr(settings, 'host', 'localhost')
    port = getattr(settings, 'port', 7502)
    
    logger = logging.getLogger(__name__)
    
    # Handle both direct transport args and --transport flag format
    transport = None
    if sys.argv[1] == "--transport" and len(sys.argv) > 2:
        transport = sys.argv[2]
    else:
        transport = sys.argv[1]
    
    if transport == "sse":
        logger.info(f"🌐 Starting Jira Helper SSE server on {host}:{port}")
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="sse",
            host=host,
            port=port
        )
    elif transport == "stdio":
        logger.info("🚀 Starting Jira Helper MCP server with stdio transport")
        logger.info(f"📁 Debug log file: {log_file}")
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="stdio"
        )
    else:
        print(f"Unknown transport mode: {transport}", file=sys.stderr)
        print("Use 'sse', 'stdio', or 'help' for usage information.", file=sys.stderr)
        sys.exit(1)


def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    server_name = getattr(settings, 'server_name', 'jira-helper')
    
    return create_mcp_app(
        server_name=server_name,
        tools_config=get_tools_config()
    )


if __name__ == "__main__":
    main()
