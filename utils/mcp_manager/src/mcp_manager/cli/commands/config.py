"""
Configuration commands: validate server config, and sync the registry into
every AI platform. These are the two config operations the CLI exposes; the
registry (servers.json) remains the single source of truth and `sync` is the
one-way fan-out into each platform's settings.
"""

from typing import Optional

from mcp_manager.core.models import PlatformType
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.platforms import discover_installed_platforms, sync_to_platform
from mcp_manager.core.validation import validate_server_config
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError

output = get_output_manager()
state = get_state_manager()


def validate_config(name: Optional[str] = None) -> None:
    """Validate one server's configuration, or all of them."""
    try:
        if name:
            server = state.get_server(name)
            if not server:
                raise MCPManagerError(f"Server '{name}' not found")
            result = validate_server_config(server)
            if result.is_valid:
                output.success(f"Server '{name}' configuration is valid")
            else:
                output.error(f"Server '{name}' configuration is invalid:")
                for error in result.errors:
                    output.error(f"  • {error.message}")
                    if error.suggestion:
                        output.info(f"    Suggestion: {error.suggestion}")
            for warning in result.warnings:
                output.warning(f"  • {warning.message}")
            return

        servers = state.get_servers()
        if not servers:
            output.info("No servers to validate")
            return
        valid = 0
        for server_name, server in servers.items():
            result = validate_server_config(server)
            if result.is_valid:
                valid += 1
                output.success(f"✓ {server_name}")
            else:
                output.error(f"✗ {server_name}:")
                for error in result.errors:
                    output.error(f"    • {error.message}")
        output.info(f"Validation complete: {valid}/{len(servers)} servers valid")
    except Exception as e:
        handle_error(e, "Failed to validate configuration")


_PLATFORM_ALIASES = {
    "cline": PlatformType.CLINE,
    "claude": PlatformType.CLAUDE_DESKTOP,
    "claude-desktop": PlatformType.CLAUDE_DESKTOP,
    "claude-code": PlatformType.CLAUDE_CODE,
    "claudecode": PlatformType.CLAUDE_CODE,
    "code": PlatformType.VSCODE,
    "vscode": PlatformType.VSCODE,
    "codex": PlatformType.CODEX,
    "antigravity": PlatformType.ANTIGRAVITY,
    "agy": PlatformType.ANTIGRAVITY,
}


def sync_platforms(platform: Optional[str] = None) -> None:
    """Push the current server registry into each AI platform's settings.

    Hand-added entries are preserved; only entries whose name matches a
    registered server are overwritten. Non-local / non-stdio servers are
    skipped (editor settings only express local stdio commands).
    """
    try:
        if platform:
            key = platform.lower()
            if key not in _PLATFORM_ALIASES:
                raise MCPManagerError(
                    f"Unknown platform: {platform!r}. "
                    f"Valid choices: {', '.join(sorted(_PLATFORM_ALIASES))}."
                )
            platforms = [_PLATFORM_ALIASES[key]]
        else:
            platforms = discover_installed_platforms()
            if not platforms:
                output.warning("No supported platforms detected on this system.")
                return

        servers = list(state.get_servers().values())
        if not servers:
            output.warning("No servers registered. Install one with `mcp-manager install`.")
            return

        for platform_type in platforms:
            output.info(f"Syncing {len(servers)} server(s) to {platform_type.value}...")
            result = sync_to_platform(platform_type, servers)
            for name in result["configured"]:
                output.success(f"  ✓ {name}")
            for skip in result["skipped"]:
                output.warning(f"  skipped {skip['name']}: {skip['reason']}")
    except Exception as e:
        handle_error(e, "Failed to sync platforms")
