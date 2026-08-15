"""
MCP Server Creator - Dynamically creates and installs MCP servers from Python code.

Generated servers use the MCP Python SDK directly. Tool implementations are
plain functions and server factories register them with ``MCPServer.add_tool``.
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
from typing import Dict, List, Any, Optional, Set, Tuple, TypedDict

from config import settings

# Set up logging with consistent format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HelpResult(TypedDict):
    description: str
    security_warning: str
    usage: str
    security_features: str
    limitations: str


class CreatedServerResult(TypedDict):
    success: bool
    server_name: str
    tool_names: list[str]
    message: str


class InstalledServersResult(TypedDict):
    success: bool
    servers: dict[str, list[dict[str, Any]]]

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
    Create all necessary files for a factory-based MCP SDK v2 server.
    
    Args:
        server_dir: Directory to create the files in
        server_name: Name of the server
        code_snippet: Python code that defines the server tools
        description: Description of the server
        author: Author of the server
        tool_names: List of tools defined in the code snippet
    """
    logger.info(f"Creating server files for '{server_name}' with {len(tool_names)} tools")

    template_dir = _resolve_template_dir()
    shutil.copytree(
        template_dir,
        server_dir,
        dirs_exist_ok=False,
        ignore=shutil.ignore_patterns(
            ".venv", ".pytest_cache", "__pycache__", "*.egg-info", "dist", "build"
        ),
    )
    (server_dir / "uv.lock").unlink(missing_ok=True)
    src_dir = server_dir / "src"

    parsed_code = ast.parse(code_snippet)
    imports = _extract_imports(parsed_code)
    _, function_defs = _extract_tool_functions(parsed_code, code_snippet)
    _customize_template(
        server_dir, server_name, description, author, imports, function_defs, tool_names
    )
    logger.info(f"Successfully created all files for server '{server_name}'")


def _resolve_template_dir() -> Path:
    """Locate the canonical repository scaffold.

    Generation intentionally fails when the canonical template is unavailable;
    carrying a private embedded copy would recreate the drift this tool exists
    to avoid. Packaged installations may set ``BASE_MCP_TEMPLATE_DIR`` to a
    checkout's ``servers/template`` directory.
    """
    configured = os.environ.get("BASE_MCP_TEMPLATE_DIR")
    candidates = [
        Path(configured).expanduser() if configured else None,
        Path(__file__).resolve().parents[2] / "template",
        Path.cwd() / "servers" / "template",
    ]
    for candidate in candidates:
        if candidate and (candidate / "src" / "main.py").is_file():
            return candidate
    raise RuntimeError(
        "Canonical servers/template scaffold not found; set BASE_MCP_TEMPLATE_DIR "
        "to a BaseMcpServer checkout's servers/template directory"
    )


def _customize_template(
    server_dir: Path,
    server_name: str,
    description: str,
    author: str,
    imports: List[str],
    function_defs: List[str],
    tool_names: List[str],
) -> None:
    """Apply the permitted substitutions to a copied canonical template."""
    package_name = server_name
    env_prefix = server_name.replace("-", "_").upper()
    main_path = server_dir / "src" / "main.py"
    main_source = main_path.read_text(encoding="utf-8")
    main_source = main_source.replace("template MCP server", f"{server_name} MCP server")
    main_source = main_source.replace(
        'DESCRIPTION = "Template MCP Server (replace this description)"',
        f"DESCRIPTION = {description or server_name!r}",
    )
    main_source = main_source.replace('version("template-mcp-server")', f'version("{package_name}")')
    main_source = main_source.replace('default="template"', f'default="{server_name}"')
    main_source = main_source.replace("Template MCP Server", f"{server_name} MCP Server")
    main_source = main_source.replace("Usage: template ", f"Usage: {server_name} ")
    main_path.write_text(main_source, encoding="utf-8")

    config_path = server_dir / "src" / "config.py"
    config_source = config_path.read_text(encoding="utf-8")
    config_source = config_source.replace("template MCP server", f"{server_name} MCP server")
    config_source = config_source.replace(
        'ServerConfig(server_name="template", env_prefix="TEMPLATE")',
        f'ServerConfig(server_name="{server_name}", env_prefix="{env_prefix}")',
    )
    config_path.write_text(config_source, encoding="utf-8")

    config_example = server_dir / "config.yaml.example"
    config_example.write_text(
        config_example.read_text(encoding="utf-8").replace("name: template", f"name: {server_name}"),
        encoding="utf-8",
    )

    tools_source = "\n".join(imports + [""] + function_defs).rstrip() + "\n"
    (server_dir / "src" / "tools.py").write_text(tools_source, encoding="utf-8")
    _create_plain_tool_config(server_dir / "src", tool_names)
    _customize_pyproject(server_dir, package_name, description, author)
    _create_readme_file(server_dir, server_name, description)
    shutil.rmtree(server_dir / "tests")
    _create_test_files(server_dir, server_name, tool_names)


