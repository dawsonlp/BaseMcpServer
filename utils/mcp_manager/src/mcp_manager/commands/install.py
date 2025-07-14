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
    ServerRegistry,
    get_mcp_home,
    get_server_dir,
    get_registry_path,
)


console = Console()


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


def install_local_server(name: str, source_dir: Path, port: Optional[int] = None, force: bool = False) -> None:
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
            # Remove from registry
            registry.remove_server(name)
            registry.save(get_registry_path())
        else:
            raise ValueError(f"Server with name '{name}' already exists")
    
    # Create server directory
    server_dir = get_server_dir(name)
    if server_dir.exists():
        if force:
            # Remove existing server directory
            shutil.rmtree(server_dir)
        else:
            raise ValueError(f"Server directory already exists: {server_dir}")
    
    server_dir.mkdir(parents=True, exist_ok=True)
    
    # Detect server type based on port
    server_type = ServerType.LOCAL_SSE if port else ServerType.LOCAL_STDIO
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Create proper structure for the server - fixed to avoid nested src/src and use actual copies
        task = progress.add_task(f"Copying source files...", total=1)
        
        # Determine correct structure based on source dir
        server_code_dir = server_dir / "code"
        server_code_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if the source directory has a src subdirectory
        source_src_dir = source_dir / "src"
        
        if source_src_dir.exists() and source_src_dir.is_dir():
            # Case 1: Source has /src subdirectory - copy src's contents to code/
            console.print(f"Copying source files from {source_src_dir}")
            for item in source_src_dir.iterdir():
                if item.is_dir():
                    console.print(f"Copying directory: {item.name}")
                    # Use symlinks=False to ensure actual file copies, not symlinks
                    shutil.copytree(item, server_code_dir / item.name, 
                                   dirs_exist_ok=True, symlinks=False)
                else:
                    console.print(f"Copying file: {item.name}")
                    shutil.copy2(item, server_code_dir / item.name)
        else:
            # Case 2: Source is directly the code - copy source_dir contents to code/
            console.print(f"Copying source files from {source_dir}")
            for item in source_dir.iterdir():
                # Skip setup/config files that shouldn't be in the code directory
                if item.name in ['.env', '.env.example', 'docker', 'run.sh', 'setup.sh', 
                               'README.md', 'readme_fastmcp.md', 'requirements.txt']:
                    continue
                    
                if item.is_dir():
                    console.print(f"Copying directory: {item.name}")
                    # Use symlinks=False to ensure actual file copies, not symlinks
                    shutil.copytree(item, server_code_dir / item.name, 
                                   dirs_exist_ok=True, symlinks=False)
                else:
                    console.print(f"Copying file: {item.name}")
                    shutil.copy2(item, server_code_dir / item.name)
            
        progress.update(task, advance=1)
        
        # Create a virtual environment
        task = progress.add_task(f"Creating virtual environment...", total=1)
        venv_dir = server_dir / ".venv"
        virtualenv.cli_run([str(venv_dir)])
        progress.update(task, advance=1)
        
        # Find requirements file
        task = progress.add_task(f"Finding requirements file...", total=1)
        requirements_file = find_requirements_file(source_dir)
        progress.update(task, advance=1)
        
        # Install requirements if found
        if requirements_file:
            task = progress.add_task(f"Installing requirements from {requirements_file}...", total=1)
            install_requirements(venv_dir, requirements_file)
            progress.update(task, advance=1)
        else:
            console.print("[yellow]Warning:[/yellow] No requirements.txt file found.")
        
        # Register the server
        task = progress.add_task(f"Registering server...", total=1)
        registry = ServerRegistry.load(get_registry_path())
        
        server = LocalServer(
            name=name,
            server_type=server_type,
            source_dir=server_code_dir,  # Updated to use our code directory
            venv_dir=venv_dir,
            requirements_file=requirements_file,
            port=port,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        registry.add_server(server)
        registry.save(get_registry_path())
        progress.update(task, advance=1)
        
        # Generate wrapper script
        task = progress.add_task(f"Generating wrapper script...", total=1)
        from mcp_manager.commands.configure import generate_wrapper_script
        wrapper_path = generate_wrapper_script(server)
        
        # Update server with wrapper path
        registry = ServerRegistry.load(get_registry_path())
        server = registry.get_server(name)
        if isinstance(server, LocalServer):
            server.wrapper_path = wrapper_path
            registry.update_server(name, server)
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
