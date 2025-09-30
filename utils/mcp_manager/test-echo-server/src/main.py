"""
Main entry point for the Test Echo MCP Server.

Simple test server for testing removal functionality.
Uses mcp-commons utilities for standardized server startup.
"""

import sys
import logging
from mcp_commons import run_mcp_server, print_mcp_help

from tool_config import get_tools_config

# Configure logging to stderr to avoid interfering with stdio JSON-RPC
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)


def main() -> None:
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_mcp_help("Test Echo Server", "- Test server for MCP removal functionality")
        return
    
    if sys.argv[1] == "stdio":
        run_mcp_server(
            server_name="test-echo-server",
            tools_config=get_tools_config(),
            transport="stdio"
        )
    else:
        print(f"Unknown transport mode: {sys.argv[1]}", file=sys.stderr)
        print("Use 'stdio' or 'help' for usage information.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
