"""
MCP Server Creator - Dynamically creates and installs MCP servers from Python code.

This module provides the implementation for all MCP tools using the mcp-commons
bulk registration system, eliminating the need for manual @srv.tool() decorators.
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
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import settings

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the utils directory to the path so we can import mcp_manager
utils_path = Path(__file__).parent.parent.parent.parent / "utils"
if str(utils_path) not in sys.path:
    sys.path.insert(0, str(utils_path))

try:
    from mcp_manager.src.mcp_manager.commands.install import install_local_server
    MCP_MANAGER_AVAILABLE = True
except ImportError:
    MCP_MANAGER_AVAILABLE = False
    logger.warning("mcp-manager not available for direct import")


def create_server_files(
    server_dir: Path,
    server_name: str,
    code_snippet: str,
    description: str,
    author: str,
    tool_names: List[str]
) -> None:
    """
    Create all necessary files for a new MCP server using modern mcp-commons pattern.
    
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
    
    # Create config.py using modern approach
    config_content = f'''"""
Configuration for {server_name}.
"""

from typing import Dict, Any, Optional


class SimpleConfig:
    """Simple configuration class for {server_name}."""
    
    def __init__(self):
        self._config = {{
            "server": {{
                "name": "{server_name}",
                "host": "localhost", 
                "port": 7501
            }}
        }}
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(section, {{}}).get(key, default)


# Global config instance
config = SimpleConfig()
'''
    
    with open(src_dir / "config.py", "w") as f:
        f.write(config_content)
    
    # Extract imports and function definitions from code snippet
    parsed_code = ast.parse(code_snippet)
    imports = []
    function_defs = []
    
    # Extract imports
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.Import):
            import_names = [alias.name for alias in node.names]
            imports.append(f"import {', '.join(import_names)}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                from_names = [alias.name for alias in node.names]
                imports.append(f"from {node.module} import {', '.join(from_names)}")
    
    # Extract function definitions
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.FunctionDef):
            # Check if it has @srv.tool() decorator
            has_tool_decorator = False
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "tool" and isinstance(decorator.func.value, ast.Name):
                        if decorator.func.value.id == "srv":
                            has_tool_decorator = True
                            break
            
            if has_tool_decorator:
                # Extract the function body without the decorator and add self parameter
                func_source = ast.get_source_segment(code_snippet, node)
                if func_source:
                    lines = func_source.split('\n')
                    filtered_lines = []
                    for line in lines:
                        if not line.strip().startswith('@srv.tool'):
                            # Add self parameter to function signature
                            if line.strip().startswith('def '):
                                # Replace "def func_name(" with "def func_name(self, " or "def func_name() ->" with "def func_name(self) ->"
                                if '(' in line and ')' in line:
                                    before_paren = line[:line.find('(')]
                                    after_paren = line[line.find('(') + 1:]
                                    if after_paren.strip().startswith(')'):
                                        # No parameters, just add self
                                        line = f"{before_paren}(self{after_paren}"
                                    else:
                                        # Has parameters, add self as first
                                        line = f"{before_paren}(self, {after_paren}"
                            filtered_lines.append(line)
                    
                    if filtered_lines:
                        function_defs.append('\n'.join(filtered_lines))
    
    # Create implementation class
    impl_methods = []
    for func_def in function_defs:
        # Indent the function definition for class method
        indented_func = '\n'.join('    ' + line for line in func_def.split('\n'))
        impl_methods.append(indented_func)
    
    # Build import statements for server.py
    import_statements = [
        "import logging",
        "from typing import Dict, Any, List, Optional"
    ]
    
    # Add extracted imports from code snippet
    for imp in imports:
        if imp not in import_statements:
            import_statements.append(imp)
    
    imports_section = '\n'.join(import_statements)
    
    # Create server.py with implementation class
    server_content = f'''"""
{description}

Implementation class for {server_name} MCP server tools.
"""

{imports_section}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {server_name.replace('-', '_').title()}Implementation:
    """
    Implementation class containing all MCP tool methods.
    
    This class provides the actual implementation for all tools that will be
    bulk registered with the mcp-commons system.
    """
    
{chr(10).join(impl_methods) if impl_methods else '    def placeholder_tool(self) -> Dict[str, Any]:\n        """Placeholder tool."""\n        return {"message": "No tools implemented"}'}
'''
    
    with open(src_dir / "server.py", "w") as f:
        f.write(server_content)
    
    # Create tool_config.py using modern pattern
    impl_class_name = f"{server_name.replace('-', '_').title()}Implementation"
    
    tool_entries = []
    for tool_name in tool_names:
        tool_entries.append(f'''    '{tool_name}': {{
        'function': _implementation.{tool_name},
        'description': '{tool_name.replace("_", " ").title()} tool'
    }}''')
    
    tool_config_content = f'''"""
Tool configuration for {server_name}.

This module defines the configuration for all MCP tools that will be bulk registered
with the mcp-commons system, eliminating the need for individual @srv.tool() decorators.
"""

from typing import Dict, Any
from server import {impl_class_name}


# Create implementation instance for tool functions
_implementation = {impl_class_name}()


# Tool configuration - single source of truth for all {server_name} tools
{server_name.replace('-', '_').upper()}_TOOLS: Dict[str, Dict[str, Any]] = {{
{',\n\n'.join(tool_entries) if tool_entries else '    \'placeholder_tool\': {\n        \'function\': _implementation.placeholder_tool,\n        \'description\': \'Placeholder tool\'\n    }'}
}}


def get_tool_count() -> int:
    """Get the total number of configured tools."""
    return len({server_name.replace('-', '_').upper()}_TOOLS)


def get_tool_names() -> list[str]:
    """Get list of all tool names."""
    return list({server_name.replace('-', '_').upper()}_TOOLS.keys())


def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool configuration dictionary

    Raises:
        KeyError: If tool name not found
    """
    if tool_name not in {server_name.replace('-', '_').upper()}_TOOLS:
        raise KeyError(f"Tool '{{tool_name}}' not found in configuration")
    
    return {server_name.replace('-', '_').upper()}_TOOLS[tool_name].copy()


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """
    Get the tools configuration for registration.
    
    Returns:
        Dictionary mapping tool names to their configuration
    """
    return {server_name.replace('-', '_').upper()}_TOOLS


def get_config_stats() -> Dict[str, Any]:
    """
    Get statistics about the tool configuration.

    Returns:
        Configuration statistics
    """
    return {{
        'total_tools': len({server_name.replace('-', '_').upper()}_TOOLS),
        'description': 'Metadata-driven tool configuration for {server_name}'
    }}
'''
    
    with open(src_dir / "tool_config.py", "w") as f:
        f.write(tool_config_content)
    
    # Create main.py using modern mcp-commons pattern
    main_content = f'''"""
Main entry point for the {server_name} MCP Server.

Consolidated to use mcp-commons utilities for standardized server startup.
"""

import sys
from mcp_commons import run_mcp_server, create_mcp_app, print_mcp_help

from config import config
from tool_config import get_tools_config


def main() -> None:
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_mcp_help("{server_name}", "- {description}")
        return
    
    # Get config values
    server_name = config.get("server", "name", default="{server_name}")
    host = config.get("server", "host", default="localhost")
    port = config.get("server", "port", default=7501)
    
    if sys.argv[1] == "sse":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="sse",
            host=host,
            port=port
        )
    elif sys.argv[1] == "stdio":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="stdio"
        )
    else:
        print(f"Unknown transport mode: {{sys.argv[1]}}")
        print("Use 'sse', 'stdio', or 'help' for usage information.")
        sys.exit(1)


def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    server_name = config.get("server", "name", default="{server_name}")
    
    return create_mcp_app(
        server_name=server_name,
        tools_config=get_tools_config()
    )


if __name__ == "__main__":
    main()
'''
    
    with open(src_dir / "main.py", "w") as f:
        f.write(main_content)
    
    # Create requirements.txt with modern dependencies
    requirements_content = '''# Core MCP dependencies (Python 3.13+)
mcp>=1.13.1

# Additional dependencies for tool functionality
psutil>=6.1.0

# For local development, mcp-commons should be installed separately
# Run: pip install -e /Users/ldawson/repos/mcp-commons
'''
    
    with open(server_dir / "requirements.txt", "w") as f:
        f.write(requirements_content)


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
    
    # Extract the tool names from @mcp.tool() or @srv.tool() decorators
    tool_names = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "tool" and isinstance(decorator.func.value, ast.Name):
                        # Support both @mcp.tool() and @srv.tool() patterns
                        if decorator.func.value.id in ["mcp", "srv"]:
                            tool_names.append(node.name)
    
    if not tool_names:
        raise ValueError("No tools defined with @mcp.tool() or @srv.tool() decorator. Remember to include parentheses: use @srv.tool() instead of @srv.tool")
    
    return tool_names