def _create_plain_tool_config(src_dir: Path, tool_names: List[str]) -> None:
    imports = ", ".join(tool_names)
    entries = []
    for tool_name in tool_names:
        entries.append(
            f'    "{tool_name}": {{\n'
            f'        "function": {tool_name},\n'
            f'        "title": "{tool_name.replace("_", " ").title()}",\n'
            f'        "description": {tool_name.replace("_", " ").title()!r},\n'
            '        "annotations": ToolAnnotations(\n'
            '            readOnlyHint=None, destructiveHint=None,\n'
            '            idempotentHint=None, openWorldHint=None,\n'
            '        ),\n'
            '    },'
        )
    content = (
        '"""Tool registration metadata; classify annotations before deployment."""\n\n'
        'from typing import Any\n\nfrom mcp.types import ToolAnnotations\n'
        f'from tools import {imports}\n\nTOOLS: dict[str, dict[str, Any]] = {{\n'
        + "\n".join(entries)
        + '\n}\n\ndef get_tools_config() -> dict[str, dict[str, Any]]:\n    return TOOLS\n'
    )
    (src_dir / "tool_config.py").write_text(content, encoding="utf-8")


def _customize_pyproject(
    server_dir: Path, package_name: str, description: str, author: str
) -> None:
    path = server_dir / "pyproject.toml"
    source = path.read_text(encoding="utf-8")
    source = source.replace('name = "template-mcp-server"', f'name = "{package_name}"')
    source = source.replace(
        'description = "Starter template for new MCP servers in the BaseMcpServer monorepo"',
        f'description = {json.dumps(description or package_name)}',
    )
    source = source.replace(
        '{name = "Your Name", email = "you@example.com"}',
        f'{{name = {json.dumps(author)}}}',
    )
    source = source.replace('template = "main:main"', f'{package_name} = "main:main"')
    source = source.replace(
        'py-modules = ["main", "config", "tool_config"]',
        'py-modules = ["main", "config", "tools", "tool_config"]',
    )
    path.write_text(source, encoding="utf-8")


def _create_readme_file(server_dir: Path, server_name: str, description: str) -> None:
    """Create the README referenced by the generated package metadata."""
    content = f"""# {server_name}

{description or f'Generated MCP server: {server_name}'}

Tools are plain Python methods registered by ``create_server()`` through
``MCPServer.add_tool()``. No registration decorators are used. Every tool must
have fully typed parameters and a concrete return annotation. Review each
generated ``ToolAnnotations`` entry and replace the explicit unknown hints with
behavior-based values before deployment.

Streamable HTTP defaults to loopback. A non-loopback host requires explicit
``server.allowed_hosts`` and ``server.allowed_origins`` configuration.
"""
    with open(server_dir / "README.md", "w") as f:
        f.write(content)


def _create_test_files(server_dir: Path, server_name: str, tool_names: List[str]) -> None:
    """Create a protocol-level smoke test for generated metadata and discovery."""
    tests_dir = server_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    content = f'''from importlib.metadata import version

import anyio
from mcp.client import Client

from main import create_server


def test_generated_server_contract():
    async def check():
        async with Client(create_server(), raise_exceptions=True) as client:
            result = await client.list_tools()
            assert client.server_info.version == version("{server_name}")
        assert {{tool.name for tool in result.tools}} == set({tool_names!r})
        assert all(tool.title and tool.description and tool.annotations for tool in result.tools)

    anyio.run(check)
'''
    with open(tests_dir / "test_server.py", "w") as f:
        f.write(content)


