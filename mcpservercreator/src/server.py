"""
MCP Server Creator - Dynamically creates and installs MCP servers from Python code.
"""

import os
import json
import tempfile
import logging
import re
import ast
import shutil
import uuid
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP

from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_server_files(
    server_dir: Path,
    server_name: str,
    code_snippet: str,
    description: str,
    author: str,
    tool_names: List[str]
) -> None:
    """
    Create all necessary files for a new MCP server.
    
    Args:
        server_dir: Directory to create the files in
        server_name: Name of the server
        code_snippet: Python code that defines the server tools
        description: Description of the server
        author: Author of the server
        tool_names: List of tools defined in the code snippet
    """
    # Create src directory
    src_dir = server_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    # Create __init__.py
    with open(src_dir / "__init__.py", "w") as f:
        f.write(f"# {server_name} package\n")
    
    # Create config.py
    with open(src_dir / "config.py", "w") as f:
        f.write(f'''"""
Configuration settings for {server_name}.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for {server_name} server."""
    
    # MCP server settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 7501))
    api_key: str = os.getenv("API_KEY", "example_key")
    server_name: str = os.getenv("SERVER_NAME", "{server_name}-server")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
''')
    
    # Create server.py with the provided code snippet
    with open(src_dir / "server.py", "w") as f:
        f.write(f'''"""
{description}

This module defines tools and resources for the MCP server.
All tool and resource definitions should be placed inside the register_tools_and_resources function.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_tools_and_resources(mcp: FastMCP) -> None:
    """
    Register tools and resources with the provided MCP server instance.
    
    This is the main entry point for defining all tools and resources.
    Add your custom tool implementations as decorated functions within this function.
    
    Example:
        @mcp.tool()
        def my_tool(param1: str, param2: int) -> Dict[str, Any]:
            \"\"\"Tool description\"\"\"
            # Tool implementation
            return {{"result": result}}
            
        @mcp.resource("resource://my-resource/{{parameter}}")
        def my_resource(parameter: str) -> Dict[str, Any]:
            \"\"\"Resource description\"\"\"
            # Resource implementation
            return {{"data": data}}
    
    Args:
        mcp: A FastMCP server instance to register tools and resources with
    """
{code_snippet}
''')
    
    # Create main.py
    with open(src_dir / "main.py", "w") as f:
        f.write(f'''"""
Main entry point for the {server_name} MCP Server.

This module sets up and runs the MCP server using FastMCP.
It handles server initialization, transport selection, and configuration.
"""

import sys
import logging
from mcp.server.fastmcp import FastMCP

from config import settings
from server import register_tools_and_resources

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def print_help() -> None:
    """Print helpful information about using and customizing the MCP server."""
    help_text = """
{server_name} MCP Server Usage Guide
==========================

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

ADDING NEW TOOLS:
---------------
To add a new tool, edit server.py and add a function within the
register_tools_and_resources function:

    @mcp.tool()
    def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
        \"\"\"
        Tool description here (will be shown to users)

        Args:
            param1: Description of first parameter
            param2: Description of second parameter

        Returns:
            A dictionary with the result
        \"\"\"
        # Your tool implementation here
        result = do_something(param1, param2)
        return {{"result": result}}

ADDING NEW RESOURCES:
------------------
To add a new resource, edit server.py:

    @mcp.resource("resource://my-resource")
    def my_resource() -> Dict[str, Any]:
        \"\"\"Resource description\"\"\"
        return {{"data": "resource content"}}

CONNECTING TO CLAUDE/CLINE:
------------------------
To connect this MCP server to Claude Desktop or Cline in VS Code:

1. First make sure your MCP server is running with the sse transport:
   python main.py sse

2. For Cline in VS Code, edit the settings file:

   Path: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json

   Example configuration:

   {{
     "mcpServers": {{
       "{server_name}-server": {{
         "url": "http://localhost:7501/sse",
         "apiKey": "example_key",
         "disabled": false,
         "autoApprove": []
       }}
     }}
   }}

   Notes:
   - Use the correct server name from config.py (server_name setting)
   - Ensure the port matches your configuration (default is 7501)
   - Include "/sse" at the end of the URL
   - The apiKey should match the one in your .env file

3. For Claude Desktop, go to:
   Settings → Advanced → MCP Servers → Add MCP Server

   Enter:
   - Name: {server_name}-server (or your custom server name)
   - URL: http://localhost:7501
   - API Key: example_key (or your custom API key)

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


def start_server(transport: str = "sse") -> None:
    """Start the MCP server using the specified transport."""
    # Create the MCP server
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources
    register_tools_and_resources(mcp_server)
    
    # Log important configuration
    logger.info(f"Starting {{settings.server_name}}")

    # Configure server settings
    if transport == "sse":
        mcp_server.settings.host = settings.host
        mcp_server.settings.port = settings.port
        logger.info(f"Using HTTP+SSE transport on {{settings.host}}:{{settings.port}}")
    else:  # stdio
        logger.info(f"Using stdio transport")

    mcp_server.settings.debug = True
    mcp_server.settings.log_level = "INFO"

    # Run the server with the selected transport
    mcp_server.run(transport)


def create_app() -> Any:
    """Create an ASGI application for use with an external ASGI server."""
    # Create the MCP server
    mcp_server = FastMCP(settings.server_name)
    
    # Register all tools and resources
    register_tools_and_resources(mcp_server)
    
    # Configure server settings
    mcp_server.settings.debug = True

    # Return the ASGI app instance
    return mcp_server.sse_app()


def main() -> None:
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_help()
        return
    
    if sys.argv[1] == "sse":
        start_server("sse")
    elif sys.argv[1] == "stdio":
        start_server("stdio")
    else:
        print(f"Unknown transport mode: {{sys.argv[1]}}")
        print("Use 'sse', 'stdio', or 'help' for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
''')
    
    # Create requirements.txt
    with open(server_dir / "requirements.txt", "w") as f:
        f.write('''# Core MCP dependencies
mcp>=1.6.0
pydantic-settings>=2.9.1
python-dotenv>=1.1.0
uvicorn>=0.34.2
''')