def install_server(server_dir: Path, server_name: str) -> bool:
    """
    Install the MCP server using mcpmanager.
    
    Args:
        server_dir: Directory containing the server files
        server_name: Name to install the server under
        
    Returns:
        True if installation succeeded, False otherwise
    """
    try:
        # Call mcp-manager to install the server (mcp-manager is included in our requirements)
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


class MCPServerCreatorImplementation:
    """
    Implementation class containing all MCP tool methods.
    
    This class provides the actual implementation for all tools that will be
    bulk registered with the mcp-commons system.
    """
    
    def help(self) -> Dict[str, str]:
        """
        Get detailed help and security information about the MCP Server Creator.
        
        This tool provides comprehensive information about using the MCP Server Creator,
        including important security warnings and best practices.
        
        Returns:
            Dictionary containing help sections including usage, security warnings, and examples
        """
        help_text = {
            "description": "The MCP Server Creator dynamically creates and installs new MCP servers based on Python code snippets.",
            
            "security_warning": """
⚠️ IMPORTANT SECURITY WARNING ⚠️

The MCP Server Creator allows an AI to:
1. Write arbitrary Python code from vague specifications
2. Install that code as an MCP server
3. Use that server without human code review

SECURITY RISKS:
- CODE EXECUTION: Generated code runs on your machine with the same privileges as your user
- LACK OF REVIEW: Server code is installed and made available without mandatory human review
- SECURITY BYPASSES: May circumvent some built-in AI safety restrictions
- DATA EXFILTRATION: Potential for accessing sensitive data on your machine
- API KEYS: Any keys or credentials in generated code could be misused

SAFETY RECOMMENDATIONS:
- ALWAYS review generated code before using the server
- NEVER include API keys or sensitive credentials in code snippets
- USE with caution in production or sensitive environments
- INSPECT code in ~/.mcp_servers directory after creation
- CONSIDER security implications before creating servers that access external services
- DISABLE the server when not in active use
            """,
            
            "usage": """
To create a new MCP server, use the create_mcp_server tool with:
- code_snippet: Python code that defines MCP tools using @srv.tool() decorators
- server_name: Name for the new server (alphanumeric with optional hyphens)
- description: Optional description for the server
- author: Optional author name

After creation, restart VS Code completely for the server to be recognized.
            """,
            
            "security_features": """
Built-in security measures:
- AST-based code analysis to detect potentially harmful operations
- Blocking of dangerous imports and system operations
- Restriction of file access operations
- Prevention of direct code execution via eval() or exec()

These measures provide basic protection but ARE NOT FOOLPROOF.
            """,
            
            "limitations": """
Currently, the MCP Server Creator has limitations:
- No automated handling for .env files (manual configuration in ~/.mcp_servers required)
- Limited management of external dependencies
- No mandatory code review step before installation
- Basic validation that can potentially be bypassed by sophisticated code
            """
        }
        
        return help_text
    
    def create_mcp_server(self, code_snippet: str, server_name: str, description: str = "", author: str = "MCP Server Creator") -> Dict[str, Any]:
        """
        Create and install a new MCP server from a Python code snippet.
        
        This tool generates a complete MCP server from a provided code snippet that defines 
        one or more tools. The generated server follows best practices for MCP server architecture
        and includes proper documentation, type hints, and configuration.
        
        Args:
            code_snippet: Python code that defines one or more MCP tools using @srv.tool() decorators.
                         Each tool should be a function decorated with @srv.tool() that returns a dictionary.
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

    def list_installed_servers(self) -> Dict[str, Any]:
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
        """
        try:
            # Find the mcp-manager executable by checking multiple locations
            mcpmanager_paths = [
                # Check common paths for pipx installations
                os.path.expanduser("~/.local/bin/mcp-manager"),  # Linux/macOS pipx default
                os.path.expanduser("~/Library/Python/*/bin/mcp-manager"),  # macOS user Python
                os.path.expanduser("~/AppData/Roaming/Python/*/Scripts/mcp-manager.exe"),  # Windows
                # Check if it's in the system PATH
                "mcp-manager",
            ]
            
            # Find the first valid path that exists
            mcpmanager_cmd = None
            for path in mcpmanager_paths:
                # Handle glob patterns (for version-specific paths)
                if "*" in path:
                    import glob
                    matching_paths = glob.glob(path)
                    if matching_paths:
                        mcpmanager_cmd = matching_paths[0]
                        break
                elif path != "mcpmanager" and os.path.isfile(path):
                    mcpmanager_cmd = path
                    break
            
            # Default to just the name if no specific path was found
            if mcpmanager_cmd is None:
                mcpmanager_cmd = "mcp-manager"
                
            logger.info(f"Using mcp-manager at: {mcpmanager_cmd}")
            
            # Call mcp-manager list command (without --json flag as it's not supported)
            result = subprocess.run(
                [mcpmanager_cmd, "list"],
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