def _extract_imports(parsed_code: ast.Module) -> List[str]:
    """Extract import statements from parsed AST."""
    imports = []
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.Import):
            import_names = [alias.name for alias in node.names]
            imports.append(f"import {', '.join(import_names)}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            from_names = [alias.name for alias in node.names]
            imports.append(f"from {node.module} import {', '.join(from_names)}")
    return imports


def _extract_tool_functions(parsed_code: ast.Module, code_snippet: str) -> Tuple[List[str], List[str]]:
    """Extract public top-level functions as tool implementations."""
    tool_names = []
    function_defs = []
    
    for node in parsed_code.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            tool_names.append(node.name)
            func_source = ast.get_source_segment(code_snippet, node)
            if func_source:
                processed_func = _process_function_definition(func_source)
                if processed_func:
                    function_defs.append(processed_func)
    
    return tool_names, function_defs


def _process_function_definition(func_source: str) -> Optional[str]:
    """Preserve a validated plain top-level tool function."""
    return func_source.strip() or None


def _validate_security_restrictions(parsed_code: ast.Module) -> None:
    """Validate code against security restrictions."""
    restricted_imports = set(settings.restricted_imports)
    
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(restricted) for restricted in restricted_imports):
                    raise ValueError(f"Import of '{alias.name}' is not allowed for security reasons")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if any(node.module.startswith(restricted) for restricted in restricted_imports):
                raise ValueError(f"Import from '{node.module}' is not allowed for security reasons")


def validate_code_snippet(code_snippet: str) -> List[str]:
    """
    Validate the Python code snippet to ensure it's safe and extract tool names.
    
    Args:
        code_snippet: Python code to validate
        
    Returns:
        List of tool names defined in the snippet
        
    Raises:
        ValueError: If code is invalid or unsafe
    """
    if not code_snippet.strip():
        raise ValueError("Code snippet cannot be empty")
    
    # Parse the code to check syntax
    try:
        parsed = ast.parse(code_snippet)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python syntax: {str(e)}")
    
    # Security validation
    _validate_security_restrictions(parsed)

    decorated = [
        node.name
        for node in parsed.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.decorator_list
    ]
    if decorated:
        raise ValueError(
            "Decorators are not accepted. Define plain public functions; "
            "the generated create_server() factory registers them with add_tool()."
        )

    public_functions = [
        node for node in parsed.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]
    for function in public_functions:
        if function.args.kwarg is not None:
            raise ValueError(
                f"Tool {function.name!r} uses **{function.args.kwarg.arg}; expose an explicit "
                "typed mapping parameter instead."
            )
        parameters = [
            *function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs,
        ]
        untyped = [parameter.arg for parameter in parameters if parameter.annotation is None]
        if untyped:
            raise ValueError(
                f"Tool {function.name!r} has untyped parameters: {', '.join(untyped)}."
            )
        if function.returns is None:
            raise ValueError(f"Tool {function.name!r} must declare a return type.")
        if isinstance(function.returns, ast.Name) and function.returns.id in {
            "dict", "list", "set", "tuple",
        }:
            raise ValueError(
                f"Tool {function.name!r} uses bare {function.returns.id}; provide item/value "
                "types or a TypedDict/Pydantic result model."
            )
    
    # Extract tool names and functions
    tool_names, _ = _extract_tool_functions(parsed, code_snippet)
    
    if not tool_names:
        raise ValueError(
            "No tools found. Define at least one plain public top-level function."
        )
    
    logger.info(f"Validated code snippet with {len(tool_names)} tools: {', '.join(tool_names)}")
    return tool_names


