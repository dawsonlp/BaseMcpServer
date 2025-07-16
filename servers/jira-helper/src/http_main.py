"""
HTTP entry point for the Jira Helper MCP server.

This module provides the HTTP server entry point for running the Jira Helper
as a streamable HTTP service, enabling Docker deployment and multi-server integration.
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from adapters.http_adapter import run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Jira Helper HTTP server."""
    try:
        logger.info("Starting Jira Helper HTTP server with hexagonal architecture...")
        run_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise


if __name__ == "__main__":
    main()
