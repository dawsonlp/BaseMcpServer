"""
Main entry point for the DirectlyRunTest MCP server.

This module sets up and runs the MCP server using FastMCP.
"""

import logging
import sys
import argparse
from mcp.server.fastmcp import FastMCP

from config import settings
from server import register_tools_and_resources


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def start():
    """Start the MCP server using FastMCP's built-in functionality."""
    # Parse command-line arguments for stdio support
    parser = argparse.ArgumentParser(description="DirectlyRunTest MCP Server")
    parser.add_argument(
        "--use-stdio",
        action="store_true",
        help="Use stdio transport instead of HTTP+SSE"
    )
    args = parser.parse_args()
    
    # Create the MCP server directly in main.py
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources from server.py
    register_tools_and_resources(mcp_server)
    
    # Configure server settings
    if not args.use_stdio:
        mcp_server.settings.host = settings.host
        mcp_server.settings.port = settings.port
        logger.info(f"Starting {settings.server_name} on {settings.host}:{settings.port}")
        logger.info("Using HTTP+SSE transport")
    else:
        logger.info(f"Starting {settings.server_name} with stdio transport")
    
    mcp_server.settings.debug = True
    mcp_server.settings.log_level = "INFO"
    
    # Run the server with the appropriate transport
    transport = "stdio" if args.use_stdio else "sse"
    mcp_server.run(transport)


def main():
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print("""
DirectlyRunTest MCP Server Usage Guide
=====================================

BASIC USAGE:
-----------
  python main.py sse        # Run as HTTP+SSE server (for network/container use)
  python main.py stdio      # Run as stdio server (for local development)
  python main.py help       # Show this help message
""")
        return
    
    if sys.argv[1] == "sse":
        start_server("sse")
    elif sys.argv[1] == "stdio":
        start_server("stdio")
    else:
        print(f"Unknown transport mode: {sys.argv[1]}")
        print("Use 'sse', 'stdio', or 'help' for usage information.")
        sys.exit(1)


def start_server(transport="sse"):
    """Start the MCP server using the specified transport."""
    # Create the MCP server directly in main.py
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources from server.py
    register_tools_and_resources(mcp_server)
    
    # Configure server settings
    if transport == "sse":
        mcp_server.settings.host = settings.host
        mcp_server.settings.port = settings.port
        logger.info(f"Starting {settings.server_name} on {settings.host}:{settings.port}")
        logger.info("Using HTTP+SSE transport")
    else:  # stdio
        logger.info(f"Starting {settings.server_name} with stdio transport")
    
    mcp_server.settings.debug = True
    mcp_server.settings.log_level = "INFO"
    
    # Run the server with the selected transport
    mcp_server.run(transport)


if __name__ == "__main__":
    main()
