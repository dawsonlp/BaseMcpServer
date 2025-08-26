"""
Implementation of the config-info command.

This module provides functions for displaying comprehensive MCP configuration
information across different applications (VS Code/Cline, Claude Desktop)
and cross-referencing with the mcp-manager registry.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from mcp_manager.server import (
    ServerRegistry,
    LocalServer,
    RemoteServer,
    get_registry_path,
    get_vscode_cline_settings_path,
    get_claude_desktop_settings_path,
)


console = Console()


@dataclass
class ConfigFileInfo:
    """Information about a configuration file."""
    
    path: Path
    exists: bool
    readable: bool
    servers_count: int
    error_message: Optional[str] = None


@dataclass
class ServerConfigInfo:
    """Information about a server's configuration status."""
    
    name: str
    enabled: bool
    server_type: str
    managed_by: str  # "mcp-manager" or "manual"
    config_source: str  # "cline", "claude-desktop", "registry-only"


@dataclass
class ConfigAnalysis:
    """Complete analysis of MCP configuration status."""
    
    cline_config: ConfigFileInfo
    claude_desktop_config: ConfigFileInfo
    registry_servers: Dict[str, Any]
    configured_servers: List[ServerConfigInfo]
    orphaned_servers: List[str]  # In registry but not configured
    unmanaged_servers: List[str]  # Configured but not in registry


def discover_config_files() -> Tuple[ConfigFileInfo, ConfigFileInfo]:
    """Discover and validate configuration file paths."""
    
    def check_config_file(path: Path) -> ConfigFileInfo:
        """Check a single configuration file."""
        exists = path.exists()
        readable = False
        servers_count = 0
        error_message = None
        
        if exists:
            try:
                if path.stat().st_size == 0:
                    error_message = "File is empty"
                else:
                    content = path.read_text()
                    data = json.loads(content)
                    if "mcpServers" in data:
                        servers_count = len(data["mcpServers"])
                    readable = True
            except PermissionError:
                error_message = "Permission denied"
            except json.JSONDecodeError as e:
                error_message = f"Invalid JSON: {e}"
            except Exception as e:
                error_message = f"Error reading file: {e}"
        
        return ConfigFileInfo(
            path=path,
            exists=exists,
            readable=readable,
            servers_count=servers_count,
            error_message=error_message
        )
    
    cline_path = get_vscode_cline_settings_path()
    claude_desktop_path = get_claude_desktop_settings_path()
    
    return (
        check_config_file(cline_path),
        check_config_file(claude_desktop_path)
    )


def parse_cline_config(path: Path) -> Dict[str, Any]:
    """Parse VS Code/Cline MCP settings."""
    if not path.exists():
        return {}
    
    try:
        content = path.read_text()
        data = json.loads(content)
        return data.get("mcpServers", {})
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not parse Cline config: {e}")
        return {}


def parse_claude_desktop_config(path: Path) -> Dict[str, Any]:
    """Parse Claude Desktop settings."""
    if not path.exists():
        return {}
    
    try:
        content = path.read_text()
        data = json.loads(content)
        return data.get("mcpServers", {})
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not parse Claude Desktop config: {e}")
        return {}


def get_managed_server_names(registry: ServerRegistry) -> Set[str]:
    """Return set of server names managed by mcp-manager."""
    return set(registry.servers.keys())


def determine_server_type(config_entry: Dict[str, Any]) -> str:
    """Determine server type from configuration entry."""
    if "url" in config_entry:
        return "remote"
    elif "command" in config_entry:
        return "stdio"
    else:
        return "unknown"


def cross_reference_servers(registry: ServerRegistry, cline_config: Dict[str, Any], 
                          claude_desktop_config: Dict[str, Any]) -> ConfigAnalysis:
    """Cross-reference servers between registry and configuration files."""
    
    managed_servers = get_managed_server_names(registry)
    configured_servers = []
    
    # Analyze Cline servers
    for server_name, config in cline_config.items():
        enabled = not config.get("disabled", False)
        server_type = determine_server_type(config)
        managed_by = "mcp-manager" if server_name in managed_servers else "manual"
        
        configured_servers.append(ServerConfigInfo(
            name=server_name,
            enabled=enabled,
            server_type=server_type,
            managed_by=managed_by,
            config_source="cline"
        ))
    
    # Analyze Claude Desktop servers
    for server_name, config in claude_desktop_config.items():
        # Check if already added from Cline
        existing = next((s for s in configured_servers if s.name == server_name), None)
        if existing:
            # Update to show it's in both configs
            existing.config_source = "cline+claude-desktop"
        else:
            enabled = True  # Claude Desktop doesn't have disabled field
            server_type = determine_server_type(config)
            managed_by = "mcp-manager" if server_name in managed_servers else "manual"
            
            configured_servers.append(ServerConfigInfo(
                name=server_name,
                enabled=enabled,
                server_type=server_type,
                managed_by=managed_by,
                config_source="claude-desktop"
            ))
    
    # Find orphaned servers (in registry but not configured)
    configured_names = {s.name for s in configured_servers}
    orphaned_servers = list(managed_servers - configured_names)
    
    # Find unmanaged servers (configured but not in registry)
    unmanaged_servers = [s.name for s in configured_servers if s.managed_by == "manual"]
    
    # Discover config files
    cline_config_info, claude_desktop_config_info = discover_config_files()
    
    return ConfigAnalysis(
        cline_config=cline_config_info,
        claude_desktop_config=claude_desktop_config_info,
        registry_servers=dict(registry.servers),
        configured_servers=configured_servers,
        orphaned_servers=orphaned_servers,
        unmanaged_servers=unmanaged_servers
    )