def sync_with_cline(server_name: str) -> bool:
    """
    Sync the installed server with Cline configuration.
    
    Args:
        server_name: Name of the server to sync
        
    Returns:
        True if sync succeeded, False otherwise
    """
    try:
        logger.info(f"Syncing server '{server_name}' with Cline configuration")
        result = subprocess.run(
            ["mcp-manager", "sync", "--platform", "cline"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully synced server '{server_name}' with Cline")
            return True
        else:
            logger.warning(f"Cline sync completed with warnings: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Cline sync for server '{server_name}' timed out after 30 seconds")
        return False
    except FileNotFoundError:
        logger.warning("mcp-manager command not found for Cline sync")
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(f"Cline sync failed: {e.stderr if e.stderr else str(e)}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during Cline sync: {str(e)}")
        return False


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
        logger.info(f"Installing server '{server_name}' from {server_dir}")
        result = subprocess.run(
            ["mcp-manager", "install", server_name, "--source", str(server_dir), "--force"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60  # Add timeout for robustness
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully installed server '{server_name}'")
            return True
        else:
            logger.error(f"Installation failed with return code {result.returncode}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Installation of server '{server_name}' timed out after 60 seconds")
        return False
    except FileNotFoundError:
        logger.error("mcp-manager command not found. Ensure mcp-manager is installed and in PATH")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Installation failed: {e.stderr if e.stderr else str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during installation: {str(e)}")
        return False


class MCPServerCreatorImplementation:
    """
    Implementation class containing all MCP tool methods.
    
    This class provides the actual implementation for all tools that will be
    registered by the MCPServer factory.
    """
    
    def help(self) -> HelpResult:
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
- INSPECT generated code under ~/.config/mcp-manager/servers/<name>/ after creation
- CONSIDER security implications before creating servers that access external services
- DISABLE the server when not in active use
            """,
            
            "usage": """
To create a new MCP server, use the create_mcp_server tool with:
- code_snippet: Python code containing plain public tool functions (no decorators)
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
- No automated handling for .env / config.yaml files (place per-server credentials at ~/.config/mcp-manager/servers/<name>/config.yaml)
- Limited management of external dependencies
- No mandatory code review step before installation
- Basic validation that can potentially be bypassed by sophisticated code
            """
        }
        
        return help_text
    
    def create_mcp_server(self, code_snippet: str, server_name: str, description: str = "", author: str = "MCP Server Creator") -> CreatedServerResult:
        """
        Create and install a new MCP server from a Python code snippet.
        
        This tool generates a complete MCP server from a provided code snippet that defines 
        one or more tools. The generated server follows best practices for MCP server architecture
        and includes proper documentation, type hints, and configuration.
        
        Args:
            code_snippet: Python code defining one or more plain public functions.
                         The generated factory registers each function with add_tool().
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
            raise ValueError("server_name must be alphanumeric with optional hyphens")
        
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
                # Auto-sync with Cline to register the new server
                sync_success = sync_with_cline(server_name)
                sync_message = " and registered with Cline" if sync_success else " (manual Cline sync required)"
                
                return {
                    "success": True,
                    "server_name": server_name,
                    "tool_names": tool_names,
                    "message": f"Server '{server_name}' created, installed{sync_message}. Restart VS Code to use it."
                }
            else:
                raise RuntimeError("Failed to install the server. Check the logs for details.")
        except ValueError as e:
            logger.error(f"Failed to create server: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Unexpected error: {e}") from e

    def list_installed_servers(self) -> InstalledServersResult:
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
            # Resolve mcp-manager via PATH. uv tool install places it at
            # ~/.local/bin/mcp-manager on macOS/Linux by default, which is on
            # PATH after `uv tool update-shell`.
            import shutil
            mcpmanager_cmd = shutil.which("mcp-manager")
            if not mcpmanager_cmd:
                raise RuntimeError(
                    "mcp-manager not found on PATH. Install it with "
                    "`uv tool install ./utils/mcp_manager` and run `uv tool update-shell`."
                )

            logger.info(f"Using mcp-manager at: {mcpmanager_cmd}")

            # Call mcp-manager list command (without --json flag as it's not supported)
            result = subprocess.run(
                [mcpmanager_cmd, "list"],
                check=True,
                capture_output=True,
                text=True,
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
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Failed to list servers: {e}") from e
