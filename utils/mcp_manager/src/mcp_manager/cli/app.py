"""
Main CLI application for MCP Manager.

This module contains the complete CLI application logic using the new modular command structure.
Provides a comprehensive, user-friendly interface for managing MCP servers.
"""

import typer
from pathlib import Path
from typing import Optional
import sys
from rich.panel import Panel

from mcp_manager import __version__
from mcp_manager.core.state import create_directory_structure, get_mcp_home
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error

# Import all command modules
from mcp_manager.cli.commands.install import (
    install_local,
    install_remote,
    install_from_template,
    list_templates
)
from mcp_manager.cli.commands.lifecycle import (
    start_server,
    start_server_impl,
    stop_server,
    restart_server,
    show_logs,
    show_server_status,
    kill_server
)
from mcp_manager.cli.commands.info import (
    list_servers,
    show_status,
    show_system_info,
    show_logs,
    show_config
)
from mcp_manager.cli.commands.config import (
    edit_server_config,
    validate_config,
    sync_platforms,
    export_config,
    import_config,
    backup_config,
    configure_cline,
    configure_claude_desktop
)
from mcp_manager.cli.commands.diagnostics import (
    health_check,
    monitor_health,
    troubleshoot_server,
    system_diagnostics
)
from mcp_manager.cli.commands.advanced import (
    cleanup_system,
    reset_system,
    migrate_data,
    analyze_performance,
    export_diagnostics
)


# Create main app
app = typer.Typer(
    help="🚀 MCP Manager: Comprehensive manager for Model Context Protocol (MCP) servers",
    add_completion=False,
    rich_markup_mode="rich"
)

# Create command groups
install_app = typer.Typer(
    help="📦 Install MCP servers from various sources",
    rich_markup_mode="rich"
)
lifecycle_app = typer.Typer(
    help="🔄 Manage server lifecycle (start/stop/restart)",
    rich_markup_mode="rich"
)
info_app = typer.Typer(
    help="📋 View server information and status",
    rich_markup_mode="rich"
)
config_app = typer.Typer(
    help="⚙️  Configure platforms and manage settings",
    rich_markup_mode="rich"
)
diag_app = typer.Typer(
    help="🏥 Health checks and diagnostics",
    rich_markup_mode="rich"
)
advanced_app = typer.Typer(
    help="🔧 Advanced operations and utilities",
    rich_markup_mode="rich"
)

# Add command groups to main app
app.add_typer(install_app, name="install")
app.add_typer(lifecycle_app, name="server")  # More intuitive name
app.add_typer(info_app, name="info")
app.add_typer(config_app, name="config")
app.add_typer(diag_app, name="health")  # Shorter name
app.add_typer(advanced_app, name="admin")  # More intuitive name


@app.callback()
def callback(
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """
    🚀 MCP Manager: Comprehensive manager for Model Context Protocol (MCP) servers.
    
    Easily install, configure, and manage MCP servers with rich diagnostics and monitoring.
    """
    if version:
        output_mgr = get_output_manager()
        output_mgr.console.print(f"[bold blue]MCP Manager[/bold blue] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()
    
    # Create directory structure if it doesn't exist
    create_directory_structure()


# === INSTALL COMMANDS ===
@install_app.command("local")
def install_local_wrapper(
    name: str = typer.Argument(..., help="Name for the MCP server"),
    source: Path = typer.Option(
        ..., "--source", "-s", help="Source directory containing the MCP server"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force installation, overwriting existing server"
    ),
    no_pipx: bool = typer.Option(
        False, "--no-pipx", help="Use virtual environment instead of pipx (default: pipx)"
    ),
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Port for SSE transport (optional)"
    ),
    transport: str = typer.Option(
        "stdio", "--transport", "-t", help="Transport type (stdio/sse)"
    ),
    auto_approve: list[str] = typer.Option(
        [], "--auto-approve", help="Auto-approve tools (can be used multiple times)"
    ),
):
    """📁 Install a local MCP server from a directory."""
    from mcp_manager.core.models import TransportType
    transport_type = TransportType.STDIO if transport == "stdio" else TransportType.SSE
    install_local(name=name, source=source, transport=transport_type, port=port, force=force, no_pipx=no_pipx, auto_approve=auto_approve)


@install_app.command("template")
def install_template_wrapper(
    name: str = typer.Argument(..., help="Name for the MCP server"),
    template: str = typer.Option(..., "--template", "-t", help="Template name"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force installation"
    ),
):
    """📁 Install from template."""
    install_from_template(name=name, template=template, force=force)

@install_app.command("list-templates")
def list_templates_wrapper():
    """📋 List available templates."""
    list_templates()


@install_app.command("remote")
def install_remote_wrapper(
    name: str = typer.Argument(..., help="Name for the remote MCP server"),
    url: str = typer.Option(..., "--url", "-u", help="Remote server URL"),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k", help="API key for authentication"
    ),
):
    """🌍 Add a remote MCP server."""
    from mcp_manager.core.models import TransportType
    install_remote(name=name, url=url, api_key=api_key, transport=TransportType.SSE, force=False)


