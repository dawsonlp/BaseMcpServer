"""
Implementation of the run command.

This module provides functions for running local MCP servers.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List, Union, cast
from rich.console import Console

from mcp_manager.server import (
    Server,
    LocalServer,
    ServerRegistry,
    ServerType,
    get_registry_path,
)


console = Console()


def run_server(name: str, transport: str) -> None:
    """Run a local MCP server."""
    # Load the server registry
    registry = ServerRegistry.load(get_registry_path())
    
    # Check if the server exists
    if name not in registry.servers:
        raise ValueError(f"Server '{name}' not found in registry")
    
    # Get the server
    server = registry.get_server(name)
    
    # Check if the server is local
    if not isinstance(server, LocalServer):
        raise ValueError(f"Server '{name}' is not a local server")
    
    # Check if the server is disabled
    if server.disabled:
        raise ValueError(f"Server '{name}' is disabled")
    
    # Check if the source directory exists
    if not server.source_dir.exists():
        raise ValueError(f"Source directory '{server.source_dir}' does not exist")
    
    # Check if the virtual environment exists
    if not server.venv_dir.exists():
        raise ValueError(f"Virtual environment '{server.venv_dir}' does not exist")
    
    # Validate transport
    if transport not in ["stdio", "sse"]:
        raise ValueError(f"Invalid transport '{transport}', must be 'stdio' or 'sse'")
    
    # Get paths
    if sys.platform == "win32":
        python_path = server.venv_dir / "Scripts" / "python"
        activate_path = server.venv_dir / "Scripts" / "activate"
    else:
        python_path = server.venv_dir / "bin" / "python"
        activate_path = server.venv_dir / "bin" / "activate"
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{server.source_dir}:{env.get('PYTHONPATH', '')}"
    
    # Run the server
    console.print(f"Running MCP server [bold]{name}[/bold] with [bold]{transport}[/bold] transport")
    console.print(f"Press Ctrl+C to stop the server\n")
    
    try:
        # Find the main.py file - check both root and src/ directory
        main_py_path = None
        if (server.source_dir / "main.py").exists():
            main_py_path = server.source_dir / "main.py"
            working_dir = server.source_dir
        elif (server.source_dir / "src" / "main.py").exists():
            main_py_path = server.source_dir / "src" / "main.py"
            working_dir = server.source_dir / "src"
            # Add src to PYTHONPATH for proper imports
            env["PYTHONPATH"] = f"{server.source_dir / 'src'}:{env.get('PYTHONPATH', '')}"
        else:
            raise ValueError(f"Could not find main.py in {server.source_dir} or {server.source_dir / 'src'}")
        
        cmd = [
            str(python_path),
            str(main_py_path),
            transport
        ]
        
        subprocess.run(
            cmd,
            env=env,
            cwd=working_dir,
            check=True,
        )
    except KeyboardInterrupt:
        console.print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error:[/bold red] Server exited with code {e.returncode}")
        if e.stdout:
            console.print(f"[bold]Output:[/bold]\n{e.stdout.decode()}")
        if e.stderr:
            console.print(f"[bold red]Error output:[/bold red]\n{e.stderr.decode()}")
        raise ValueError(f"Server failed with exit code {e.returncode}")
