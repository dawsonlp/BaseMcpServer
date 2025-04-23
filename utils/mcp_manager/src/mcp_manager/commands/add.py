"""
Implementation of the add command.

This module provides functions for adding remote MCP servers
to the registry without installing them locally.
"""

import httpx
from pathlib import Path
from typing import Optional
from pydantic import HttpUrl
from rich.console import Console
from datetime import datetime

from mcp_manager.server import (
    RemoteServer,
    ServerType,
    ServerRegistry,
    get_registry_path,
)


console = Console()


def add_remote_server(name: str, url: str, api_key: str) -> None:
    """Add a remote MCP server to the registry."""
    # Validate server name
    if not name.isalnum() and not (name.replace("-", "").isalnum() and "-" in name):
        raise ValueError(
            f"Server name must be alphanumeric or contain only hyphens, got '{name}'"
        )
    
    # Validate URL is accessible
    normalized_url = url
    if not url.endswith("/sse"):
        normalized_url = f"{url}/sse"
    
    # Try to connect to the server
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
    except httpx.RequestError as e:
        console.print(f"[yellow]Warning:[/yellow] Could not connect to {url}: {e}")
        console.print("Adding server anyway, but it may not be accessible.")
    
    # Create server entry
    server = RemoteServer(
        name=name,
        server_type=ServerType.REMOTE_SSE,
        url=HttpUrl(normalized_url),
        api_key=api_key,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # Register the server
    registry = ServerRegistry.load(get_registry_path())
    registry.add_server(server)
    registry.save(get_registry_path())
    
    console.print(f"Added remote server [bold]{name}[/bold] at [bold]{normalized_url}[/bold]")
