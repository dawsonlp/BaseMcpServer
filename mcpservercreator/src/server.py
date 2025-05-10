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
    
    # Create config.py - using separate string concatenation to avoid f-string triple quote issues
    config_content = '"""\n'
    config_content += f'Configuration settings for {server_name}.\n'
    config_content += '"""\n\n'
    config_content += 'import os\n'
    config_content += 'from pydantic_settings import BaseSettings\n\n\n'
    config_content += 'class Settings(BaseSettings):\n'
    config_content += f'    """Configuration settings for {server_name} server."""\n'
    config_content += '    \n'
    config_content += '    # MCP server settings\n'
    config_content += '    host: str = os.getenv("HOST", "0.0.0.0")\n'
    config_content += '    port: int = int(os.getenv("PORT", 7501))\n'
    config_content += '    api_key: str = os.getenv("API_KEY", "example_key")\n'
    config_content += f'    server_name: str = os.getenv("SERVER_NAME", "{server_name}")\n'
    config_content += '    \n'
    config_content += '    class Config:\n'
    config_content += '        env_file = ".env"\n'
    config_content += '        case_sensitive = False\n\n\n'
    config_content += 'settings = Settings()\n'
    
    with open(src_dir / "config.py", "w") as f:
        f.write(config_content)
    
    # Indent the code snippet for proper placement within the function
    indented_code = "\n".join("    " + line for line in code_snippet.splitlines())
    
    # Create server.py with the provided code snippet - using string concatenation to avoid triple quote issues
    server_content = '"""\n'
    server_content += f'{description}\n\n'
    server_content += 'This module defines tools and resources for the MCP server.\n'
    server_content += 'All tool and resource definitions should be placed inside the register_tools_and_resources function.\n'
    server_content += '"""\n\n'
    server_content += 'import logging\n'
    server_content += 'import random\n'
    server_content += 'from typing import Dict, Any, List, Optional, Union, Literal\n'
    server_content += 'from mcp.server.fastmcp import FastMCP\n\n'
    server_content += '# Set up logging\n'
    server_content += 'logging.basicConfig(level=logging.INFO)\n'
    server_content += 'logger = logging.getLogger(__name__)\n\n\n'
    server_content += 'def register_tools_and_resources(mcp: FastMCP) -> None:\n'
    server_content += '    """\n'
    server_content += '    Register tools and resources with the provided MCP server instance.\n'
    server_content += '    \n'
    server_content += '    This is the main entry point for defining all tools and resources.\n'
    server_content += '    Add your custom tool implementations as decorated functions within this function.\n'
    server_content += '    \n'
    server_content += '    Example:\n'
    server_content += '        @mcp.tool()\n'
    server_content += '        def my_tool(param1: str, param2: int) -> Dict[str, Any]:\n'
    server_content += "            '''Tool description'''\n"
    server_content += '            # Tool implementation\n'
    server_content += '            return {"result": "result"}\n'
    server_content += '            \n'
    server_content += '        @mcp.resource("resource://my-resource/{parameter}")\n'
    server_content += '        def my_resource(parameter: str) -> Dict[str, Any]:\n'
    server_content += "            '''Resource description'''\n"
    server_content += '            # Resource implementation\n'
    server_content += '            return {"data": "data"}\n'
    server_content += '    \n'
    server_content += '    Args:\n'
    server_content += '        mcp: A FastMCP server instance to register tools and resources with\n'
    server_content += '    """\n'
    server_content += f'{indented_code}\n'
    
    with open(src_dir / "server.py", "w") as f:
        f.write(server_content)
    
    # Create main.py - using separate string concatenation to avoid f-string triple quote issues
    main_content = '"""\n'
    main_content += f'Main entry point for the {server_name} MCP Server.\n\n'
    main_content += 'This module sets up and runs the MCP server using FastMCP.\n'
    main_content += 'It handles server initialization, transport selection, and configuration.\n'
    main_content += '"""\n\n'
    main_content += 'import sys\n'
    main_content += 'import logging\n'
    main_content += 'from typing import Any\n'
    main_content += 'from mcp.server.fastmcp import FastMCP\n\n'
    main_content += 'from config import settings\n'
    main_content += 'from server import register_tools_and_resources\n\n'
    main_content += '# Set up logging\n'
    main_content += 'logging.basicConfig(\n'
    main_content += '    level=logging.INFO,\n'
    main_content += '    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",\n'
    main_content += '    handlers=[logging.StreamHandler(sys.stdout)]\n'
    main_content += ')\n'
    main_content += 'logger = logging.getLogger(__name__)\n\n\n'
    main_content += 'def print_help() -> None:\n'
    main_content += '    """Print helpful information about using and customizing the MCP server."""\n'
    main_content += '    help_text = """\n'
    main_content += f'{server_name} MCP Server Usage Guide\n'
    main_content += '==========================\n\n'
    main_content += 'BASIC USAGE:\n'
    main_content += '-----------\n'
    main_content += '  python main.py sse        # Run as HTTP+SSE server (for network/container use)\n'
    main_content += '  python main.py stdio      # Run as stdio server (for local development)\n'
    main_content += '  python main.py help       # Show this help message\n\n'
    main_content += 'CUSTOMIZATION:\n'
    main_content += '-------------\n'
    main_content += 'This MCP server is designed with a clear separation of concerns:\n\n'
    main_content += '1. main.py (THIS FILE):\n'
    main_content += '   - Handles server initialization and transport selection\n'
    main_content += '   - Sets up logging and configuration\n'
    main_content += '   - Generally, you should NOT modify this file\n\n'
    main_content += '2. server.py:\n'
    main_content += '   - Defines all MCP tools and resources\n'
    main_content += '   - This is where you should add your customizations\n'
    main_content += '   - Use the register_tools_and_resources function to add tools\n\n'
    main_content += '3. config.py:\n'
    main_content += '   - Contains server configuration settings\n'
    main_content += '   - Environment variables can override these settings\n\n'
    main_content += 'ADDING NEW TOOLS:\n'
    main_content += '---------------\n'
    main_content += 'To add a new tool, edit server.py and add a function within the\n'
    main_content += 'register_tools_and_resources function:\n\n'
    main_content += '    @mcp.tool()\n'
    main_content += '    def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:\n'
    main_content += '        # Description comments instead of nested triple quotes\n'
    main_content += '        # Tool description here (will be shown to users)\n'
    main_content += '        #\n'
    main_content += '        # Args:\n'
    main_content += '        #    param1: Description of first parameter\n'
    main_content += '        #    param2: Description of second parameter\n'
    main_content += '        #\n'
    main_content += '        # Returns:\n'
    main_content += '        #    A dictionary with the result\n'
    main_content += '        \n'
    main_content += '        # Your tool implementation here\n'
    main_content += '        result = do_something(param1, param2)\n'
    main_content += '        return {"result": result}\n\n'
    main_content += 'ADDING NEW RESOURCES:\n'
    main_content += '------------------\n'
    main_content += 'To add a new resource, edit server.py:\n\n'
    main_content += '    @mcp.resource("resource://my-resource")\n'
    main_content += '    def my_resource() -> Dict[str, Any]:\n'
    main_content += '        # Resource description \n'
    main_content += '        return {"data": "resource content"}\n\n'
    main_content += 'CONNECTING TO CLAUDE/CLINE:\n'
    main_content += '------------------------\n'
    main_content += 'To connect this MCP server to Claude Desktop or Cline in VS Code:\n\n'
    main_content += '1. First make sure your MCP server is running with the sse transport:\n'
    main_content += '   python main.py sse\n\n'
    main_content += '2. For Cline in VS Code, edit the settings file:\n\n'
    main_content += '   Path: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json\n\n'
    main_content += '   Example configuration:\n\n'
    main_content += '   {\n'
    main_content += '     "mcpServers": {\n'
    main_content += f'       "{server_name}": {{\n'
    main_content += '         "url": "http://localhost:7501/sse",\n'
    main_content += '         "apiKey": "example_key",\n'
    main_content += '         "disabled": false,\n'
    main_content += '         "autoApprove": []\n'
    main_content += '       }\n'
    main_content += '     }\n'
    main_content += '   }\n\n'
    main_content += '   Notes:\n'
    main_content += '   - Use the correct server name from config.py (server_name setting)\n'
    main_content += '   - Ensure the port matches your configuration (default is 7501)\n'
    main_content += '   - Include "/sse" at the end of the URL\n'
    main_content += '   - The apiKey should match the one in your .env file\n\n'
    main_content += '3. For Claude Desktop, go to:\n'
    main_content += '   Settings → Advanced → MCP Servers → Add MCP Server\n\n'
    main_content += '   Enter:\n'
    main_content += f'   - Name: {server_name} (must match the server_name in config.py)\n'
    main_content += '   - URL: http://localhost:7501\n'
    main_content += '   - API Key: example_key (or your custom API key)\n\n'
    main_content += '4. Restart Claude/VS Code to apply the changes\n\n'
    main_content += 'DEPLOYMENT:\n'
    main_content += '----------\n'
    main_content += '- For local development: Use \'stdio\' transport\n'
    main_content += '- For Docker/containers: Use \'sse\' transport with port 7501\n'
    main_content += '- Configure with environment variables or .env file\n\n'
    main_content += 'For more information, see the MCP SDK documentation at:\n'
    main_content += 'https://github.com/modelcontextprotocol/python-sdk\n'
    main_content += '"""\n'
    main_content += '    print(help_text)\n\n\n'
    main_content += 'def start_server(transport: str = "sse") -> None:\n'
    main_content += '    """Start the MCP server using the specified transport."""\n'
    main_content += '    # Create the MCP server\n'
    main_content += '    mcp_server = FastMCP(settings.server_name)\n'
    main_content += '    \n'
    main_content += '    # Register all tools and resources\n'
    main_content += '    register_tools_and_resources(mcp_server)\n'
    main_content += '    \n'
    main_content += '    # Log important configuration\n'
    main_content += '    logger.info(f"Starting {settings.server_name}")\n\n'
    main_content += '    # Configure server settings\n'
    main_content += '    if transport == "sse":\n'
    main_content += '        mcp_server.settings.host = settings.host\n'
    main_content += '        mcp_server.settings.port = settings.port\n'
    main_content += '        logger.info(f"Using HTTP+SSE transport on {settings.host}:{settings.port}")\n'
    main_content += '    else:  # stdio\n'
    main_content += '        logger.info(f"Using stdio transport")\n\n'
    main_content += '    mcp_server.settings.debug = True\n'
    main_content += '    mcp_server.settings.log_level = "INFO"\n\n'
    main_content += '    # Run the server with the selected transport\n'
    main_content += '    mcp_server.run(transport)\n\n\n'
    main_content += 'def create_app() -> Any:\n'
    main_content += '    """Create an ASGI application for use with an external ASGI server."""\n'
    main_content += '    # Create the MCP server\n'
    main_content += '    mcp_server = FastMCP(settings.server_name)\n'
    main_content += '    \n'
    main_content += '    # Register all tools and resources\n'
    main_content += '    register_tools_and_resources(mcp_server)\n'
    main_content += '    \n'
    main_content += '    # Configure server settings\n'
    main_content += '    mcp_server.settings.debug = True\n\n'
    main_content += '    # Return the ASGI app instance\n'
    main_content += '    return mcp_server.sse_app()\n\n\n'
    main_content += 'def main() -> None:\n'
    main_content += '    """Process command-line arguments and start the server appropriately."""\n'
    main_content += '    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:\n'
    main_content += '        print_help()\n'
    main_content += '        return\n'
    main_content += '    \n'
    main_content += '    if sys.argv[1] == "sse":\n'
    main_content += '        start_server("sse")\n'
    main_content += '    elif sys.argv[1] == "stdio":\n'
    main_content += '        start_server("stdio")\n'
    main_content += '    else:\n'
    main_content += '        print(f"Unknown transport mode: {sys.argv[1]}")\n'
    main_content += '        print("Use \'sse\', \'stdio\', or \'help\' for usage information.")\n'
    main_content += '        sys.exit(1)\n\n\n'
    main_content += 'if __name__ == "__main__":\n'
    main_content += '    main()\n'
    
    with open(src_dir / "main.py", "w") as f:
        f.write(main_content)
    
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


def register_tools_and_resources(mcp: FastMCP) -> None:
    """
    Register tools and resources with the provided MCP server instance.
    
    This is the main entry point for defining all tools and resources.
    Add your custom tool implementations as decorated functions within this function.
    
    Args:
        mcp: A FastMCP server instance to register tools and resources with
    """
    
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
