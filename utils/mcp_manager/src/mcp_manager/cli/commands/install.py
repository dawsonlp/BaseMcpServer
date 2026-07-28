"""
Installation of a local MCP server into an isolated uv environment.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from mcp_manager.cli.common.errors import MCPManagerError, handle_error
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.validation import is_valid_server_name
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
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall if exists"),
    auto_approve: List[str] = typer.Option([], "--auto-approve", help="Auto-approve tools (can be used multiple times)"),
):
    """Install a local MCP server from a source directory using uv."""
    try:
        uv_exe = _require_uv()

        if not is_valid_server_name(name):
            raise MCPManagerError(f"Invalid server name: {name}")

        existing_server = state.get_server(name)
        if existing_server and not force:
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
        server_dir.parent.mkdir(parents=True, exist_ok=True)
        previous_dir: Optional[Path] = None
        if server_dir.exists():
            previous_dir = Path(
                tempfile.mkdtemp(prefix=f".{name}-previous-", dir=server_dir.parent)
            )
            previous_dir.rmdir()
            server_dir.rename(previous_dir)
        output.info(f"Installing server '{name}' into an isolated uv environment")

        try:
            server_dir.mkdir(parents=True)
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
                # Resolve to an absolute path. A bare relative name like "worldcontext"
                # gets interpreted by `uv pip install` as a PyPI package name lookup,
                # not a local directory, even when the dir exists in cwd.
                source_abs = source.resolve()
                result = subprocess.run(
                    [
                        uv_exe,
                        "pip",
                        "install",
                        "--prerelease=allow",
                        "--python",
                        str(venv_dir / "bin" / "python"),
                        str(source_abs),
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise MCPManagerError(f"Failed to install package: {result.stderr.strip()}")

                progress.update(task, description="Setting up configuration...", advance=20)
                config_path = server_dir / "config.yaml"
                if config_backup is not None:
                    config_path.write_text(config_backup)
                    output.info("Restored existing config.yaml")
                else:
                    config_example = source_abs / "config.yaml.example"
                    source_config = source_abs / "config.yaml"
                    if config_example.exists():
                        shutil.copy2(config_example, config_path)
                        output.info("Created config.yaml from example")
                        output.warning(
                            f"Please edit {server_dir / 'config.yaml'} with your actual credentials"
                        )
                    elif source_config.exists():
                        shutil.copy2(source_config, config_path)
                        output.info("Copied existing config.yaml from source")

                server = Server(
                    name=name,
                    server_type=ServerType.LOCAL,
                    transport=TransportType.STDIO,
                    source_dir=source_abs,
                    source_type=SourceType.LOCAL,
                    installation_type=InstallationType.UV,
                    venv_dir=venv_dir,
                    auto_approve=auto_approve,
                )

                validation_result = validate_server_config(server)
                if not validation_result.is_valid:
                    output.error("Server configuration validation failed:")
                    for error in validation_result.errors:
                        output.error(f"  • {error.message}")
                    raise MCPManagerError("Server configuration validation failed")

                progress.update(task, description="Registering server...", advance=5)
                if existing_server:
                    state.update_server(server)
                else:
                    state.add_server(server)

                if previous_dir and previous_dir.exists():
                    shutil.rmtree(previous_dir)
                progress.update(task, description="Installed", completed=100)
        except Exception:
            if server_dir.exists():
                shutil.rmtree(server_dir)
            if previous_dir and previous_dir.exists():
                previous_dir.rename(server_dir)
            raise

        output.success(f"Successfully installed local server '{name}'")
        output.info(f"Source: {source}")

    except Exception as e:
        handle_error(e, "Failed to install local server")


if __name__ == "__main__":
    app()
