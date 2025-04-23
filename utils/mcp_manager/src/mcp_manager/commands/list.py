"""
Implementation of the list command.

This module provides functions for listing all configured MCP servers.
"""

from rich.console import Console
from rich.table import Table
from typing import Dict, Optional, List, Union, cast

from mcp_manager.server import (
    Server,
    LocalServer,
    RemoteServer,
    ServerRegistry,
    ServerType,
    get_registry_path,
)


console = Console()


def list_servers(local_only: bool = False, remote_only: bool = False) -> None:
    """List all configured MCP servers."""
    # Load the server registry
    registry = ServerRegistry.load(get_registry_path())
    
    if len(registry.servers) == 0:
        console.print("[yellow]No MCP servers configured.[/yellow]")
        console.print("Use [bold]mcp-manager install[/bold] or [bold]mcp-manager add[/bold] to add servers.")
        return
    
    # Create tables for different server types
    local_table = Table(title="Local MCP Servers")
    local_table.add_column("Name", style="cyan")
    local_table.add_column("Type", style="green")
    local_table.add_column("Source", style="blue")
    local_table.add_column("Port", style="magenta")
    local_table.add_column("Status", style="yellow")
    
    remote_table = Table(title="Remote MCP Servers")
    remote_table.add_column("Name", style="cyan")
    remote_table.add_column("URL", style="blue")
    remote_table.add_column("Status", style="yellow")
    
    # Add servers to the tables
    local_count = 0
    remote_count = 0
    
    for name, server in registry.servers.items():
        if isinstance(server, LocalServer) and not remote_only:
            local_count += 1
            port = str(server.port) if server.port else "N/A"
            server_type = "HTTP+SSE" if server.server_type == ServerType.LOCAL_SSE else "stdio"
            status = "Disabled" if server.disabled else "Enabled"
            local_table.add_row(
                name,
                server_type,
                str(server.source_dir),
                port,
                status,
            )
        elif isinstance(server, RemoteServer) and not local_only:
            remote_count += 1
            status = "Disabled" if server.disabled else "Enabled"
            remote_table.add_row(
                name,
                str(server.url),
                status,
            )
    
    # Print the tables
    if local_count > 0 and not remote_only:
        console.print(local_table)
    
    if remote_count > 0 and not local_only:
        console.print(remote_table)
    
    # Print summary
    if local_only and local_count == 0:
        console.print("[yellow]No local MCP servers configured.[/yellow]")
    elif remote_only and remote_count == 0:
        console.print("[yellow]No remote MCP servers configured.[/yellow]")
