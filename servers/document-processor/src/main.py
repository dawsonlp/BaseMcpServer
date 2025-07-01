"""
Main entry point for the Document Processor MCP server.

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
    """Print helpful information about using the Document Processor MCP server."""
    help_text = """
Document Processor MCP Server Usage Guide
========================================

BASIC USAGE:
-----------
  python main.py streamable-http  # Run as Streamable HTTP server (for network/container use)
  python main.py stdio           # Run as stdio server (for local development)
  python main.py help            # Show this help message

OVERVIEW:
--------
The Document Processor MCP server converts markdown text to various document formats:
- PDF (using WeasyPrint, pdfkit, ReportLab, or Pandoc)
- HTML (with optional templates)
- Microsoft Word (.docx)
- Plain text

AVAILABLE TOOLS:
---------------
1. convert_markdown_to_pdf - Convert markdown to PDF format
2. convert_markdown_to_html - Convert markdown to HTML format
3. convert_markdown_to_docx - Convert markdown to Word document
4. convert_markdown_to_text - Convert markdown to plain text
5. list_output_files - List all generated files
6. get_server_info - Get server configuration information

DOCKER USAGE:
------------
This server is designed to run in a Docker container with mounted volumes:

  docker run -d \\
    -p 7502:7502 \\
    -v /host/output:/app/output \\
    -v /host/input:/app/input \\
    -v /host/templates:/app/templates \\
    document-processor:latest

CONFIGURATION:
-------------
Environment variables (can be set in .env file):
- SERVER_NAME: Name of the MCP server (default: document-processor)
- HOST: Server host (default: 0.0.0.0)
- PORT: Server port (default: 7502)
- API_KEY: API key for authentication (default: doc_processor_api_key)
- OUTPUT_DIRECTORY: Directory for output files (default: /app/output)
- INPUT_DIRECTORY: Directory for input files (default: /app/input)
- HTML_TEMPLATE_DIR: Directory for HTML templates (default: /app/templates)
- PDF_ENGINE: Default PDF engine (default: weasyprint)
- MAX_FILE_SIZE_MB: Maximum file size in MB (default: 50)

CONNECTING TO CLAUDE/CLINE:
------------------------
To connect this MCP server to Claude Desktop or Cline in VS Code:

1. Make sure the server is running with the streamable-http transport:
   python main.py streamable-http

2. For Cline in VS Code, edit the settings file:
   
   Path: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
   
   Example configuration:
   
   {
     "mcpServers": {
       "document-processor": {
         "url": "http://localhost:7502/mcp",
         "apiKey": "doc_processor_api_key",
         "disabled": false,
         "autoApprove": []
       }
     }
   }

3. For Claude Desktop, go to:
   Settings → Advanced → MCP Servers → Add MCP Server
   
   Enter:
   - Name: document-processor
   - URL: http://localhost:7502/mcp
   - API Key: doc_processor_api_key

4. Restart Claude/VS Code to apply the changes

EXAMPLE USAGE:
-------------
Once connected, you can use the tools like this:

1. Convert markdown to PDF:
   convert_markdown_to_pdf(
     markdown_text="# Hello World\\n\\nThis is a test document.",
     filename="my_document",
     engine="weasyprint"
   )

2. Convert to HTML with template:
   convert_markdown_to_html(
     markdown_text="# My Report\\n\\nContent here...",
     filename="report",
     template="professional.html"
   )

3. List generated files:
   list_output_files()

TEMPLATES:
---------
HTML templates should be placed in the templates directory and use Jinja2 syntax.
The markdown content is available as {{ content }} in templates.

Example template:
<!DOCTYPE html>
<html>
<head>
    <title>Professional Document</title>
    <style>
        body { font-family: 'Times New Roman', serif; margin: 2cm; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
    </style>
</head>
<body>
    {{ content }}
</body>
</html>

For more information, see the MCP SDK documentation at:
https://github.com/modelcontextprotocol/python-sdk
"""
    print(help_text)


def start_server(transport="streamable-http"):
    """Start the MCP server using the specified transport."""
    # Log important configuration
    logger.info(f"Starting {settings.server_name}")
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Output directory: {settings.output_directory}")
    logger.info(f"Input directory: {settings.input_directory}")
    logger.info(f"Template directory: {settings.html_template_dir}")
    logger.info(f"PDF engine: {settings.pdf_engine}")
    logger.info(f"API Key is set: {'Yes' if settings.api_key else 'No'}")
    
    # Create the MCP server using the hexagonal architecture
    from server import create_document_processor_server
    mcp_server = create_document_processor_server()
    
    # Configure server settings
    if transport == "streamable-http":
        mcp_server.settings.host = settings.host
        mcp_server.settings.port = settings.port
        logger.info(f"Using Streamable HTTP transport on {settings.host}:{settings.port}")
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
    return mcp_server.streamable_http_app()


def main():
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_help()
        return
    
    if sys.argv[1] == "streamable-http":
        start_server("streamable-http")
    elif sys.argv[1] == "stdio":
        start_server("stdio")
    else:
        print(f"Unknown transport mode: {sys.argv[1]}")
        print("Use 'streamable-http', 'stdio', or 'help' for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
