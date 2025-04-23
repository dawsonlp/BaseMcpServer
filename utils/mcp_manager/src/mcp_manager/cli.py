"""
Main CLI entry point for MCP Manager.

This module defines the command-line interface and imports all subcommands.
"""

import typer
from pathlib import Path
from typing import Optional, List
from enum import Enum
import sys
import rich
from rich.console import Console
from rich.panel import Panel

from mcp_manager import __version__
from mcp_manager.server import create_directory_structure, get_mcp_home


# Create console for rich output
console = Console()


# Define transport enum
class Transport(str, Enum):
    """Transport protocols for MCP servers."""
    STDIO = "stdio"
    SSE = "sse"


# Create main app and subcommands
app = typer.Typer(
    help="MCP Manager: A comprehensive manager for Model Context Protocol (MCP) servers.",
    add_completion=False,
)
install_app = typer.Typer(help="Install MCP servers from different sources.")
app.add_typer(install_app, name="install")


@app.callback()
def callback(
    version: bool = typer.Option(
        False, "--version", "-V", help="Show the version and exit."
    ),
) -> None:
    """
    MCP Manager: A comprehensive manager for Model Context Protocol (MCP) servers.
    
    This tool helps you install, configure, and run MCP servers.
    """
    if version:
        console.print(f"MCP Manager version: [bold]{__version__}[/bold]")
        raise typer.Exit()
    
    # Create directory structure if it doesn't exist
    create_directory_structure()


@install_app.command("local")
def install_local(
    name: str = typer.Argument(..., help="Name for the MCP server"),
    source: Path = typer.Option(
        ..., "--source", "-s", help="Source directory containing the MCP server"
    ),
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Port for SSE transport (if needed)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force installation, overwriting existing server"
    ),
):
    """Install a local MCP server from a directory."""
    from mcp_manager.commands.install import install_local_server
    
    source = source.absolute()
    if not source.exists() or not source.is_dir():
        console.print(f"[bold red]Error:[/bold red] Source directory '{source}' does not exist.")
        raise typer.Exit(1)
    
    try:
        install_local_server(name, source, port, force)
        console.print(f"[bold green]Success:[/bold green] MCP server '{name}' installed.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@install_app.command("git")
def install_git(
    name: str = typer.Argument(..., help="Name for the MCP server"),
    repo: str = typer.Option(..., "--repo", "-r", help="Git repository URL"),
    path: str = typer.Option(
        ".", "--path", "-p", help="Path within repository to the MCP server"
    ),
    branch: str = typer.Option(
        "main", "--branch", "-b", help="Git branch to clone"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force installation, overwriting existing server"
    ),
):
    """Install a local MCP server from a Git repository."""
    from mcp_manager.commands.install import install_git_server
    
    try:
        install_git_server(name, repo, path, branch, force)
        console.print(f"[bold green]Success:[/bold green] MCP server '{name}' installed from Git.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def add(
    name: str = typer.Argument(..., help="Name for the remote MCP server"),
    url: str = typer.Option(..., "--url", "-u", help="URL of the remote MCP server"),
    api_key: str = typer.Option(..., "--api-key", "-k", help="API key for authentication"),
):
    """Add a remote MCP server."""
    from mcp_manager.commands.add import add_remote_server
    
    try:
        add_remote_server(name, url, api_key)
        console.print(f"[bold green]Success:[/bold green] Remote MCP server '{name}' added.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def list(
    local: bool = typer.Option(False, "--local", help="List only local servers"),
    remote: bool = typer.Option(False, "--remote", help="List only remote servers"),
):
    """List all configured MCP servers."""
    from mcp_manager.commands.list import list_servers
    
    try:
        list_servers(local_only=local, remote_only=remote)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def run(
    name: str = typer.Argument(..., help="Name of the MCP server to run"),
    transport: Transport = typer.Option(
        Transport.STDIO, "--transport", "-t", help="Transport protocol to use"
    ),
):
    """Run a local MCP server."""
    from mcp_manager.commands.run import run_server
    
    try:
        run_server(name, transport.value)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def configure(
    target: str = typer.Argument(..., help="Target to configure (vscode, cline)"),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create a backup of existing configuration"
    ),
):
    """Configure editor integration."""
    from mcp_manager.commands.configure import configure_editor
    
    try:
        configure_editor(target, backup)
        console.print(f"[bold green]Success:[/bold green] Editor integration for '{target}' configured.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def generate_wrappers(
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing wrapper scripts"
    ),
):
    """Generate wrapper scripts for all local servers."""
    from mcp_manager.commands.configure import generate_wrapper_scripts
    
    try:
        count = generate_wrapper_scripts(overwrite)
        console.print(f"[bold green]Success:[/bold green] Generated {count} wrapper scripts.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def info():
    """Show information about the MCP Manager installation."""
    mcp_home = get_mcp_home()
    
    console.print(Panel(
        f"[bold]MCP Manager[/bold] version {__version__}\n\n"
        f"MCP home directory: [cyan]{mcp_home}[/cyan]\n"
        f"Python executable: [cyan]{sys.executable}[/cyan]\n",
        title="MCP Manager Info",
        expand=False
    ))


if __name__ == "__main__":
    app()
