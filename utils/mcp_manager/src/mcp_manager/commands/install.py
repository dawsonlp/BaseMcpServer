"""
Implementation of the install commands.

This module provides functions for installing MCP servers from
different sources (local directories and Git repositories).
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
import virtualenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

from mcp_manager.server import (
    LocalServer,
    ServerType,
    InstallationType,
    ServerRegistry,
    get_mcp_home,
    get_server_dir,
    get_registry_path,
)


console = Console()


def create_config_from_example(server_dir: Path, source_dir: Path) -> None:
    """Create a config.yaml file from config.yaml.example if it doesn't exist."""
    config_example_path = source_dir / "config.yaml.example"
    config_path = server_dir / "config.yaml"
    
    if config_example_path.exists() and not config_path.exists():
        shutil.copy2(config_example_path, config_path)
        console.print(f"Created config.yaml from config.yaml.example")
        console.print(f"[yellow]Please edit {config_path} with your actual credentials[/yellow]")


def find_requirements_file(source_dir: Path) -> Optional[Path]:
    """Find a requirements.txt file in the source directory or its parent."""
    # Check for requirements.txt in the source directory
    requirements = source_dir / "requirements.txt"
    if requirements.exists():
        return requirements
    
    # Check for requirements.txt in parent directory (e.g., for BaseMcpServer/example)
    parent_requirements = source_dir.parent / "requirements.txt"
    if parent_requirements.exists():
        return parent_requirements
    
    # Check for requirements-base.txt in parent directory
    base_requirements = source_dir.parent.parent / "requirements-base.txt"
    if base_requirements.exists():
        return base_requirements
    
    return None


def install_requirements(venv_dir: Path, requirements_file: Path) -> None:
    """Install requirements from a requirements.txt file."""
    # Get path to pip in the virtual environment
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip"
    else:
        pip_path = venv_dir / "bin" / "pip"
    
    # Install requirements
    console.print(f"Installing requirements from {requirements_file}")
    subprocess.run(
        [str(pip_path), "install", "-r", str(requirements_file)],
        check=True,
        capture_output=True,
    )


