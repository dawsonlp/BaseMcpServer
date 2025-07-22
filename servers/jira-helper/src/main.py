"""
Main entry point for the Jira Helper MCP server.

This module provides the entry point for the Jira Helper server
using hexagonal architecture with proper separation of concerns.
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from adapters.mcp_adapter import mcp

# Configure logging with explicit file handler and immediate flushing
log_file = "/tmp/jira_helper_debug.log"

# Create file handler with immediate flushing
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Test logging immediately with explicit flushing
test_logger = logging.getLogger("startup_test")
test_logger.info("🚀 LOGGING TEST - MCP Server starting up with file logging enabled")
test_logger.info(f"📁 Log file location: {log_file}")

# Force flush
file_handler.flush()
console_handler.flush()

# Also write directly to file as backup
with open(log_file, 'a') as f:
    import datetime
    f.write(f"{datetime.datetime.now()} - DIRECT_WRITE - MCP Server main.py loaded\n")
    f.flush()

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Jira Helper MCP server."""
    try:
        logger.info("Starting Jira Helper MCP server with hexagonal architecture...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise


if __name__ == "__main__":
    main()
