"""
Platform integration for MCP Manager.

Writes the per-editor MCP settings for the local servers that mcp-manager
owns. Two mechanisms are supported:

* File-based editors (Cline, Claude Desktop, VS Code native MCP) keep a JSON
  settings file with a map of server entries. They differ only in the map's
  top-level key and a few per-entry extras, captured by `_FileProfile`.
* CLI-managed agents (Claude Code, Codex) keep their MCP servers inside a
  large, live-mutated config file (`~/.claude.json`, `~/.codex/config.toml`).
  Rewriting those by hand risks corrupting unrelated state, so we delegate to
  each agent's own `mcp add` / `mcp remove` CLI instead (`_CliSpec`).

Scope is intentionally narrow: build entries from the current `Server` model
and push them to the agent. Reading arbitrary external entries back into the
registry isn't supported because the `Server` model assumes mcp-manager owns
the install (venv_dir + source_dir).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from mcp_manager.core.logging import MCPManagerLogger
from mcp_manager.core.models import PlatformType, Server, ServerType, TransportType
from mcp_manager.core.state import (
    get_claude_desktop_settings_path,
    get_vscode_cline_settings_path,
    get_vscode_mcp_settings_path,
)


# --------------------------------------------------------------------------
# Platform profiles
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _FileProfile:
    """How a file-based editor stores its MCP server map.

    container_key: top-level JSON key holding the server map.
    include_type:  emit an explicit ``"type": "stdio"`` on each entry.
    cline_extras:  emit Cline's ``disabled`` / ``autoApprove`` fields.
    """

    container_key: str = "mcpServers"
    include_type: bool = False
    cline_extras: bool = False


@dataclass(frozen=True)
class _CliSpec:
    """How a CLI-managed agent adds/removes an MCP server."""

    binary: str
    add_argv: Callable[[str, str, List[str], Dict[str, str]], List[str]]
    remove_argv: Callable[[str], List[str]]


_FILE_PROFILES: Dict[PlatformType, _FileProfile] = {
    PlatformType.CLINE: _FileProfile(cline_extras=True),
    PlatformType.CLAUDE_DESKTOP: _FileProfile(),
    PlatformType.VSCODE: _FileProfile(container_key="servers", include_type=True),
}

_PLATFORM_SETTINGS_PATH_FACTORY = {
    PlatformType.CLINE: get_vscode_cline_settings_path,
    PlatformType.CLAUDE_DESKTOP: get_claude_desktop_settings_path,
    PlatformType.VSCODE: get_vscode_mcp_settings_path,
}


def _claude_add_argv(name: str, cmd: str, args: List[str], env: Dict[str, str]) -> List[str]:
    # claude mcp add [-s user] [-e K=V ...] <name> -- <cmd> <args...>
    argv = ["claude", "mcp", "add", "-s", "user"]
    for k, v in env.items():
        argv += ["-e", f"{k}={v}"]
    argv += [name, "--", cmd, *args]
    return argv


def _claude_remove_argv(name: str) -> List[str]:
    return ["claude", "mcp", "remove", "-s", "user", name]


def _codex_add_argv(name: str, cmd: str, args: List[str], env: Dict[str, str]) -> List[str]:
    # codex mcp add [--env K=V ...] <name> -- <cmd> <args...>
    argv = ["codex", "mcp", "add"]
    for k, v in env.items():
        argv += ["--env", f"{k}={v}"]
    argv += [name, "--", cmd, *args]
    return argv


def _codex_remove_argv(name: str) -> List[str]:
    return ["codex", "mcp", "remove", name]


_CLI_SPECS: Dict[PlatformType, _CliSpec] = {
    PlatformType.CLAUDE_CODE: _CliSpec("claude", _claude_add_argv, _claude_remove_argv),
    PlatformType.CODEX: _CliSpec("codex", _codex_add_argv, _codex_remove_argv),
}


def is_cli_platform(platform: PlatformType) -> bool:
    """True if the platform is managed via its own `mcp` CLI, not a JSON file."""
    return platform in _CLI_SPECS


def platform_container_key(platform: PlatformType) -> str:
    """Top-level JSON key that holds the server map for a file-based platform."""
    return _FILE_PROFILES[platform].container_key


def remove_from_cli_platform(platform: PlatformType, name: str) -> Tuple[bool, str]:
    """Remove a server from a CLI-managed agent via its own `mcp remove`.

    Returns (success, message). A missing entry is reported as a failure with
    the CLI's message; callers can treat that as a warning.
    """
    spec = _CLI_SPECS[platform]
    if shutil.which(spec.binary) is None:
        return False, f"`{spec.binary}` not found on PATH"
    result = subprocess.run(spec.remove_argv(name), capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        return False, (detail[-1] if detail else "remove failed")
    return True, "removed"


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


def get_platform_settings_path(platform: PlatformType) -> Path:
    factory = _PLATFORM_SETTINGS_PATH_FACTORY.get(platform)
    if factory is None:
        raise ValueError(f"{platform.value} has no settings file (CLI-managed)")
    return factory()


def is_platform_installed(platform: PlatformType) -> bool:
    """Whether the agent looks present on this system.

    CLI-managed agents count as installed when their binary is on PATH;
    file-based editors when their settings directory exists.
    """
    if is_cli_platform(platform):
        return shutil.which(_CLI_SPECS[platform].binary) is not None
    return get_platform_settings_path(platform).parent.exists()


def discover_installed_platforms() -> List[PlatformType]:
    return [p for p in PlatformType if is_platform_installed(p)]


# --------------------------------------------------------------------------
# Command resolution
# --------------------------------------------------------------------------


def _resolve_console_script(server: Server) -> Optional[str]:
    """Name of the console script that launches this server's MCP entry point.

    mcp-manager's convention is that the script equals the server name, but a
    server may rename its script (e.g. to avoid colliding with a dependency
    that ships an identically-named CLI). The authoritative declaration is the
    `[project.scripts]` table in the server's own pyproject.toml — dependency
    scripts never appear there. Returns None when it can't be determined, so
    callers fall back to `server.name` (correct for convention-following
    servers, and for installs whose source dir is no longer present).
    """
    if not server.source_dir:
        return None
    pyproject = server.source_dir / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None

    scripts = data.get("project", {}).get("scripts", {})
    names = list(scripts)
    if not names:
        return None
    # Convention holds: a script matching the server name is the entry point.
    if server.name in names:
        return server.name
    # Single declared script is unambiguous.
    if len(names) == 1:
        return names[0]
    # Multiple scripts, none matching the name: prefer the MCP-suffixed one.
    mcp_scripts = [n for n in names if n.endswith("-mcp")]
    if len(mcp_scripts) == 1:
        return mcp_scripts[0]
    return None


def _server_executable_path(server: Server) -> Optional[Path]:
    if not server.venv_dir:
        return None
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    suffix = ".exe" if sys.platform == "win32" else ""
    script_name = _resolve_console_script(server) or server.name
    return server.venv_dir / bin_dir / f"{script_name}{suffix}"


def _resolved_command(server: Server) -> Optional[Tuple[str, List[str]]]:
    """The (command, args) to launch a syncable local stdio server, or None.

    Shared by both the file-based entry builder and the CLI adapters so they
    agree on which servers are expressible and how they're launched.
    """
    if server.server_type != ServerType.LOCAL:
        return None
    if server.transport != TransportType.STDIO:
        return None
    executable_path = _server_executable_path(server)
    if not executable_path or not executable_path.exists():
        return None
    return str(executable_path), ["stdio"]


def _entry_skip_reason(server: Server) -> str:
    if server.server_type != ServerType.LOCAL:
        return "remote server"
    if server.transport != TransportType.STDIO:
        return f"unsupported transport: {server.transport.value}"
    if not server.venv_dir:
        return "no venv_dir"
    return "executable not found"


# --------------------------------------------------------------------------
# File-based sync
# --------------------------------------------------------------------------


def build_mcp_server_entry(server: Server, platform: PlatformType) -> Optional[Dict[str, Any]]:
    """Build the settings entry for one server, or None if it can't be expressed.

    Only local stdio servers are expressible; remote/SSE servers return None so
    callers can skip them with a meaningful reason.
    """
    profile = _FILE_PROFILES.get(platform)
    if profile is None:
        return None

    resolved = _resolved_command(server)
    if resolved is None:
        return None
    command, args = resolved

    entry: Dict[str, Any] = {}
    if profile.include_type:
        entry["type"] = "stdio"
    entry["command"] = command
    entry["args"] = args
    if server.environment:
        entry["env"] = dict(server.environment)

    if profile.cline_extras:
        entry["disabled"] = not server.enabled
        entry["autoApprove"] = list(server.auto_approve)

    return entry


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


def _sync_to_file_platform(
    platform: PlatformType,
    servers: List[Server],
    logger: MCPManagerLogger,
) -> Dict[str, List]:
    profile = _FILE_PROFILES[platform]
    settings = read_platform_settings(platform)
    container = settings.setdefault(profile.container_key, {})

    configured: List[str] = []
    skipped: List[Dict[str, str]] = []

    for server in servers:
        entry = build_mcp_server_entry(server, platform)
        if entry is None:
            reason = _entry_skip_reason(server)
            skipped.append({"name": server.name, "reason": reason})
            logger.debug(f"Skipping {server.name} for {platform.value}: {reason}")
            continue
        container[server.name] = entry
        configured.append(server.name)

    write_platform_settings(platform, settings)
    logger.info(f"Synced {len(configured)} server(s) to {platform.value}")
    return {"configured": configured, "skipped": skipped}


# --------------------------------------------------------------------------
# CLI-based sync
# --------------------------------------------------------------------------


def _sync_to_cli_platform(
    platform: PlatformType,
    servers: List[Server],
    logger: MCPManagerLogger,
) -> Dict[str, List]:
    spec = _CLI_SPECS[platform]
    configured: List[str] = []
    skipped: List[Dict[str, str]] = []

    if shutil.which(spec.binary) is None:
        for server in servers:
            skipped.append({"name": server.name, "reason": f"`{spec.binary}` not found on PATH"})
        return {"configured": configured, "skipped": skipped}

    for server in servers:
        resolved = _resolved_command(server)
        if resolved is None:
            reason = _entry_skip_reason(server)
            skipped.append({"name": server.name, "reason": reason})
            logger.debug(f"Skipping {server.name} for {platform.value}: {reason}")
            continue
        command, args = resolved
        env = dict(server.environment or {})

        # Replace any existing entry: remove (ignoring "not found") then add.
        subprocess.run(spec.remove_argv(server.name), capture_output=True, text=True)
        result = subprocess.run(
            spec.add_argv(server.name, command, args, env),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip().splitlines()
            reason = f"`{spec.binary} mcp add` failed: {detail[-1] if detail else 'unknown error'}"
            skipped.append({"name": server.name, "reason": reason})
            logger.debug(f"{spec.binary} mcp add {server.name} failed: {result.stderr}")
            continue
        configured.append(server.name)

    logger.info(f"Synced {len(configured)} server(s) to {platform.value}")
    return {"configured": configured, "skipped": skipped}


# --------------------------------------------------------------------------
# Public sync entry point
# --------------------------------------------------------------------------


def sync_to_platform(
    platform: PlatformType,
    servers: List[Server],
    logger: Optional[MCPManagerLogger] = None,
) -> Dict[str, List]:
    """Push the registry's local stdio servers into one agent's config.

    For file-based editors, existing entries the user added by hand are
    preserved; only entries with a matching name are overwritten. For
    CLI-managed agents, each server is (re)registered via the agent's own
    `mcp add` command. Remote servers and non-stdio transports are skipped.
    """
    logger = logger or MCPManagerLogger()
    if is_cli_platform(platform):
        return _sync_to_cli_platform(platform, servers, logger)
    return _sync_to_file_platform(platform, servers, logger)


def get_platform_status() -> Dict[str, Dict[str, Any]]:
    """Return status info per platform: installed, settings location, count."""
    status: Dict[str, Dict[str, Any]] = {}
    for p in PlatformType:
        if is_cli_platform(p):
            status[p.value] = {
                "installed": is_platform_installed(p),
                "settings_path": f"(managed by `{_CLI_SPECS[p].binary} mcp`)",
                "server_count": None,
            }
            continue
        path = get_platform_settings_path(p)
        settings = read_platform_settings(p)
        profile = _FILE_PROFILES[p]
        status[p.value] = {
            "installed": path.parent.exists(),
            "settings_path": str(path),
            "server_count": len(settings.get(profile.container_key, {})),
        }
    return status
