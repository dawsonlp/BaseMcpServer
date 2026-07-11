"""
Information commands: list registered servers and show one server's details.

These read only the registry (the single source of truth) and each server's
static config — mcp-manager does not run or monitor server processes (the AI
clients launch them over stdio), so there is no runtime status to report.
"""

import json
from typing import Optional

import yaml
from rich.table import Table

from mcp_manager.core.state import get_server_dir, get_state_manager
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError

output = get_output_manager()
state = get_state_manager()


def _server_dict(name: str, server) -> dict:
    return {
        "name": name,
        "type": server.server_type.value,
        "transport": server.transport.value,
        "enabled": server.enabled,
        "port": server.port,
        "source_dir": str(server.source_dir) if server.source_dir else None,
        "venv_dir": str(server.venv_dir) if server.venv_dir else None,
        "auto_approve": list(server.auto_approve),
        "config_file": str(get_server_dir(name) / "config.yaml"),
    }


def list_servers(type_filter: Optional[str] = None, status_filter: Optional[str] = None,
                 format: str = "human") -> None:
    """List registered servers."""
    try:
        servers = state.get_servers()
        if type_filter:
            servers = {n: s for n, s in servers.items() if s.server_type.value == type_filter}

        if format in ("json", "yaml"):
            data = [_server_dict(n, s) for n, s in servers.items()]
            output.console.print(
                json.dumps(data, indent=2) if format == "json"
                else yaml.safe_dump(data, sort_keys=False)
            )
            return

        if not servers:
            output.info("No servers registered. Install one with `mcp-manager install <name>`.")
            return

        table = Table(title="MCP Servers")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Transport")
        table.add_column("Port")
        table.add_column("Source")
        for name, server in servers.items():
            table.add_row(
                name,
                server.server_type.value,
                server.transport.value,
                str(server.port) if server.port else "-",
                str(server.source_dir) if server.source_dir else "-",
            )
        output.console.print(table)
    except Exception as e:
        handle_error(e, "Failed to list servers")


def show_status(name: str, detailed: bool = False, format: str = "rich") -> None:
    """Show details for one server, including its config file paths."""
    try:
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")

        info = _server_dict(name, server)
        if format in ("json", "yaml"):
            output.console.print(
                json.dumps(info, indent=2) if format == "json"
                else yaml.safe_dump(info, sort_keys=False)
            )
            return

        table = Table(title=f"Server: {name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Name", name)
        table.add_row("Type", info["type"])
        table.add_row("Transport", info["transport"])
        table.add_row("Enabled", "Yes" if server.enabled else "No")
        if server.port:
            table.add_row("Port", str(server.port))
        if server.source_dir:
            table.add_row("Source Directory", str(server.source_dir))
        if server.venv_dir:
            table.add_row("Virtual Environment", str(server.venv_dir))
        table.add_row("Config File", info["config_file"])
        if server.auto_approve:
            table.add_row("Auto-approve", ", ".join(server.auto_approve))
        output.console.print(table)
    except Exception as e:
        handle_error(e, "Failed to show server")
