"""
Main entry point for the Example MCP server.

This module sets up and runs the MCP server using FastMCP.
"""

import logging
import sys

from .config import settings
from .server import create_mcp_server


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def start():
    """Start the MCP server using FastMCP's built-in functionality."""
    logger.info(f"Starting Example MCP server on {settings.host}:{settings.port}")
    
    # Create the MCP server
    mcp_server = create_mcp_server()
    
    # Configure server settings
    mcp_server.settings.host = settings.host
    mcp_server.settings.port = settings.port
    mcp_server.settings.debug = True
    mcp_server.settings.log_level = "INFO"
    
    # Run the server with SSE transport
    mcp_server.run("sse")


# Alternative approach using the FastMCP ASGI application
def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    # Create the MCP server
    mcp_server = create_mcp_server()
    
    # Configure server settings
    mcp_server.settings.debug = True
    
    # Return the ASGI app instance
    return mcp_server.sse_app()


if __name__ == "__main__":
    start()
