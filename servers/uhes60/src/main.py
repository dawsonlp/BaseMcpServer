#!/usr/bin/env python3
"""
UHES60 MCP Server

A simple MCP server demonstrating tools, prompts, and resources.
"""

import logging
import sys
from pathlib import Path
import typer

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from adapters.mcp_adapter import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def main(transport: str = typer.Argument("stdio", help="The transport to use (stdio or sse)")):
    """Main entry point for the UHES60 MCP server."""
    try:
        logger.info(f"Starting UHES60 MCP server with transport: {transport}")
        # The mcp object will be configured to use the specified transport
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    app()
