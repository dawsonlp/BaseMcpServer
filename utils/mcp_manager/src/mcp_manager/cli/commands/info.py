"""
Information and status commands for MCP Manager 3.0.

Provides server listing, status display, and system information commands.
"""

import typer
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from mcp_manager.core.models import Server, ServerState, SystemInfo, PlatformType
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.health import HealthChecker
from mcp_manager.core.platforms import PlatformManager
from mcp_manager.cli.common.output import get_output_manager, OutputFormat
from mcp_manager.cli.common.errors import handle_error, MCPManagerError


app = typer.Typer(help="Information and status commands")
output = get_output_manager()
state = get_state_manager()
health_checker = HealthChecker()
platform_manager = PlatformManager()


@app.command("list")
def list_servers(
    type_filter: Optional[str] = typer.Option(None, "--type", help="Filter by type (local|remote)"),
    status_filter: Optional[str] = typer.Option(None, "--status", help="Filter by status (running|stopped|all)"),
    format: str = typer.Option("human", "--format", "-f", help="Output format (human|json|yaml)"),
):
    """List all registered servers."""
    try:
        # Get all servers
        servers = state.get_servers()
        server_states = state.get_all_server_states()
        
        # Apply filters
        filtered_servers = {}
        for name, server in servers.items():
            # Type filter
            if type_filter and server.server_type.value != type_filter:
                continue
            
            # Status filter
            if status_filter and status_filter != "all":
                server_state = server_states.get(name)
                is_running = server_state and server_state.is_running()
                
                if status_filter == "running" and not is_running:
                    continue
                elif status_filter == "stopped" and is_running:
                    continue
            
            filtered_servers[name] = server
        
        # Format output
        if format == "json":
            # JSON output
            json_data = {}
            for name, server in filtered_servers.items():
                server_state = server_states.get(name)
                json_data[name] = {
                    "name": name,
                    "type": server.server_type.value,
                    "transport": server.transport.value,
                    "status": server_state.process_status.value if server_state else "stopped",
                    "health": server_state.health_status.value if server_state else "unknown",
                    "port": server.port,
                    "source_dir": str(server.source_dir) if server.source_dir else None,
                    "url": str(server.url) if server.url else None,
                    "enabled": server.enabled,
                    "auto_approve": server.auto_approve,
                    "created_at": server.created_at.isoformat(),
                    "updated_at": server.updated_at.isoformat()
                }
            
            output.console.print(json.dumps(json_data, indent=2))
            
        elif format == "yaml":
            # YAML output
            yaml_data = {}
            for name, server in filtered_servers.items():
                server_state = server_states.get(name)
                yaml_data[name] = {
                    "name": name,
                    "type": server.server_type.value,
                    "transport": server.transport.value,
                    "status": server_state.process_status.value if server_state else "stopped",
                    "health": server_state.health_status.value if server_state else "unknown",
                    "port": server.port,
                    "source_dir": str(server.source_dir) if server.source_dir else None,
                    "url": str(server.url) if server.url else None,
                    "enabled": server.enabled,
                    "auto_approve": server.auto_approve,
                    "created_at": server.created_at.isoformat(),
                    "updated_at": server.updated_at.isoformat()
                }
            
            output.console.print(yaml.dump(yaml_data, default_flow_style=False))
            
        else:
            # Human-readable table
            if not filtered_servers:
                output.info("No servers found")
                return
            
            table = Table(title="MCP Servers")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Type", style="blue")
            table.add_column("Transport", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Health", style="magenta")
            table.add_column("Port", style="white")
            table.add_column("Source/URL", style="dim")
            
            for name, server in filtered_servers.items():
                server_state = server_states.get(name)
                
                # Status formatting
                status = server_state.process_status.value if server_state else "stopped"
                health = server_state.health_status.value if server_state else "unknown"
                
                # Source/URL display
                if server.is_local():
                    source_display = str(server.source_dir) if server.source_dir else "N/A"
                else:
                    source_display = str(server.url) if server.url else "N/A"
                
                # Truncate long paths
                if len(source_display) > 40:
                    source_display = "..." + source_display[-37:]
                
                table.add_row(
                    name,
                    server.server_type.value,
                    server.transport.value,
                    status,
                    health,
                    str(server.port) if server.port else "-",
                    source_display
                )
            
            output.console.print(table)
            output.info(f"Found {len(filtered_servers)} server(s)")
        
    except Exception as e:
        handle_error(e, "Failed to list servers")


@app.command("status")
def show_status(
    name: Optional[str] = typer.Argument(None, help="Specific server name (optional)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
    format: str = typer.Option("human", "--format", "-f", help="Output format (human|json|yaml)"),
):
    """Show server status information."""
    try:
        if name:
            # Show status for specific server
            server = state.get_server(name)
            if not server:
                raise MCPManagerError(f"Server '{name}' not found")
            
            server_state = state.get_server_state(name)
            
            if format == "json":
                status_data = {
                    "name": name,
                    "type": server.server_type.value,
                    "transport": server.transport.value,
                    "status": server_state.process_status.value if server_state else "stopped",
                    "health": server_state.health_status.value if server_state else "unknown",
                    "enabled": server.enabled
                }
                
                if detailed and server_state:
                    status_data.update({
                        "health_score": server_state.health_score,
                        "uptime": str(server_state.uptime) if server_state.uptime else None,
                        "memory_mb": server_state.memory_usage_mb,
                        "cpu_percent": server_state.cpu_usage_percent,
                        "last_error": server_state.last_error,
                        "last_health_check": server_state.last_health_check.isoformat() if server_state.last_health_check else None
                    })
                
                output.console.print(json.dumps(status_data, indent=2))
                
            else:
                # Human-readable status
                title = f"Status: {name}"
                if server_state:
                    status_color = "green" if server_state.is_running() else "red"
                    title += f" ([{status_color}]{server_state.process_status.value}[/{status_color}])"
                
                table = Table(title=title)
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Name", name)
                table.add_row("Type", server.server_type.value)
                table.add_row("Transport", server.transport.value)
                table.add_row("Enabled", "Yes" if server.enabled else "No")
                
                if server.port:
                    table.add_row("Port", str(server.port))
                
                if server_state:
                    table.add_row("Status", server_state.process_status.value)
                    table.add_row("Health", server_state.health_status.value)
                    
                    if detailed:
                        table.add_row("Health Score", f"{server_state.health_score:.1%}")
                        if server_state.uptime:
                            table.add_row("Uptime", str(server_state.uptime))
                        if server_state.memory_usage_mb:
                            table.add_row("Memory", f"{server_state.memory_usage_mb} MB")
                        if server_state.cpu_usage_percent:
                            table.add_row("CPU", f"{server_state.cpu_usage_percent:.1f}%")
                        if server_state.last_error:
                            table.add_row("Last Error", server_state.last_error)
                
                if server.is_local():
                    table.add_row("Source Directory", str(server.source_dir) if server.source_dir else "N/A")
                    if server.venv_dir:
                        table.add_row("Virtual Environment", str(server.venv_dir))
                else:
                    table.add_row("URL", str(server.url) if server.url else "N/A")
                
                if server.auto_approve:
                    table.add_row("Auto-approve", ", ".join(server.auto_approve))
                
                output.console.print(table)
        else:
            # Show overview of all servers
            servers = state.get_servers()
            server_states = state.get_all_server_states()
            
            if not servers:
                output.info("No servers registered")
                return
            
            # Count by status
            running_count = sum(1 for state in server_states.values() if state.is_running())
            total_count = len(servers)
            
            # Create overview panel
            overview_text = Text()
            overview_text.append(f"Total Servers: {total_count}\n", style="bold")
            overview_text.append(f"Running: {running_count}\n", style="green")
            overview_text.append(f"Stopped: {total_count - running_count}", style="red")
            
            overview_panel = Panel(
                overview_text,
                title="Server Overview",
                border_style="blue"
            )
            
            # Create status grid
            server_panels = []
            for name, server in servers.items():
                server_state = server_states.get(name)
                is_running = server_state and server_state.is_running()
                
                status_text = Text()
                status_text.append(f"{name}\n", style="bold cyan")
                status_text.append(f"Type: {server.server_type.value}\n", style="dim")
                status_text.append(f"Status: ", style="dim")
                status_text.append(
                    server_state.process_status.value if server_state else "stopped",
                    style="green" if is_running else "red"
                )
                
                panel_style = "green" if is_running else "red"
                server_panels.append(Panel(status_text, border_style=panel_style))
            
            # Display overview and servers
            output.console.print(overview_panel)
            output.console.print()
            
            if server_panels:
                columns = Columns(server_panels, equal=True, expand=True)
                output.console.print(columns)
        
    except Exception as e:
        handle_error(e, "Failed to show status")


@app.command("system")
def show_system_info():
    """Show system information and MCP Manager status."""
    try:
        system_info = state.get_system_info()
        
        # Create system info table
        table = Table(title="System Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Python Version", system_info.python_version)
        table.add_row("Platform", system_info.platform)
        table.add_row("MCP Home", str(system_info.mcp_home))
        table.add_row("Total Servers", str(system_info.total_servers))
        table.add_row("Running Servers", str(system_info.running_servers))
        table.add_row("Disk Usage", f"{system_info.disk_usage_mb} MB")
        
        output.console.print(table)
        
        # Platform information
        if system_info.platforms:
            platform_table = Table(title="Platform Integration")
            platform_table.add_column("Platform", style="cyan")
            platform_table.add_column("Status", style="yellow")
            platform_table.add_column("Servers", style="green")
            platform_table.add_column("Config Path", style="dim")
            
            for platform in system_info.platforms:
                status = "Available" if platform.is_available() else "Not Available"
                config_path = str(platform.config_path) if platform.config_path else "N/A"
                
                # Truncate long paths
                if len(config_path) > 50:
                    config_path = "..." + config_path[-47:]
                
                platform_table.add_row(
                    platform.display_name,
                    status,
                    str(platform.server_count),
                    config_path
                )
            
            output.console.print(platform_table)
        
    except Exception as e:
        handle_error(e, "Failed to show system information")


@app.command("logs")
def show_logs(
    name: str = typer.Argument(..., help="Server name"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    level: str = typer.Option("info", "--level", help="Minimum log level"),
):
    """Show server logs."""
    try:
        # Delegate to lifecycle module for consistency
        from mcp_manager.cli.commands.lifecycle import show_logs as lifecycle_show_logs
        lifecycle_show_logs(name, follow, lines, level)
        
    except Exception as e:
        handle_error(e, f"Failed to show logs for server '{name}'")


@app.command("config")
def show_config(
    name: str = typer.Argument(..., help="Server name"),
    format: str = typer.Option("yaml", "--format", "-f", help="Output format (yaml|json)"),
):
    """Show server configuration."""
    try:
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Convert server to dict
        config_data = server.model_dump(mode='json')
        
        # Convert Path objects to strings for serialization
        for key, value in config_data.items():
            if isinstance(value, Path):
                config_data[key] = str(value)
        
        if format == "json":
            output.console.print(json.dumps(config_data, indent=2, default=str))
        else:
            output.console.print(yaml.dump(config_data, default_flow_style=False))
        
    except Exception as e:
        handle_error(e, f"Failed to show configuration for server '{name}'")


if __name__ == "__main__":
    app()
