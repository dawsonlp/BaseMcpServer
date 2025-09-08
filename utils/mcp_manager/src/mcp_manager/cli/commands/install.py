"""
Installation commands for MCP Manager 3.0.

Handles installation of local and remote MCP servers with various options.
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from mcp_manager.core.models import Server, ServerType, TransportType, InstallationType, SourceType
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.validation import validate_server_config
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError
from mcp_manager.cli.common.validation import is_valid_server_name, CLIValidator


app = typer.Typer(help="Install MCP servers")
output = get_output_manager()
validator = CLIValidator()
state = get_state_manager()


@app.command("local")
def install_local(
    name: str = typer.Argument(..., help="Server name"),
    source: Path = typer.Option(..., "--source", "-s", help="Path to server source directory"),
    transport: TransportType = typer.Option(TransportType.STDIO, "--transport", "-t", help="Transport protocol"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port for SSE transport"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if exists"),
    pipx: bool = typer.Option(False, "--pipx", help="Install as standalone application (requires pyproject.toml)"),
    auto_approve: List[str] = typer.Option([], "--auto-approve", help="Auto-approve tools (can be used multiple times)"),
):
    """Install a local MCP server from source directory."""
    try:
        # Validate server name
        if not is_valid_server_name(name):
            raise MCPManagerError(f"Invalid server name: {name}")
        
        # Check if server already exists
        if state.get_server(name) and not force:
            raise MCPManagerError(f"Server '{name}' already exists. Use --force to reinstall.")
        
        # Validate source directory
        if not source.exists() or not source.is_dir():
            raise MCPManagerError(f"Source directory does not exist: {source}")
        
        # For pipx installation, check for pyproject.toml
        if pipx and not (source / "pyproject.toml").exists():
            raise MCPManagerError("A pyproject.toml file is required for pipx-style installation.")
        
        # Set installation type based on pipx flag
        installation_type = InstallationType.PIPX if pipx else InstallationType.VENV
        
        # Create server directory
        from mcp_manager.core.state import get_server_dir
        server_dir = get_server_dir(name)
        
        # Handle existing server directory
        if server_dir.exists():
            if force:
                import shutil
                # Backup existing config if it exists
                config_backup = None
                config_path = server_dir / "config.yaml"
                if config_path.exists():
                    config_backup = config_path.read_text()
                    output.info("Backing up existing config.yaml")
                shutil.rmtree(server_dir)
            elif not force:
                raise MCPManagerError(f"Server directory already exists: {server_dir}")
        
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Install server with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
        ) as progress:
            
            if pipx:
                # Pipx-style installation
                task = progress.add_task("Installing as standalone application...", total=100)
                
                # Step 1: Create virtual environment (25%)
                progress.update(task, description="Creating virtual environment...", advance=25)
                venv_dir = server_dir / ".venv"
                
                import subprocess
                import os
                import virtualenv
                
                # Create environment and remove PIPX_DEFAULT_PYTHON
                env = os.environ.copy()
                env.pop("PIPX_DEFAULT_PYTHON", None)
                
                # Use virtualenv for better compatibility
                virtualenv.cli_run([str(venv_dir)])
                
                # Step 2: Install package (50%)
                progress.update(task, description="Installing package...", advance=50)
                python_exe = venv_dir / "bin" / "python"
                pip_exe = venv_dir / "bin" / "pip"
                
                result = subprocess.run(
                    [str(pip_exe), "install", "-e", str(source)],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if result.returncode != 0:
                    raise MCPManagerError(f"Failed to install package: {result.stderr}")
                
                # Step 3: Handle config (25%)
                progress.update(task, description="Setting up configuration...", advance=25)
                
                # Restore or create config
                config_path = server_dir / "config.yaml"
                if 'config_backup' in locals() and config_backup:
                    config_path.write_text(config_backup)
                    output.info("Restored existing config.yaml")
                else:
                    # Create from example if available
                    config_example = source / "config.yaml.example"
                    if config_example.exists():
                        import shutil
                        shutil.copy2(config_example, config_path)
                        output.info("Created config.yaml from example")
                        output.warning(f"Please edit {config_path} with your actual credentials")
                    
                    # Also copy existing config.yaml from source if present
                    source_config = source / "config.yaml"
                    if source_config.exists() and not config_path.exists():
                        import shutil
                        shutil.copy2(source_config, config_path)
                        output.info("Copied existing config.yaml from source")
                
                # Create server configuration
                package_name = source.name
                executable_name = name
                
                server = Server(
                    name=name,
                    server_type=ServerType.LOCAL,
                    transport=transport,
                    source_dir=source.resolve(),
                    source_type=SourceType.LOCAL,
                    installation_type=InstallationType.PIPX,
                    venv_dir=venv_dir,
                    port=port if transport == TransportType.SSE else None,
                    auto_approve=auto_approve
                )
                
            else:
                # Standard venv installation
                task = progress.add_task("Installing server...", total=100)
                
                # Step 1: Copy source files (25%)
                progress.update(task, description="Copying source files...", advance=25)
                server_code_dir = server_dir / "code"
                server_code_dir.mkdir(parents=True, exist_ok=True)
                source_src_dir = source / "src"
                
                import shutil
                if source_src_dir.exists() and source_src_dir.is_dir():
                    shutil.copytree(source_src_dir, server_code_dir, dirs_exist_ok=True, symlinks=False)
                else:
                    shutil.copytree(source, server_code_dir, dirs_exist_ok=True, symlinks=False)
                
                # Step 2: Create virtual environment (25%)
                progress.update(task, description="Creating virtual environment...", advance=25)
                venv_dir = server_dir / ".venv"
                
                import subprocess
                result = subprocess.run(
                    ["python", "-m", "venv", str(venv_dir)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise MCPManagerError(f"Failed to create virtual environment: {result.stderr}")
                
                # Step 3: Install dependencies (25%)
                progress.update(task, description="Installing dependencies...", advance=25)
                
                # Find requirements file
                requirements_file = None
                for req_file in ["requirements.txt", "pyproject.toml"]:
                    req_path = source / req_file
                    if req_path.exists():
                        requirements_file = req_path
                        break
                
                if requirements_file:
                    python_exe = venv_dir / "bin" / "python"
                    if requirements_file.name == "requirements.txt":
                        cmd = [str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)]
                    else:
                        cmd = [str(python_exe), "-m", "pip", "install", "-e", str(source)]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise MCPManagerError(f"Failed to install dependencies: {result.stderr}")
                else:
                    output.warning("No requirements.txt or pyproject.toml file found")
                
                # Create server configuration
                server = Server(
                    name=name,
                    server_type=ServerType.LOCAL,
                    transport=transport,
                    source_dir=server_code_dir,
                    source_type=SourceType.LOCAL,
                    installation_type=InstallationType.VENV,
                    venv_dir=venv_dir,
                    requirements_file=requirements_file,
                    port=port if transport == TransportType.SSE else None,
                    auto_approve=auto_approve
                )
            
            # Step 4: Register server (remaining percentage)
            progress.update(task, description="Registering server...", completed=100)
            
            # Validate configuration
            validation_result = validate_server_config(server)
            if not validation_result.is_valid:
                output.error("Server configuration validation failed:")
                for error in validation_result.errors:
                    output.error(f"  • {error.message}")
                raise typer.Exit(1)
            
            # Remove existing server if force is enabled
            if force and state.get_server(name):
                state.remove_server(name)
            
            # Add the server
            state.add_server(server)
        
        output.success(f"Successfully installed local server '{name}'")
        output.info(f"Source: {source}")
        output.info(f"Transport: {transport.value}")
        if port:
            output.info(f"Port: {port}")
        
    except Exception as e:
        handle_error(e, "Failed to install local server")


@app.command("remote")
def install_remote(
    name: str = typer.Argument(..., help="Server name"),
    url: str = typer.Option(..., "--url", "-u", help="Server URL"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for authentication"),
    transport: TransportType = typer.Option(TransportType.SSE, "--transport", "-t", help="Transport protocol"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if exists"),
    auto_approve: List[str] = typer.Option([], "--auto-approve", help="Auto-approve tools (can be used multiple times)"),
):
    """Install a remote MCP server."""
    try:
        # Validate server name
        if not is_valid_server_name(name):
            raise MCPManagerError(f"Invalid server name: {name}")
        
        # Check if server already exists
        if state.get_server(name) and not force:
            raise MCPManagerError(f"Server '{name}' already exists. Use --force to reinstall.")
        
        # Create server configuration
        server = Server(
            name=name,
            server_type=ServerType.REMOTE,
            transport=transport,
            url=url,
            api_key=api_key,
            auto_approve=auto_approve
        )
        
        # Validate configuration
        validation_result = validate_server_config(server)
        if not validation_result.is_valid:
            output.error("Server configuration validation failed:")
            for error in validation_result.errors:
                output.error(f"  • {error.message}")
            raise typer.Exit(1)
        
        # Register server
        if force and state.get_server(name):
            state.remove_server(name)
        
        state.add_server(server)
        
        output.success(f"Successfully installed remote server '{name}'")
        output.info(f"URL: {url}")
        output.info(f"Transport: {transport.value}")
        
    except Exception as e:
        handle_error(e, "Failed to install remote server")


@app.command("from-template")
def install_from_template(
    name: str = typer.Argument(..., help="Server name"),
    template: str = typer.Option(..., "--template", "-t", help="Template name or path"),
    destination: Optional[Path] = typer.Option(None, "--dest", "-d", help="Destination directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if exists"),
):
    """Install a server from a template."""
    try:
        # This would integrate with the template system
        output.info("Template installation not yet implemented")
        output.info("This feature will be available in a future version")
        
    except Exception as e:
        handle_error(e, "Failed to install from template")


@app.command("list-templates")
def list_templates():
    """List available server templates."""
    try:
        output.info("Available templates:")
        output.info("• basic-server - Basic MCP server template")
        output.info("• fastapi-server - FastAPI-based MCP server")
        output.info("• tool-server - Tool-focused MCP server")
        output.info("\nTemplate system not yet fully implemented")
        
    except Exception as e:
        handle_error(e, "Failed to list templates")


if __name__ == "__main__":
    app()
