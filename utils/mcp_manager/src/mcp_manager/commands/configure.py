"""
Implementation of the configure command.

This module provides functions for configuring editor integration
and generating wrapper scripts for local MCP servers.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Union, Any, cast
from datetime import datetime
from rich.console import Console
from jinja2 import Environment, FileSystemLoader
import stat
import subprocess

from mcp_manager.server import (
    Server,
    LocalServer,
    RemoteServer,
    ServerRegistry,
    ServerType,
    get_registry_path,
    get_bin_dir,
    get_vscode_cline_settings_path,
)


console = Console()


def get_jinja_env() -> Environment:
    """Get the Jinja2 environment for templates."""
    # Get the directory containing the templates
    templates_dir = Path(__file__).parent.parent / "templates"
    return Environment(
        loader=FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_wrapper_script(server: LocalServer) -> Path:
    """Generate a wrapper script for a local server."""
    # Check if the server is local
    if not isinstance(server, LocalServer):
        raise ValueError(f"Server '{server.name}' is not a local server")
    
    # Create bin directory if it doesn't exist
    bin_dir = get_bin_dir()
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the wrapper script path
    wrapper_path = bin_dir / f"{server.name}.sh"
    
    # Get the server directory
    server_dir = server.source_dir.parent
    
    # Get the virtual environment activation script path
    if sys.platform == "win32":
        venv_activate = server.venv_dir / "Scripts" / "activate"
    else:
        venv_activate = server.venv_dir / "bin" / "activate"
    
    # Check if the activation script exists
    if not venv_activate.exists():
        raise ValueError(f"Virtual environment activation script not found: {venv_activate}")
    
    # Find the path to mcp-manager executable
    mcp_manager_path = shutil.which("mcp-manager")
    
    # Render the template
    env = get_jinja_env()
    template = env.get_template("wrapper.sh.j2")
    wrapper_content = template.render(
        server=server,
        server_dir=server_dir,
        source_dir=server.source_dir,
        venv_activate=venv_activate,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        mcp_manager_path=mcp_manager_path,
    )
    
    # Write the wrapper script
    wrapper_path.write_text(wrapper_content)
    
    # Make the wrapper script executable
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    console.print(f"Generated wrapper script: [bold]{wrapper_path}[/bold]")
    return wrapper_path


def generate_wrapper_scripts(overwrite: bool = False) -> int:
    """Generate wrapper scripts for all local servers."""
    # Load the server registry
    registry = ServerRegistry.load(get_registry_path())
    
    # Count generated scripts
    count = 0
    
    # Generate wrapper scripts for local servers
    for name, server in registry.servers.items():
        if isinstance(server, LocalServer):
            # Skip if wrapper already exists and overwrite is False
            wrapper_path = get_bin_dir() / f"{name}.sh"
            if wrapper_path.exists() and not overwrite:
                console.print(f"Skipping existing wrapper script: [bold]{wrapper_path}[/bold]")
                continue
            
            try:
                # Generate the wrapper script
                wrapper_path = generate_wrapper_script(server)
                
                # Update the server
                server.wrapper_path = wrapper_path
                registry.update_server(name, server)
                
                count += 1
            except Exception as e:
                console.print(f"[bold red]Error generating wrapper for {name}:[/bold red] {e}")
    
    # Save the registry
    registry.save(get_registry_path())
    
    return count


def configure_vscode_cline(backup: bool = True) -> None:
    """Configure VS Code Cline integration."""
    # Load the server registry
    registry = ServerRegistry.load(get_registry_path())
    
    # Get the VS Code Cline settings path
    settings_path = get_vscode_cline_settings_path()
    settings_dir = settings_path.parent
    
    # Create the settings directory if it doesn't exist
    settings_dir.mkdir(parents=True, exist_ok=True)
    
    # Back up existing settings if they exist
    if settings_path.exists() and backup:
        backup_path = settings_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(settings_path, backup_path)
        console.print(f"Backed up existing settings to: [bold]{backup_path}[/bold]")
    
    # Load existing settings or create new ones
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning:[/yellow] Existing settings file is not valid JSON. Creating new settings.")
            settings = {}
    else:
        settings = {}
    
    # Ensure mcpServers exists
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    
    # Add/update servers
    for name, server in registry.servers.items():
        if isinstance(server, LocalServer):
            # Skip if no wrapper script
            if not server.wrapper_path or not Path(server.wrapper_path).exists():
                # Generate a wrapper script
                wrapper_path = generate_wrapper_script(server)
                server.wrapper_path = wrapper_path
                registry.update_server(name, server)
            
            # Add/update the server
            settings["mcpServers"][name] = {
                "command": "/bin/bash",
                "args": [str(server.wrapper_path)],
                "disabled": server.disabled,
                "autoApprove": server.auto_approve,
            }
        elif isinstance(server, RemoteServer):
            # Add/update the server
            settings["mcpServers"][name] = {
                "url": str(server.url),
                "apiKey": server.api_key,
                "disabled": server.disabled,
                "autoApprove": server.auto_approve,
            }
    
    # Save the registry with updated wrapper paths
    registry.save(get_registry_path())
    
    # Save the settings
    settings_path.write_text(json.dumps(settings, indent=2))
    console.print(f"Updated VS Code Cline settings at: [bold]{settings_path}[/bold]")
    
    # Print instructions
    console.print("\n[bold green]VS Code Cline integration configured successfully![/bold green]")
    console.print("You may need to restart VS Code for the changes to take effect.")


def configure_editor(target: str, backup: bool = True) -> None:
    """Configure editor integration."""
    if target.lower() in ["vscode", "code", "cline"]:
        configure_vscode_cline(backup)
    else:
        raise ValueError(f"Unsupported editor target: {target}")
