"""
HTTP adapter for the Jira Helper MCP server.

This module provides HTTP transport for the MCP server using mcp-commons,
maintaining hexagonal architecture and DRY principles by sharing the same
tool configuration and service initialization as the CLI interface.

Architecture:
    Port (HTTP) → mcp-commons.create_mcp_app() → tool_config.get_tools_config() → Domain Services
    
This ensures both CLI and HTTP use identical service initialization,
eliminating duplication while maintaining proper separation of concerns.
"""

import logging
import uvicorn
from mcp_commons import create_mcp_app

from config import settings
from tool_config import get_tools_config

logger = logging.getLogger(__name__)


def create_http_app():
    """
    Create an ASGI application for HTTP transport.
    
    Uses the same tool configuration and service initialization as CLI,
    ensuring consistency across all transport mechanisms (hexagonal architecture).
    
    Returns:
        ASGI application instance configured with all 33 Jira/Confluence tools
    """
    server_name = getattr(settings, 'server_name', 'jira-helper')
    
    logger.info(f"Creating MCP HTTP server '{server_name}' with mcp-commons")
    logger.info("Using shared tool_config for service initialization (DRY)")
    
    # Create ASGI app with same tools_config as CLI
    # This is the key to DRY - both transports use get_tools_config()
    app = create_mcp_app(
        server_name=server_name,
        tools_config=get_tools_config()
    )
    
    logger.info("HTTP server application created successfully")
    return app


def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the HTTP server using uvicorn.
    
    Args:
        host: Host to bind to (default: 0.0.0.0 for Docker compatibility)
        port: Port to listen on (default: 8000)
    """
    # Configure logging for HTTP server
    log_file = getattr(settings, 'log_file', '/tmp/jira_helper_debug.log')
    log_level = getattr(settings, 'log_level', 'INFO')
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler()  # OK to use stdout with HTTP transport
        ]
    )
    
    logger.info(f"🌐 Starting Jira Helper HTTP server on {host}:{port}")
    logger.info(f"📁 Debug log file: {log_file}")
    logger.info("🔧 Using mcp-commons unified framework")
    logger.info("♻️  Sharing service initialization with CLI (DRY architecture)")
    
    # Create the ASGI app
    app = create_http_app()
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level.lower()
    )


# Export the app for external ASGI servers (e.g., gunicorn, hypercorn)
app = create_http_app()


if __name__ == "__main__":
    # Get config values
    host = getattr(settings, 'host', '0.0.0.0')
    port = getattr(settings, 'port', 8000)
    
    run_http_server(host=host, port=port)
