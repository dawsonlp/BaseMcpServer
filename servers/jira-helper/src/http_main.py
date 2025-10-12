"""
HTTP entry point for the Jira Helper MCP server.

This module provides the HTTP server entry point using mcp-commons,
maintaining consistency with the CLI interface through shared service initialization.

Architecture:
    This entry point uses the same hexagonal architecture as main.py,
    with HTTP as the transport port instead of stdio/sse.
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from adapters.http_adapter import run_http_server
from config import settings

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the Jira Helper HTTP server.
    
    Uses mcp-commons unified framework, sharing tool configuration
    and service initialization with CLI for DRY compliance.
    """
    try:
        # Get HTTP configuration
        host = getattr(settings, 'host', '0.0.0.0')
        port = getattr(settings, 'port', 8000)
        
        logger.info("🚀 Starting Jira Helper HTTP server with unified mcp-commons framework")
        logger.info(f"📍 Binding to {host}:{port}")
        
        # Run HTTP server with mcp-commons
        run_http_server(host=host, port=port)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise


if __name__ == "__main__":
    main()
