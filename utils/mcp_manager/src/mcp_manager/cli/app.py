"""
MCP Manager CLI — a flat, minimal command set.

The tool's job: install a local (stdio) MCP server into an isolated environment,
keep one registry as the single source of truth, and sync that registry into
every AI platform's config. Commands map 1:1 to that job.

    mcp-manager install <name> [--source DIR]   install a local server
    mcp-manager sync [--platform P]             push the registry into all platforms
    mcp-manager list                            list registered servers
    mcp-manager show <name>                      details for one server
    mcp-manager remove <name>                    uninstall (registry + platforms + files)
    mcp-manager validate [name]                  validate configuration
    mcp-manager version                          version + paths
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from mcp_manager import __version__
from mcp_manager.cli.commands import removal
from mcp_manager.cli.commands.config import sync_platforms, validate_config
from mcp_manager.cli.commands.info import list_servers, show_status
from mcp_manager.cli.commands.install import install_local
from mcp_manager.cli.common.errors import handle_error
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.core.state import create_directory_structure, get_mcp_home

app = typer.Typer(
    help="🚀 MCP Manager: install local MCP servers and sync them into your AI tools.",
    add_completion=False,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit"),
) -> None:
    """Install and sync Model Context Protocol servers from one registry."""
    if version:
        get_output_manager().console.print(
            f"[bold blue]MCP Manager[/bold blue] version [bold green]{__version__}[/bold green]"
        )
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        get_output_manager().console.print(ctx.get_help())
        raise typer.Exit()
    create_directory_structure()


@app.command("install")
def install(
    name: str = typer.Argument(..., help="Name for the MCP server"),
    source: Optional[Path] = typer.Option(
        None, "--source", "-s",
        help="Server source directory (default: ./servers/<name>)",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Reinstall if it already exists"),
):
    """Install a local MCP server from a directory into an isolated environment."""
    src = source or Path("servers") / name
    install_local(name=name, source=src, force=force, auto_approve=[])


@app.command("sync")
def sync(
    platform: Optional[str] = typer.Option(
        None, "--platform", "-p",
        help="One platform (cline|claude|claude-code|vscode|codex|antigravity). Default: all installed.",
    ),
):
    """Push the server registry into every installed AI platform's config."""
    sync_platforms(platform=platform)


@app.command("list")
def list_cmd(
    format: str = typer.Option("human", "--format", "-f", help="Output format (human|json|yaml)"),
):
    """List registered servers."""
    list_servers(type_filter=None, status_filter="all", format=format)


@app.command("show")
def show(
    name: str = typer.Argument(..., help="Server name"),
    format: str = typer.Option("rich", "--format", "-f", help="Output format (rich|json|yaml)"),
):
    """Show details for one server (including its config file paths)."""
    show_status(name=name, format=format)


@app.command("remove")
def remove(
    name: str = typer.Argument(..., help="Server name to remove"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed"),
):
    """Uninstall a server: remove it from the registry, every platform, and disk."""
    removal.remove_server(name=name, yes=yes, dry_run=dry_run)


@app.command("validate")
def validate(
    name: Optional[str] = typer.Argument(None, help="Server name (validates all if omitted)"),
):
    """Validate server configuration."""
    validate_config(name=name)


@app.command("version")
def version():
    """Show version and key paths."""
    get_output_manager().console.print(
        Panel(
            f"[bold blue]MCP Manager[/bold blue] version [bold green]{__version__}[/bold green]\n\n"
            f"🏠 MCP home: [cyan]{get_mcp_home()}[/cyan]\n"
            f"🐍 Python: [cyan]{sys.executable}[/cyan]\n",
            title="📋 Version Information",
            expand=False,
        )
    )


def main() -> None:
    try:
        app()
    except Exception as e:  # noqa: BLE001 - top-level CLI error boundary
        handle_error(e)
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
