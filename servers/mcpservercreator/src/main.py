"""
Main entry point for the MCP Server Creator.
"""

import sys
import logging
from typing import Any
from mcp.server.fastmcp import FastMCP

from config import settings
from server import register_tools_and_resources  # Import the function that registers tools

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def print_help() -> None:
    """Print helpful information about using the MCP server."""
    help_text = """
MCP Server Creator Usage Guide
==========================

BASIC USAGE:
-----------
  python main.py sse        # Run as HTTP+SSE server (for network/container use)
  python main.py stdio      # Run as stdio server (for local development)
  python main.py help       # Show this help message
"""
    print(help_text)


def start_server(transport: str = "sse") -> None:
    """Start the MCP server using the specified transport."""
    # Create the MCP server
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources
    register_tools_and_resources(mcp_server)
    
    # Log important configuration
    logger.info(f"Starting {settings.server_name}")
    
    # Configure server settings
    if transport == "sse":
        mcp_server.settings.host = settings.host
        mcp_server.settings.port = settings.port
        logger.info(f"Using HTTP+SSE transport on {settings.host}:{settings.port}")
    else:  # stdio
        logger.info(f"Using stdio transport")
    
    mcp_server.settings.debug = True
    mcp_server.settings.log_level = "INFO"
    
    # Run the server with the selected transport
    mcp_server.run(transport)


def create_app() -> Any:
    """Create an ASGI application for use with an external ASGI server."""
    # Create the MCP server
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources
    register_tools_and_resources(mcp_server)
    
    # Configure server settings
    mcp_server.settings.debug = True
    
    # Return the ASGI app instance
    return mcp_server.sse_app()


def main():
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_help()
        return
    
    if sys.argv[1] == "sse":
        start_server("sse")
    elif sys.argv[1] == "stdio":
        start_server("stdio")
    else:
        print(f"Unknown transport mode: {sys.argv[1]}")
        print("Use 'sse', 'stdio', or 'help' for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
