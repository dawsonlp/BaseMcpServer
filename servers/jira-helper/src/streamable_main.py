"""
Streamable HTTP entry point for the Jira Helper MCP server.

This module provides the entry point for the Jira Helper server
using the official MCP streamable HTTP transport.
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from adapters.mcp_adapter import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Jira Helper MCP server with streamable HTTP transport."""
    try:
        logger.info("Starting Jira Helper MCP server with streamable HTTP transport...")
        # Use the official streamable HTTP transport
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise


if __name__ == "__main__":
    main()