# === LIFECYCLE COMMANDS ===
@lifecycle_app.command("start")
def start_wrapper(
    name: str = typer.Argument(..., help="Server name to start"),
    transport: Optional[str] = typer.Option(None, "--transport", "-t", help="Override transport protocol"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Override port for SSE transport"),
    background: bool = typer.Option(
        False, "--background", "-b", help="Run in background"
    ),
):
    """▶️  Start an MCP server."""
    start_server_impl(name, transport, port, background)


@lifecycle_app.command("stop")
def stop_wrapper(
    name: str = typer.Argument(..., help="Server name to stop"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force stop server"
    ),
):
    """⏹️  Stop an MCP server."""
    stop_server(name, force=force)


@lifecycle_app.command("restart")
def restart_wrapper(
    name: str = typer.Argument(..., help="Server name to restart"),
):
    """🔄 Restart an MCP server."""
    restart_server(name)


@lifecycle_app.command("logs")
def logs_wrapper(
    name: str = typer.Argument(..., help="Server name to show logs for"),
    tail: int = typer.Option(50, "--tail", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(
        False, "--follow", "-f", help="Follow log output"
    ),
):
    """📄 View server logs."""
    show_logs(name, follow=follow, lines=tail)


@lifecycle_app.command("status")
def status_wrapper(
    name: str = typer.Argument(..., help="Server name to show status for"),
):
    """📊 Show server status."""
    show_server_status(name)


# === INFO COMMANDS ===
@info_app.command("list")
def list_servers_wrapper(
    type_filter: Optional[str] = typer.Option(None, "--type", help="Filter by type (local|remote)"),
    status_filter: Optional[str] = typer.Option(None, "--status", help="Filter by status (running|stopped|all)"),
    format: str = typer.Option("human", "--format", "-f", help="Output format (human|json|yaml)"),
):
    """📋 List all MCP servers."""
    list_servers(type_filter=type_filter, status_filter=status_filter, format=format)


@info_app.command("show")
def show_wrapper(
    name: str = typer.Argument(..., help="Server name to show details for"),
    format: str = typer.Option("rich", "--format", "-f", help="Output format (rich/json/yaml)"),
):
    """🔍 Show detailed server information."""
    show_status(name=name, format=format)


@info_app.command("tree")
def tree_wrapper():
    """🌳 Show server hierarchy and dependencies."""
    show_system_info()


@info_app.command("summary")
def summary_wrapper():
    """📈 Show system summary and statistics."""
    show_system_info()


# === CONFIG COMMANDS ===
@config_app.command("cline")
def configure_cline_wrapper(
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before updating"),
):
    """⚙️  Configure VS Code Cline integration."""
    configure_cline(backup=backup)


@config_app.command("claude")
def configure_claude_wrapper(
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before updating"),
):
    """⚙️  Configure Claude Desktop integration."""
    configure_claude_desktop(backup=backup)


@config_app.command("sync")
def sync_wrapper(
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Specific platform to sync (cline|claude)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be synced"),
):
    """🔄 Sync servers with platform configurations."""
    sync_platforms(platform=platform, dry_run=dry_run)


@config_app.command("validate")
def validate_wrapper():
    """✅ Validate all configurations."""
    validate_config()


@config_app.command("backup")
def backup_wrapper():
    """💾 Create backup of configurations."""
    backup_config()


@config_app.command("restore")
def restore_wrapper(
    backup_file: str = typer.Argument(..., help="Backup file to restore from"),
):
    """🔄 Restore configurations from backup."""
    import_config(backup_file)


@config_app.command("import")
def import_config_wrapper(
    file: str = typer.Argument(..., help="Configuration file to import"),
    merge: bool = typer.Option(False, "--merge", help="Merge with existing config"),
):
    """📥 Import configuration from file."""
    import_config(file, overwrite=not merge)


@config_app.command("export")
def export_config_wrapper(
    file: str = typer.Argument(..., help="File to export configuration to"),
    format: str = typer.Option("yaml", "--format", "-f", help="Export format (json/yaml)"),
):
    """📤 Export configuration to file."""
    export_config(Path(file), format=format)


# === HEALTH/DIAGNOSTIC COMMANDS ===
@diag_app.command("check")
def health_check_wrapper(
    name: Optional[str] = typer.Argument(None, help="Server name (optional)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Perform detailed health check"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Health check timeout in seconds"),
    format: str = typer.Option("human", "--format", "-f", help="Output format (human|json)"),
):
    """🏥 Perform health check on servers."""
    health_check(name=name, detailed=detailed, timeout=timeout, format=format)


@diag_app.command("monitor")
def monitor_wrapper(
    name: Optional[str] = typer.Argument(None, help="Server name to monitor (optional)"),
    interval: int = typer.Option(5, "--interval", "-i", help="Update interval in seconds"),
):
    """📊 Monitor server metrics in real-time."""
    monitor_health(name=name, interval=interval)


@diag_app.command("test")
def test_connection_wrapper(
    name: str = typer.Argument(..., help="Server name to test"),
):
    """🔗 Test server connection and functionality."""
    troubleshoot_server(name=name, auto_fix=False)


@diag_app.command("troubleshoot")
def troubleshoot_wrapper(
    name: Optional[str] = typer.Argument(None, help="Server name (optional)"),
):
    """🔧 Run troubleshooting diagnostics."""
    troubleshoot_server(name=name)


# === ADVANCED/ADMIN COMMANDS ===
@advanced_app.command("cleanup")
def cleanup_wrapper(
    logs: bool = typer.Option(True, "--logs/--no-logs", help="Clean up old log files"),
    backups: bool = typer.Option(True, "--backups/--no-backups", help="Clean up old backup files"),
    processes: bool = typer.Option(True, "--processes/--no-processes", help="Clean up stale process entries"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be cleaned without making changes"),
    age_days: int = typer.Option(30, "--age-days", help="Age in days for files to be considered old"),
):
    """🧹 Clean up unused servers and files."""
    cleanup_system(logs=logs, backups=backups, processes=processes, dry_run=dry_run, age_days=age_days)


@advanced_app.command("reset")
def reset_wrapper(
    name: Optional[str] = typer.Argument(None, help="Server name to reset (optional)"),
    confirm: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
):
    """🔄 Reset server or entire system."""
    reset_system(name=name, confirm=confirm)


@advanced_app.command("migrate")
def migrate_wrapper(
    from_version: Optional[str] = typer.Option(None, "--from", help="Source version"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show migration plan"),
):
    """🚚 Migrate configurations to current version."""
    migrate_data(from_version=from_version, dry_run=dry_run)


@advanced_app.command("analyze")
def analyze_wrapper(
    name: Optional[str] = typer.Argument(None, help="Server name (analyzes all if not specified)"),
    duration: int = typer.Option(60, "--duration", "-d", help="Analysis duration in seconds"),
    interval: int = typer.Option(5, "--interval", "-i", help="Sampling interval in seconds"),
):
    """📊 Analyze system performance and usage."""
    analyze_performance(name=name, duration=duration, interval=interval)


@advanced_app.command("optimize")
def optimize_wrapper():
    """⚡ Optimize system performance."""
    export_diagnostics()


@advanced_app.command("benchmark")
def benchmark_wrapper(
    name: Optional[str] = typer.Argument(None, help="Server name to benchmark (optional)"),
):
    """🏃 Run performance benchmarks."""
    analyze_performance(name=name)


# === CONVENIENCE COMMANDS (shortcuts for common operations) ===
@app.command("list")
def quick_list():
    """📋 Quick list of all servers (shortcut)."""
    list_servers(type_filter=None, status_filter="all", format="human")


@app.command("run")  # Legacy compatibility
def quick_run(
    name: str = typer.Argument(..., help="Server name to run"),
):
    """▶️  Quick start a server (shortcut)."""
    start_server_impl(name)


@app.command("version")
def show_version():
    """📋 Show detailed version information."""
    mcp_home = get_mcp_home()
    output_mgr = get_output_manager()
    
    output_mgr.console.print(Panel(
        f"[bold blue]MCP Manager[/bold blue] version [bold green]{__version__}[/bold green]\n\n"
        f"🏠 MCP home: [cyan]{mcp_home}[/cyan]\n"
        f"🐍 Python: [cyan]{sys.executable}[/cyan]\n"
        f"📦 Rich UI: [green]Enabled[/green]\n",
        title="📋 Version Information",
        expand=False
    ))


@app.command("help")
def show_help():
    """❓ Show comprehensive help and usage examples."""
    mcp_home = get_mcp_home()
    output_mgr = get_output_manager()
    help_text = f"""
[bold blue]🚀 MCP Manager - Usage Guide[/bold blue]

[bold yellow]📁 FILE LOCATIONS[/bold yellow]
  [bold]Config files[/bold] (checked in order):
  [dim]1. ~/.config/mcp-manager/servers/{{server-name}}/config.yaml[/dim] (managed)
  [dim]2. ~/.config/mcp-manager/servers/{{server-name}}/.env[/dim] (managed env vars)
  [dim]3. Legacy locations (server-specific)[/dim]
  [dim]4. ./config.yaml or ./.env[/dim] (local development)

  [bold]Log files[/bold]:
  [dim]~/.config/mcp-manager/logs/{{server-name}}.log[/dim]

  [bold]Virtual environments[/bold]:
  [dim]~/.config/mcp-manager/servers/{{server-name}}/.venv[/dim]

  [bold]System directory[/bold]: [cyan]{mcp_home}[/cyan]

[bold yellow]📦 INSTALLATION COMMANDS[/bold yellow]
  [cyan]mcp-manager install local my-server --source /path/to/server[/cyan]
    Install from local directory

  [cyan]mcp-manager install git my-server --repo https://github.com/user/repo[/cyan]
    Install from Git repository

  [cyan]mcp-manager install pipx my-server --package server-package[/cyan]
    Install using pipx

  [cyan]mcp-manager install remote my-server --url https://api.server.com[/cyan]
    Add remote server

[bold yellow]🔄 SERVER LIFECYCLE[/bold yellow]
  [cyan]mcp-manager server start my-server[/cyan]           Start server
  [cyan]mcp-manager server stop my-server[/cyan]            Stop server
  [cyan]mcp-manager server restart my-server[/cyan]         Restart server
  [cyan]mcp-manager server logs my-server --follow[/cyan]   View logs
  [cyan]mcp-manager server status[/cyan]                    Show all server status

[bold yellow]📋 INFORMATION & MONITORING[/bold yellow]
  [cyan]mcp-manager info list[/cyan]                        List all servers
  [cyan]mcp-manager info show my-server[/cyan]              Show server details (includes file paths)

[bold yellow]⚙️ CONFIGURATION[/bold yellow]
  [cyan]mcp-manager config cline[/cyan]                    Configure VS Code/Cline
  [cyan]mcp-manager config claude[/cyan]                   Configure Claude Desktop
  [cyan]mcp-manager config sync[/cyan]                     Sync all platforms
  [cyan]mcp-manager config validate[/cyan]                 Validate configurations

[bold yellow]🏥 HEALTH & DIAGNOSTICS[/bold yellow]
  [cyan]mcp-manager health check[/cyan]                     Health check all servers
  [cyan]mcp-manager health monitor[/cyan]                   Real-time monitoring
  [cyan]mcp-manager health test my-server[/cyan]            Test specific server
  [cyan]mcp-manager health troubleshoot[/cyan]              Run diagnostics

[bold yellow]🔧 ADVANCED OPERATIONS[/bold yellow]
  [cyan]mcp-manager admin cleanup[/cyan]                    Clean unused files
  [cyan]mcp-manager admin analyze[/cyan]                    Performance analysis
  [cyan]mcp-manager admin optimize[/cyan]                   Optimize system
  [cyan]mcp-manager admin benchmark[/cyan]                  Run benchmarks

[bold yellow]⚡ QUICK SHORTCUTS[/bold yellow]
  [cyan]mcp-manager list[/cyan]                             Quick server list
  [cyan]mcp-manager run my-server[/cyan]                    Quick start server
  [cyan]mcp-manager version[/cyan]                          Version information

[bold yellow]🔍 FINDING YOUR FILES[/bold yellow]
  [cyan]mcp-manager info show my-server[/cyan]              See which config files exist & are being used
  [cyan]mcp-manager server logs my-server[/cyan]            View logs (shows log file location)
  
[dim]💡 Tip: Use --help with any command for detailed options[/dim]
"""
    output_mgr.console.print(help_text)


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        handle_error(e)
        raise typer.Exit(1)
