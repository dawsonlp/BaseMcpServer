"""
Main entry point for the MCP Server Creator.
"""

import sys
import logging
from mcp.server.fastmcp import FastMCP

from config import settings
from server import mcp  # Import the already initialized MCP server from server.py

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def print_help():
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


def start_server(transport="sse"):
    """Start the MCP server using the specified transport."""
    # Log important configuration
    logger.info(f"Starting {settings.server_name}")
    
    # Configure server settings
    if transport == "sse":
        mcp.settings.host = settings.host
        mcp.settings.port = settings.port
        logger.info(f"Using HTTP+SSE transport on {settings.host}:{settings.port}")
    else:  # stdio
        logger.info(f"Using stdio transport")
    
    mcp.settings.debug = True
    mcp.settings.log_level = "INFO"
    
    # Run the server with the selected transport
    mcp.run(transport)


def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    # Configure server settings
    mcp.settings.debug = True
    
    # Return the ASGI app instance
    return mcp.sse_app()


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
