"""
Main entry point for the MCP Server Creator.
"""

import sys
import logging
from mcp.server.fastmcp import run

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Determine the transport to use
    transport = "sse" if len(sys.argv) > 1 and sys.argv[1] == "sse" else "stdio"
    
    # Log startup information
    logger.info(f"Starting mcpservercreator-server with {transport} transport")
    
    # Run the server with the specified transport
    run(transport)
