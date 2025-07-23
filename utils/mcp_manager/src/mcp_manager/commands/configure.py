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
    InstallationType,
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
            if server.installation_type == InstallationType.PIPX:
                if not server.executable_name:
                    console.print(f"[bold red]Error:[/bold red] Executable name not set for pipx-installed server '{name}'")
                    continue
                
                if not server.venv_dir:
                    console.print(f"[bold red]Error:[/bold red] venv_dir not set for pipx-installed server '{name}'")
                    continue

                executable_path = server.venv_dir / "bin" / server.executable_name
                if not executable_path.exists():
                    console.print(f"[bold red]Error:[/bold red] Executable '{executable_path}' not found for server '{name}'")
                    continue

                settings["mcpServers"][name] = {
                    "command": str(executable_path),
                    "args": ["stdio"],
                    "disabled": server.disabled,
                    "autoApprove": server.auto_approve,
                }
            else:  # Default to VENV
                if not server.venv_dir:
                    console.print(f"[bold red]Error:[/bold red] venv_dir not set for venv-installed server '{name}'")
                    continue

                if sys.platform == "win32":
                    python_executable = server.venv_dir / "Scripts" / "python.exe"
                else:
                    python_executable = server.venv_dir / "bin" / "python"

                if not python_executable.exists():
                    console.print(f"[bold red]Error:[/bold red] Python executable not found for server '{name}' at '{python_executable}'")
                    continue

                main_script_path = server.source_dir / "main.py"
                if not main_script_path.exists():
                    console.print(f"[bold red]Error:[/bold red] main.py not found for server '{name}' at '{main_script_path}'")
                    continue

                settings["mcpServers"][name] = {
                    "command": str(python_executable),
                    "args": [str(main_script_path), "stdio"],
                    "options": {
                        "cwd": str(server.source_dir),
                        "env": {"PYTHONPATH": str(server.source_dir)},
                    },
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

    # Save the registry
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