def format_config_info_output(analysis: ConfigAnalysis) -> None:
    """Format and display configuration information using Rich."""
    
    # Header
    console.print(Panel(
        "[bold]MCP Configuration Status[/bold]",
        style="blue"
    ))
    console.print()
    
    # Configuration Files Status
    console.print("[bold]Configuration Files:[/bold]")
    
    # Cline config
    if analysis.cline_config.exists and analysis.cline_config.readable:
        status = f"✓ VS Code/Cline: [cyan]{analysis.cline_config.path}[/cyan] ({analysis.cline_config.servers_count} servers configured)"
    elif analysis.cline_config.exists:
        status = f"⚠ VS Code/Cline: [cyan]{analysis.cline_config.path}[/cyan] (error: {analysis.cline_config.error_message})"
    else:
        status = f"✗ VS Code/Cline: [cyan]{analysis.cline_config.path}[/cyan] (not found)"
    console.print(status)
    
    # Claude Desktop config
    if analysis.claude_desktop_config.exists and analysis.claude_desktop_config.readable:
        status = f"✓ Claude Desktop: [cyan]{analysis.claude_desktop_config.path}[/cyan] ({analysis.claude_desktop_config.servers_count} servers configured)"
    elif analysis.claude_desktop_config.exists:
        status = f"⚠ Claude Desktop: [cyan]{analysis.claude_desktop_config.path}[/cyan] (error: {analysis.claude_desktop_config.error_message})"
    else:
        status = f"✗ Claude Desktop: [cyan]{analysis.claude_desktop_config.path}[/cyan] (not found)"
    console.print(status)
    console.print()
    
    # Configured Servers Table
    if analysis.configured_servers:
        console.print("[bold]Configured Servers:[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Server", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Type", justify="center")
        table.add_column("Managed By", justify="center")
        table.add_column("Config Source", justify="center")
        
        for server in sorted(analysis.configured_servers, key=lambda x: x.name):
            # Status indicator
            if server.enabled:
                status_text = Text("✓", style="green")
            else:
                status_text = Text("✗", style="red")
            
            # Management indicator
            if server.managed_by == "mcp-manager":
                managed_text = Text("mcp-manager", style="green")
            else:
                managed_text = Text("manual", style="yellow")
            
            table.add_row(
                server.name,
                status_text,
                server.server_type,
                managed_text,
                server.config_source
            )
        
        console.print(table)
        console.print()
    
    # Registry Status Summary
    console.print("[bold]Registry Status:[/bold]")
    total_registry = len(analysis.registry_servers)
    total_configured = len(analysis.configured_servers)
    total_orphaned = len(analysis.orphaned_servers)
    total_unmanaged = len(analysis.unmanaged_servers)
    
    console.print(f"• {total_registry} servers in mcp-manager registry")
    console.print(f"• {total_configured} servers actively configured")
    
    if total_orphaned > 0:
        console.print(f"• [yellow]{total_orphaned} orphaned entries[/yellow] (in registry, not configured): {', '.join(analysis.orphaned_servers)}")
    
    if total_unmanaged > 0:
        console.print(f"• [yellow]{total_unmanaged} unmanaged servers[/yellow] (configured, not in registry): {', '.join(analysis.unmanaged_servers)}")
    
    if total_orphaned == 0 and total_unmanaged == 0:
        console.print("• [green]No configuration inconsistencies detected[/green]")


def config_info_main() -> None:
    """Main entry point for the config-info command."""
    try:
        # Load the server registry
        registry_path = get_registry_path()
        if not registry_path.exists():
            console.print("[yellow]Warning:[/yellow] MCP manager registry not found. Run 'mcpmanager configure' to initialize.")
            registry = ServerRegistry()
        else:
            registry = ServerRegistry.load(registry_path)
        
        # Parse configuration files
        cline_config = parse_cline_config(get_vscode_cline_settings_path())
        claude_desktop_config = parse_claude_desktop_config(get_claude_desktop_settings_path())
        
        # Perform cross-reference analysis
        analysis = cross_reference_servers(registry, cline_config, claude_desktop_config)
        
        # Display results
        format_config_info_output(analysis)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise
