"""
Installation commands for MCP Manager.

Handles installation of local and remote MCP servers with various options.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from mcp_manager.cli.common.errors import MCPManagerError, handle_error
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.validation import CLIValidator, is_valid_server_name
from mcp_manager.core.models import (
    InstallationType,
    Server,
    ServerType,
    SourceType,
    TransportType,
)
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.validation import validate_server_config


app = typer.Typer(help="Install MCP servers")
output = get_output_manager()
validator = CLIValidator()
state = get_state_manager()


def _require_uv() -> str:
    """Return the path to the uv executable, or raise if unavailable."""
    uv_path = shutil.which("uv")
    if not uv_path:
        raise MCPManagerError(
            "uv is required but was not found on PATH. Install it with "
            "`curl -LsSf https://astral.sh/uv/install.sh | sh` and ensure "
            "`uv tool update-shell` has been run."
        )
    return uv_path


@app.command("local")
def install_local(
    name: str = typer.Argument(..., help="Server name"),
    source: Path = typer.Option(..., "--source", "-s", help="Path to server source directory"),
    transport: TransportType = typer.Option(TransportType.STDIO, "--transport", "-t", help="Transport protocol"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port for SSE transport"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if exists"),
    auto_approve: List[str] = typer.Option([], "--auto-approve", help="Auto-approve tools (can be used multiple times)"),
):
    """Install a local MCP server from a source directory using uv."""
    try:
        uv_exe = _require_uv()

        if not is_valid_server_name(name):
            raise MCPManagerError(f"Invalid server name: {name}")

        if state.get_server(name) and not force:
            raise MCPManagerError(f"Server '{name}' already exists. Use --force to reinstall.")

        if not source.exists() or not source.is_dir():
            raise MCPManagerError(f"Source directory does not exist: {source}")

        if not (source / "pyproject.toml").exists():
            raise MCPManagerError(
                f"A pyproject.toml file is required at {source}. "
                "MCP Manager installs servers as isolated packages with uv."
            )

        from mcp_manager.core.state import get_server_dir
        server_dir = get_server_dir(name)

        config_backup: Optional[str] = None
        if server_dir.exists():
            if not force:
                raise MCPManagerError(f"Server directory already exists: {server_dir}")
            config_path = server_dir / "config.yaml"
            if config_path.exists():
                config_backup = config_path.read_text()
                output.info("Backing up existing config.yaml")
            shutil.rmtree(server_dir)

        server_dir.mkdir(parents=True, exist_ok=True)
        output.info(f"Installing server '{name}' into an isolated uv environment")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Installing package into isolated environment...", total=100)

            venv_dir = server_dir / ".venv"
            progress.update(task, description="Creating virtual environment with uv...", advance=25)
            result = subprocess.run(
                [uv_exe, "venv", str(venv_dir)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise MCPManagerError(f"Failed to create virtual environment: {result.stderr.strip()}")

            progress.update(task, description="Installing package with uv pip...", advance=50)
            result = subprocess.run(
                [uv_exe, "pip", "install", "--python", str(venv_dir / "bin" / "python"), str(source)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise MCPManagerError(f"Failed to install package: {result.stderr.strip()}")

            progress.update(task, description="Setting up configuration...", advance=25)
            config_path = server_dir / "config.yaml"
            if config_backup:
                config_path.write_text(config_backup)
                output.info("Restored existing config.yaml")
            else:
                config_example = source / "config.yaml.example"
                source_config = source / "config.yaml"
                if config_example.exists():
                    shutil.copy2(config_example, config_path)
                    output.info("Created config.yaml from example")
                    output.warning(f"Please edit {config_path} with your actual credentials")
                elif source_config.exists():
                    shutil.copy2(source_config, config_path)
                    output.info("Copied existing config.yaml from source")

            server = Server(
                name=name,
                server_type=ServerType.LOCAL,
                transport=transport,
                source_dir=source.resolve(),
                source_type=SourceType.LOCAL,
                installation_type=InstallationType.UV,
                venv_dir=venv_dir,
                port=port if transport == TransportType.SSE else None,
                auto_approve=auto_approve,
            )

            progress.update(task, description="Registering server...", completed=100)

            validation_result = validate_server_config(server)
            if not validation_result.is_valid:
                output.error("Server configuration validation failed:")
                for error in validation_result.errors:
                    output.error(f"  • {error.message}")
                raise typer.Exit(1)

            if force and state.get_server(name):
                state.remove_server(name)

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
        if not is_valid_server_name(name):
            raise MCPManagerError(f"Invalid server name: {name}")

        if state.get_server(name) and not force:
            raise MCPManagerError(f"Server '{name}' already exists. Use --force to reinstall.")

        server = Server(
            name=name,
            server_type=ServerType.REMOTE,
            transport=transport,
            url=url,
            api_key=api_key,
            auto_approve=auto_approve,
        )

        validation_result = validate_server_config(server)
        if not validation_result.is_valid:
            output.error("Server configuration validation failed:")
            for error in validation_result.errors:
                output.error(f"  • {error.message}")
            raise typer.Exit(1)

        if force and state.get_server(name):
            state.remove_server(name)

        state.add_server(server)

        output.success(f"Successfully installed remote server '{name}'")
        output.info(f"URL: {url}")
        output.info(f"Transport: {transport.value}")

    except Exception as e:
        handle_error(e, "Failed to install remote server")


if __name__ == "__main__":
    app()
