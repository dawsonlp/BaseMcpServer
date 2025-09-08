"""
Main entry point for the Jira Helper MCP server.

Consolidated to use mcp-commons utilities while maintaining hexagonal architecture.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from config import settings
from adapters.mcp_adapter import mcp

# Configure logging for file output (avoid stdout corruption with stdio transport)
# Use configurable log file path from config.yaml
log_file = settings.log_file
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a')
        # Note: No stdout handler when using stdio transport to avoid corrupting MCP protocol
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Jira Helper MCP server."""
    parser = argparse.ArgumentParser(description="Jira Helper MCP Server")
    parser.add_argument("transport", nargs="?", default="stdio", 
                       help="Transport type (stdio or sse)")
    parser.add_argument("--transport", dest="transport_flag", 
                       help="Transport type (alternative flag format)")
    
    args = parser.parse_args()
    
    # Use --transport flag value if provided, otherwise use positional argument
    transport = args.transport_flag if args.transport_flag else args.transport
    
    if transport in ["help", "--help", "-h"]:
        parser.print_help()
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