def validate_code_snippet(code_snippet: str) -> List[str]:
    """
    Validate the Python code snippet to ensure it's safe.
    
    Args:
        code_snippet: Python code to validate
        
    Returns:
        List of tool names defined in the snippet
    """
    # Parse the code to check for potentially dangerous imports
    try:
        parsed = ast.parse(code_snippet)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python syntax: {str(e)}")
    
    # Check for forbidden imports
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for name in node.names:
                if any(name.name.startswith(restricted) for restricted in settings.restricted_imports):
                    raise ValueError(f"Import of {name.name} is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if any(node.module.startswith(restricted) for restricted in settings.restricted_imports):
                raise ValueError(f"Import from {node.module} is not allowed")
    
    # Extract the tool names from @mcp.tool() decorators
    tool_names = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "tool" and isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "mcp":
                        tool_names.append(node.name)
    
    if not tool_names:
        raise ValueError("No tools defined with @mcp.tool() decorator. Remember to include parentheses: use @mcp.tool() instead of @mcp.tool")
    
    return tool_names


def install_server(server_dir: Path, server_name: str) -> bool:
    """
    Install the MCP server using mcp-manager.
    
    Args:
        server_dir: Directory containing the server files
        server_name: Name to install the server under
        
    Returns:
        True if installation succeeded, False otherwise
    """
    try:
        # Call mcp-manager to install the server
        subprocess.run(
            ["mcp-manager", "install", "local", server_name, "--source", str(server_dir), "--force"],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to install server: {str(e)}")
        return False


# Initialize MCP server
mcp = FastMCP(settings.server_name)


@mcp.tool()
def create_mcp_server(code_snippet: str, server_name: str, description: str = "", author: str = "MCP Server Creator") -> Dict[str, Any]:
    """
    Create and install a new MCP server from a Python code snippet.
    
    This tool generates a complete MCP server from a provided code snippet that defines 
    one or more tools. The generated server follows best practices for MCP server architecture
    and includes proper documentation, type hints, and configuration.
    
    Args:
        code_snippet: Python code that defines one or more MCP tools using @mcp.tool() decorators.
                     Each tool should be a function decorated with @mcp.tool() that returns a dictionary.
        server_name: Name for the new MCP server (alphanumeric with optional hyphens).
                    This will be used as the directory name and in configuration.
        description: Optional description for the server. This will appear in docstrings and help text.
        author: Optional author name for the server, defaults to "MCP Server Creator".
        
    Returns:
        Dictionary containing:
          - success: Boolean indicating whether the server was created successfully
          - server_name: The name of the created server
          - tool_names: List of tool names defined in the code snippet
          - message: Success message with instructions for using the server
          - error: Error message if success is False
    
    Example usage:
        To create a simple greeting server, you would:
        1. Define a code snippet with your tool
        2. Call create_mcp_server with the snippet and server details
        3. The server will be created and installed for you
    """
    logger.info(f"Creating MCP server '{server_name}'")
    
    # Validate server name (alphanumeric with optional hyphens)
    if not re.match(r'^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$', server_name):
        return {
            "success": False,
            "error": "Server name must be alphanumeric with optional hyphens"
        }
    
    # Create a temporary directory for the server
    temp_dir = Path(settings.output_dir)
    temp_dir.mkdir(exist_ok=True, parents=True)
    server_dir = temp_dir / server_name
    
    try:
        # Validate the code snippet and get the tool names
        tool_names = validate_code_snippet(code_snippet)
        
        # Create the server files
        if server_dir.exists():
            shutil.rmtree(server_dir)
        server_dir.mkdir(exist_ok=True, parents=True)
        create_server_files(
            server_dir=server_dir,
            server_name=server_name,
            code_snippet=code_snippet,
            description=description,
            author=author,
            tool_names=tool_names
        )
        
        # Install the server using mcp-manager
        success = install_server(server_dir, server_name)
        
        if success:
            return {
                "success": True,
                "server_name": server_name,
                "tool_names": tool_names,
                "message": f"Server '{server_name}' created and installed successfully. Restart VS Code to use it."
            }
        else:
            return {
                "success": False,
                "error": "Failed to install the server. Check the logs for details."
            }
    except ValueError as e:
        logger.error(f"Failed to create server: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


@mcp.tool()
def list_installed_servers() -> Dict[str, Any]:
    """
    List all installed MCP servers.
    
    This tool discovers and lists all MCP servers installed on the system,
    including both local and remote servers. It runs the mcp-manager list
    command and parses the output into a structured format.
    
    Returns:
        Dictionary containing:
          - success: Boolean indicating whether the operation succeeded
          - servers: Dictionary with two keys:
              - local: List of local server information (name, type, source, port, status)
              - remote: List of remote server information (name, url, status)
          - error: Error message if success is False
    
    Example usage:
        To list all installed MCP servers, simply call the function and 
        process the returned dictionary. The servers are organized by type
        (local or remote) and include details like name, type, and status.
    """
    try:
        # Find the mcp-manager executable by checking multiple locations
        mcp_manager_paths = [
            # Check common paths for pipx installations
            os.path.expanduser("~/.local/bin/mcp-manager"),  # Linux/macOS pipx default
            os.path.expanduser("~/Library/Python/*/bin/mcp-manager"),  # macOS user Python
            os.path.expanduser("~/AppData/Roaming/Python/*/Scripts/mcp-manager.exe"),  # Windows
            # Check if it's in the system PATH
            "mcp-manager",
        ]
        
        # Find the first valid path that exists
        mcp_manager_cmd = None
        for path in mcp_manager_paths:
            # Handle glob patterns (for version-specific paths)
            if "*" in path:
                import glob
                matching_paths = glob.glob(path)
                if matching_paths:
                    mcp_manager_cmd = matching_paths[0]
                    break
            elif path != "mcp-manager" and os.path.isfile(path):
                mcp_manager_cmd = path
                break
        
        # Default to just the name if no specific path was found
        if mcp_manager_cmd is None:
            mcp_manager_cmd = "mcp-manager"
            
        logger.info(f"Using mcp-manager at: {mcp_manager_cmd}")
        
        # Call mcp-manager list command (without --json flag as it's not supported)
        result = subprocess.run(
            [mcp_manager_cmd, "list"],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PATH": f"{os.path.expanduser('~/.local/bin')}:{os.environ.get('PATH', '')}"}
        )
        
        # Parse the text output into a structured format
        output = result.stdout
        
        # Example output parsing - this is a basic implementation that should be enhanced
        # for more robust handling of different server types and formats
        servers = {
            "local": [],
            "remote": []
        }
        
        current_section = None
        for line in output.splitlines():
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for section headers
            if "Local MCP Servers" in line:
                current_section = "local"
                continue
            elif "Remote MCP Servers" in line:
                current_section = "remote"
                continue
                
            # Skip table headers and separators
            if line.startswith("───") or line.startswith("Name") or line.startswith("URL"):
                continue
                
            # Process server entries
            if current_section and line:
                parts = [part.strip() for part in line.split() if part.strip()]
                if parts:
                    if current_section == "local" and len(parts) >= 4:
                        servers["local"].append({
                            "name": parts[0],
                            "type": parts[1],
                            "source": parts[2],
                            "port": parts[3],
                            "status": parts[4] if len(parts) > 4 else "Enabled"
                        })
                    elif current_section == "remote" and len(parts) >= 2:
                        servers["remote"].append({
                            "name": parts[0],
                            "url": parts[1],
                            "status": parts[2] if len(parts) > 2 else "Enabled"
                        })
        
        return {
            "success": True,
            "servers": servers
        }
    except Exception as e:
        logger.error(f"Failed to list servers: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
