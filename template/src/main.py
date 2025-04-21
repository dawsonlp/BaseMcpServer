"""
Main entry point for the MCP server.

This module sets up and runs the MCP server using FastMCP with HTTP+SSE transport.
"""

import logging
import sys

from .config import settings
from .server import create_mcp_server


# Configure logging - Customize the format and level as needed
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def start():
    """
    Start the MCP server using FastMCP's built-in HTTP+SSE transport.
    
    This function initializes the server, applies configuration settings,
    and starts the server with SSE transport.
    """
    logger.info(f"Starting MCP server on {settings.host}:{settings.port}")
    
    # Create the MCP server instance
    mcp_server = create_mcp_server()
    
    # Configure server settings from the settings module
    mcp_server.settings.host = settings.host
    mcp_server.settings.port = settings.port
    
    # Debug mode helpful during development, disable in production
    mcp_server.settings.debug = True
    
    # Configure logging level
    mcp_server.settings.log_level = "INFO"
    
    # Run the server with HTTP+SSE transport
    # SSE (Server-Sent Events) is the recommended transport for MCP
    mcp_server.run("sse")


# Alternative approach: Create an ASGI application for use with external ASGI servers
def create_app():
    """
    Create an ASGI application for use with an external ASGI server (e.g., uvicorn, hypercorn).
    
    Returns:
        An ASGI application instance
    
    Example use with uvicorn:
        uvicorn src.main:create_app --host 0.0.0.0 --port 7501
    """
    # Create the MCP server
    mcp_server = create_mcp_server()
    
    # Configure server settings
    mcp_server.settings.debug = True
    
    # Return the ASGI app instance
    return mcp_server.sse_app()


# This block is executed when the script is run directly
if __name__ == "__main__":
    start()