def install_local_server(
    name: str,
    source_dir: Path,
    port: Optional[int] = None,
    force: bool = False,
    pipx: bool = False,
) -> None:
    """Install a local MCP server from a directory."""
    # Validate server name
    if not name.isalnum() and not (name.replace("-", "").isalnum() and "-" in name):
        raise ValueError(
            f"Server name must be alphanumeric or contain only hyphens, got '{name}'"
        )

    # Check if server exists in registry
    registry = ServerRegistry.load(get_registry_path())
    if name in registry.servers:
        if force:
            console.print(f"[yellow]Warning:[/yellow] Overwriting existing server: {name}")
            # TODO: Add uninstall logic here before reinstalling
            registry.remove_server(name)
            registry.save(get_registry_path())
        else:
            raise ValueError(f"Server with name '{name}' already exists")

    if pipx:
        # Install using a dedicated virtual environment to simulate pipx
        console.print(f"Installing server '{name}' as a standalone application...")
        server_dir = get_server_dir(name)
        
        # Backup existing config if it exists and we're forcing
        config_backup = None
        if server_dir.exists() and force:
            config_path = server_dir / "config.yaml"
            if config_path.exists():
                # Read the existing config to restore it later
                with open(config_path, 'r') as f:
                    config_backup = f.read()
                console.print(f"[yellow]Backing up existing config.yaml[/yellow]")
            shutil.rmtree(server_dir)
        elif server_dir.exists():
            raise ValueError(f"Server directory already exists: {server_dir}")
        
        server_dir.mkdir(parents=True, exist_ok=True)

        try:
            if not (source_dir / "pyproject.toml").exists():
                raise FileNotFoundError("A pyproject.toml file is required for pipx-style installation.")

            # Create a copy of the environment and remove PIPX_DEFAULT_PYTHON
            env = os.environ.copy()
            env.pop("PIPX_DEFAULT_PYTHON", None)

            # Create a virtual environment
            venv_dir = server_dir / ".venv"
            virtualenv.cli_run([str(venv_dir)])

            # Install the package in editable mode
            pip_path = venv_dir / "bin" / "pip"
            subprocess.run(
                [str(pip_path), "install", "-e", str(source_dir)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            # TODO: A more robust way to get package and executable name
            package_name = source_dir.name
            executable_name = name

            # Restore backed-up config if we have one, otherwise create from example
            config_path = server_dir / "config.yaml"
            if config_backup:
                with open(config_path, 'w') as f:
                    f.write(config_backup)
                console.print(f"[green]Restored existing config.yaml[/green]")
            else:
                # Create config file from example if it doesn't exist
                create_config_from_example(server_dir, source_dir)
                
                # Also copy the config.yaml if it exists in source (and no config exists yet)
                source_config_path = source_dir / "config.yaml"
                if source_config_path.exists() and not config_path.exists():
                    shutil.copy2(source_config_path, config_path)
                    console.print(f"Copied existing config.yaml from source")

            console.print(f"Server '{name}' installed successfully as a standalone application.")
            
            # Register the server
            server = LocalServer(
                name=name,
                server_type=ServerType.LOCAL_STDIO,
                installation_type=InstallationType.PIPX,
                source_dir=source_dir,
                venv_dir=venv_dir,
                package_name=package_name,
                executable_name=executable_name,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            registry.add_server(server)
            registry.save(get_registry_path())
            console.print(f"Server '{name}' registered with pipx installation type.")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            console.print(f"[bold red]Error installing as a standalone application:[/bold red] {e}")
            if isinstance(e, subprocess.CalledProcessError):
                console.print(e.stderr)
            raise
    else:
        # Install using virtual environment (venv)
        server_dir = get_server_dir(name)
        if server_dir.exists():
            if force:
                shutil.rmtree(server_dir)
            else:
                raise ValueError(f"Server directory already exists: {server_dir}")
        server_dir.mkdir(parents=True, exist_ok=True)

        server_type = ServerType.LOCAL_SSE if port else ServerType.LOCAL_STDIO

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Copying source files...", total=1)
            server_code_dir = server_dir / "code"
            server_code_dir.mkdir(parents=True, exist_ok=True)
            source_src_dir = source_dir / "src"

            if source_src_dir.exists() and source_src_dir.is_dir():
                shutil.copytree(source_src_dir, server_code_dir, dirs_exist_ok=True, symlinks=False)
            else:
                shutil.copytree(source_dir, server_code_dir, dirs_exist_ok=True, symlinks=False)
            progress.update(task, advance=1)

            task = progress.add_task(f"Creating virtual environment...", total=1)
            venv_dir = server_dir / ".venv"
            virtualenv.cli_run([str(venv_dir)])
            progress.update(task, advance=1)

            requirements_file = find_requirements_file(source_dir)
            if requirements_file:
                task = progress.add_task(f"Installing requirements...", total=1)
                install_requirements(venv_dir, requirements_file)
                progress.update(task, advance=1)
            else:
                console.print("[yellow]Warning:[/yellow] No requirements.txt file found.")

            task = progress.add_task(f"Registering server...", total=1)
            server = LocalServer(
                name=name,
                server_type=server_type,
                installation_type=InstallationType.VENV,
                source_dir=server_code_dir,
                venv_dir=venv_dir,
                requirements_file=requirements_file,
                port=port,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            registry.add_server(server)
            registry.save(get_registry_path())
            progress.update(task, advance=1)


def install_git_server(name: str, repo_url: str, repo_path: str = ".", branch: str = "main", force: bool = False) -> None:
    """Install a local MCP server from a Git repository."""
    # Validate server name
    if not name.isalnum() and not (name.replace("-", "").isalnum() and "-" in name):
        raise ValueError(
            f"Server name must be alphanumeric or contain only hyphens, got '{name}'"
        )
    
    # Create temporary directory for the Git clone
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Clone the repository
            task = progress.add_task(f"Cloning repository {repo_url}...", total=1)
            subprocess.run(
                ["git", "clone", "--branch", branch, "--depth", "1", repo_url, str(temp_path)],
                check=True,
                capture_output=True,
            )
            progress.update(task, advance=1)
            
            # Get the source directory
            source_dir = temp_path / repo_path
            if not source_dir.exists() or not source_dir.is_dir():
                raise ValueError(f"Source directory '{repo_path}' not found in repository")
            
            # Install the server
            install_local_server(name, source_dir, None, force)
