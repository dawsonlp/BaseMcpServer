"""
Main entry point for the Jira Helper MCP server.

Consolidated to use mcp-commons utilities while maintaining hexagonal architecture.
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from adapters.mcp_adapter import mcp

# Configure logging for file output (avoid stdout corruption with stdio transport)
log_file = "/tmp/jira_helper_debug.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a')
        # Note: No stdout handler when using stdio transport to avoid corrupting MCP protocol
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Jira Helper MCP server."""
    # Get transport from command line argument
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    
    if transport in ["help", "--help", "-h"]:
        print("Jira Helper MCP Server")
        print("Usage: python main.py [stdio|sse]")
        print("  stdio: Use stdio transport (default)")
        print("  sse:   Use HTTP+SSE transport")
        return
    
    try:
        logger.info(f"Starting Jira Helper MCP server with transport: {transport}")
        # The mcp object will be configured to use the specified transport
        mcp.run(transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    main()
