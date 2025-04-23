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
from mcp.types.tool import MCP_TOOL

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
"""

import logging
from mcp.server.fastmcp import FastMCP
from mcp.types.tool import MCP_TOOL

from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(settings.server_name)

{code_snippet}
''')
    
    # Create main.py
    with open(src_dir / "main.py", "w") as f:
        f.write(f'''"""
Main entry point for the {server_name} MCP Server.
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
    logger.info(f"Starting {server_name}-server with %s transport", transport)
    
    # Run the server with the specified transport
    run(transport)
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
    
    # Extract the tool names from @mcp.tool decorators
    tool_names = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "tool" and isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "mcp":
                        tool_names.append(node.name)
    
    if not tool_names:
        raise ValueError("No tools defined with @mcp.tool decorator")
    
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


@mcp.tool
def create_mcp_server(code_snippet: str, server_name: str, description: str = "", author: str = "MCP Server Creator") -> Dict[str, Any]:
    """
    Create and install a new MCP server from a Python code snippet.
    
    Args:
        code_snippet: Python code that defines one or more MCP tools using @mcp.tool decorators
        server_name: Name for the new MCP server (alphanumeric with optional hyphens)
        description: Optional description for the server
        author: Optional author name for the server
        
    Returns:
        Dictionary with result information including server name and tool names
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


@mcp.tool
def list_installed_servers() -> Dict[str, Any]:
    """
    List all installed MCP servers.
    
    Returns:
        Dictionary with server information
    """
    try:
        # Call mcp-manager list to get all servers
        result = subprocess.run(
            ["mcp-manager", "list", "--json"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Parse the JSON output
        servers = json.loads(result.stdout)
        
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
