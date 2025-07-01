"""
Main entry point for the MCP server.

This module sets up and runs the MCP server using FastMCP.
"""

import logging
import sys
import argparse
from mcp.server.fastmcp import FastMCP

from config import settings
from server import register_tools_and_resources


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def print_help():
    """Print helpful information about using and customizing the MCP server."""
    help_text = """
MCP Server Template Usage Guide
===============================

BASIC USAGE:
-----------
  python main.py sse        # Run as HTTP+SSE server (for network/container use)
  python main.py stdio      # Run as stdio server (for local development)
  python main.py help       # Show this help message

CUSTOMIZATION:
-------------
This MCP server is designed with a clear separation of concerns:

1. main.py (THIS FILE):
   - Handles server initialization and transport selection
   - Sets up logging and configuration
   - Generally, you should NOT modify this file

2. server.py:
   - Defines all MCP tools and resources
   - This is where you should add your customizations
   - Use the register_tools_and_resources function to add tools

3. config.py:
   - Contains server configuration settings
   - Environment variables can override these settings
   - Your custom settings should be added here

ADDING NEW TOOLS:
--------------
To add a new tool, edit server.py and add a function within the 
register_tools_and_resources function:

    @srv.tool()
    def my_custom_tool(param1: str) -> Dict[str, Any]:
        \"\"\"
        Tool description here (will be shown to users)
        
        Args:
            param1: Description of parameter
            
        Returns:
            A dictionary with the result
        \"\"\"
        # Your tool implementation here
        return {"result": "Your result"}

ADDING NEW RESOURCES:
------------------
To add a new resource, edit server.py:

    @srv.resource("resource://example/{param}")
    def example_resource(param: str) -> Dict[str, Any]:
        \"\"\"Resource description\"\"\"
        # Resource implementation
        return {"data": f"Data for {param}"}

CONNECTING TO CLAUDE/CLINE:
------------------------
To connect this MCP server to Claude Desktop or Cline in VS Code:

1. First make sure your MCP server is running with the sse transport:
   python main.py sse

2. For Cline in VS Code, edit the settings file:
   
   Path: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
   
   Example configuration:
   
   {
     "mcpServers": {
       "template-server": {
         "url": "http://localhost:7501/sse",
         "apiKey": "your_default_api_key",
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   
   Notes:
   - Use the correct server name from config.py (server_name setting)
   - Ensure the port matches your configuration (default is 7501)
   - Include "/sse" at the end of the URL
   - The apiKey should match the one in your .env file
   
3. For Claude Desktop, go to:
   Settings → Advanced → MCP Servers → Add MCP Server
   
   Enter:
   - Name: template-server (or your custom server name)
   - URL: http://localhost:7501
   - API Key: your_default_api_key (or your custom API key)

4. Restart Claude/VS Code to apply the changes

DEPLOYMENT:
----------
- For local development: Use 'stdio' transport
- For Docker/containers: Use 'sse' transport with port 7501
- Configure with environment variables or .env file

For more information, see the MCP SDK documentation at:
https://github.com/modelcontextprotocol/python-sdk
"""
    print(help_text)


def start_server(transport="sse"):
    """Start the MCP server using the specified transport."""
    # Log important configuration
    logger.info(f"Starting {settings.server_name}")
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"API Key is set: {'Yes' if settings.api_key else 'No'}")
    
    # Create the MCP server directly in main.py
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources from server.py
    register_tools_and_resources(mcp_server)
    
    # Configure server settings
    if transport == "sse":
        mcp_server.settings.host = settings.host
        mcp_server.settings.port = settings.port
        logger.info(f"Using HTTP+SSE transport on {settings.host}:{settings.port}")
    else:  # stdio
        logger.info(f"Using stdio transport")
    
    mcp_server.settings.debug = True
    mcp_server.settings.log_level = "INFO"
    
    # Run the server with the selected transport
    mcp_server.run(transport)


def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    # Create the MCP server
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources
    register_tools_and_resources(mcp_server)
    
    # Configure server settings
    mcp_server.settings.debug = True
    
    # Return the ASGI app instance
    return mcp_server.sse_app()


def main():
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_help()
        return
    
    if sys.argv[1] == "sse":
        start_server("sse")
    elif sys.argv[1] == "stdio":
        start_server("stdio")
    else:
        print(f"Unknown transport mode: {sys.argv[1]}")
        print("Use 'sse', 'stdio', or 'help' for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
