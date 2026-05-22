"""
Platform integration for MCP Manager.

Writes the per-editor `mcpServers` settings entries for the local servers
that mcp-manager owns. Supports VS Code/Cline and Claude Desktop.

Scope is intentionally narrow: build entries from the current `Server`
model and push them to the editor's settings file. Reading arbitrary
external entries back into the registry isn't supported because the
`Server` model assumes mcp-manager owns the install (venv_dir + source_dir).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_manager.core.logging import MCPManagerLogger
from mcp_manager.core.models import PlatformType, Server, ServerType, TransportType
from mcp_manager.core.state import (
    get_claude_desktop_settings_path,
    get_vscode_cline_settings_path,
)


_PLATFORM_SETTINGS_PATH_FACTORY = {
    PlatformType.CLINE: get_vscode_cline_settings_path,
    PlatformType.CLAUDE_DESKTOP: get_claude_desktop_settings_path,
}


def get_platform_settings_path(platform: PlatformType) -> Path:
    return _PLATFORM_SETTINGS_PATH_FACTORY[platform]()


def is_platform_installed(platform: PlatformType) -> bool:
    """Treat a platform as installed if its settings directory exists."""
    return get_platform_settings_path(platform).parent.exists()


def discover_installed_platforms() -> List[PlatformType]:
    return [p for p in PlatformType if is_platform_installed(p)]


def _server_executable_path(server: Server) -> Optional[Path]:
    if not server.venv_dir:
        return None
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    suffix = ".exe" if sys.platform == "win32" else ""
    return server.venv_dir / bin_dir / f"{server.name}{suffix}"


def build_mcp_server_entry(server: Server, platform: PlatformType) -> Optional[Dict[str, Any]]:
    """Build the `mcpServers` JSON entry for one server, or None if it can't be expressed.

    Cline and Claude Desktop both expect a command/args/env shape; neither
    supports remote URL entries or SSE transport in their `mcpServers`
    section. Servers that don't fit are returned as None so callers can
    skip them with a meaningful reason.
    """
    if server.server_type != ServerType.LOCAL:
        return None
    if server.transport != TransportType.STDIO:
        return None

    executable_path = _server_executable_path(server)
    if not executable_path or not executable_path.exists():
        return None

    entry: Dict[str, Any] = {
        "command": str(executable_path),
        "args": ["stdio"],
    }
    if server.environment:
        entry["env"] = dict(server.environment)

    if platform == PlatformType.CLINE:
        entry["disabled"] = not server.enabled
        entry["autoApprove"] = list(server.auto_approve)

    return entry


def _entry_skip_reason(server: Server) -> str:
    if server.server_type != ServerType.LOCAL:
        return "remote server"
    if server.transport != TransportType.STDIO:
        return f"unsupported transport: {server.transport.value}"
    if not server.venv_dir:
        return "no venv_dir"
    return "executable not found"


def read_platform_settings(platform: PlatformType) -> Dict[str, Any]:
    path = get_platform_settings_path(platform)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_platform_settings(platform: PlatformType, settings: Dict[str, Any]) -> None:
    path = get_platform_settings_path(platform)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def sync_to_platform(
    platform: PlatformType,
    servers: List[Server],
    logger: Optional[MCPManagerLogger] = None,
) -> Dict[str, List]:
    """Write our registry's local stdio servers into the editor's settings.

    Preserves any existing `mcpServers` entries the user has added by hand;
    only entries with matching names are overwritten.
    """
    logger = logger or MCPManagerLogger()
    settings = read_platform_settings(platform)
    settings.setdefault("mcpServers", {})

    configured: List[str] = []
    skipped: List[Dict[str, str]] = []

    for server in servers:
        entry = build_mcp_server_entry(server, platform)
        if entry is None:
            reason = _entry_skip_reason(server)
            skipped.append({"name": server.name, "reason": reason})
            logger.debug(f"Skipping {server.name} for {platform.value}: {reason}")
            continue
        settings["mcpServers"][server.name] = entry
        configured.append(server.name)

    write_platform_settings(platform, settings)
    logger.info(f"Synced {len(configured)} server(s) to {platform.value}")
    return {"configured": configured, "skipped": skipped}


def get_platform_status() -> Dict[str, Dict[str, Any]]:
    """Return status info per platform: installed, settings path, server count."""
    status: Dict[str, Dict[str, Any]] = {}
    for p in PlatformType:
        path = get_platform_settings_path(p)
        settings = read_platform_settings(p)
        status[p.value] = {
            "installed": path.parent.exists(),
            "settings_path": str(path),
            "server_count": len(settings.get("mcpServers", {})),
        }
    return status
