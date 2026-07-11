"""
Core state management for MCP Manager.

This module provides centralized state management, directory structure,
and configuration handling.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

from mcp_manager import __version__
from mcp_manager.core.models import Server


def get_mcp_home() -> Path:
    """Get the MCP home directory."""
    return Path.home() / ".config" / "mcp-manager"


def get_server_dir(name: str) -> Path:
    """Get the directory for a local server."""
    return get_mcp_home() / "servers" / name


def get_bin_dir() -> Path:
    """Get the directory for wrapper scripts."""
    return get_mcp_home() / "bin"


def get_config_dir() -> Path:
    """Get the directory for configuration files."""
    return get_mcp_home() / "config"


def get_logs_dir() -> Path:
    """Get the directory for log files."""
    return get_mcp_home() / "logs"


def get_registry_file() -> Path:
    """Get the path to the server registry file."""
    return get_config_dir() / "servers.json"


def get_vscode_cline_settings_path() -> Path:
    """Get the path to the VS Code Cline settings file."""
    import sys
    
    if sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    elif sys.platform == "win32":  # Windows
        return Path.home() / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    else:  # Linux and others
        return Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"


def get_claude_desktop_settings_path() -> Path:
    """Get the path to the Claude Desktop settings file."""
    import sys

    if sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":  # Windows
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:  # Linux and others
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def get_vscode_mcp_settings_path() -> Path:
    """Get the path to VS Code's native MCP settings file (`mcp.json`).

    This is VS Code's own MCP support (Copilot), distinct from the Cline
    extension. Entries live under a top-level `servers` key.
    """
    import sys

    if sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
    elif sys.platform == "win32":  # Windows
        return Path.home() / "AppData" / "Roaming" / "Code" / "User" / "mcp.json"
    else:  # Linux and others
        return Path.home() / ".config" / "Code" / "User" / "mcp.json"


def get_antigravity_mcp_settings_path() -> Path:
    """Get the path to Antigravity's MCP config file (`mcp_config.json`).

    Antigravity (Google) reads local stdio MCP servers from its Gemini config
    home, using the standard `mcpServers` format (command/args/env). The path is
    home-relative (not an OS app-data dir), so it is the same on every platform.
    (Note: `~/.antigravity/` holds Antigravity's VS Code extension data, not the
    MCP config — the config lives under `~/.gemini/config/`.)
    """
    return Path.home() / ".gemini" / "config" / "mcp_config.json"


def create_directory_structure() -> None:
    """Create the MCP directory structure if it doesn't exist."""
    # Create main directories
    directories = [
        get_mcp_home(),
        get_server_dir("").parent,  # servers directory
        get_bin_dir(),
        get_config_dir(),
        get_logs_dir(),
        get_config_dir() / "editors",
        get_config_dir() / "templates",
        get_config_dir() / "backups"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create empty files if they don't exist
    registry_file = get_registry_file()
    if not registry_file.exists():
        registry_file.write_text(json.dumps({
            "servers": {},
            "version": __version__,
            "created_at": datetime.now().isoformat(),
        }, indent=2))


class StateManager:
    """Centralized state management for all servers."""
    
    def __init__(self):
        self.config_dir = get_mcp_home()
        self.registry_file = get_registry_file()
        self._servers_cache: Optional[Dict[str, Server]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 30  # Cache for 30 seconds
    
    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed."""
        if self._cache_timestamp is None:
            return True
        
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age > self._cache_ttl_seconds
    
    def _load_servers(self) -> Dict[str, Server]:
        """Load servers from registry file."""
        if not self.registry_file.exists():
            return {}

        try:
            data = json.loads(self.registry_file.read_text())
        except Exception as e:
            print(f"Error reading servers registry: {e}")
            return {}

        servers: Dict[str, Server] = {}
        legacy_skipped: list[str] = []

        for name, server_data in data.get("servers", {}).items():
            try:
                servers[name] = Server.model_validate(server_data)
            except Exception as e:
                legacy_skipped.append(name)
                print(f"Warning: skipped registry entry {name!r}: {e}")

        if legacy_skipped:
            print(
                f"\n{len(legacy_skipped)} server registry entr{'y' if len(legacy_skipped) == 1 else 'ies'} "
                "could not be loaded (likely from a pre-1.2.0 mcp-manager).\n"
                "Reinstall each with:\n"
                "  mcp-manager install <name> --source <path> --force\n"
                "Per-server config.yaml files in ~/.config/mcp-manager/servers/<name>/ "
                "(API keys, credentials) are preserved automatically on reinstall.\n"
            )

        return servers
    
    def _save_servers(self, servers: Dict[str, Server]):
        """Save servers to registry file."""
        try:
            # Convert servers to dict format
            servers_data = {}
            for name, server in servers.items():
                servers_data[name] = server.model_dump(mode='json')
            
            # Create registry structure
            registry_data = {
                "servers": servers_data,
                "version": __version__,
                "last_updated": datetime.now().isoformat()
            }
            
            # Write to file
            self.registry_file.write_text(json.dumps(registry_data, indent=2))
            
            # Clear cache to force reload
            self._servers_cache = None
            
        except Exception as e:
            raise RuntimeError(f"Failed to save servers registry: {e}")
    
    def get_servers(self) -> Dict[str, Server]:
        """Get all servers, using cache if available."""
        if self._servers_cache is None or self._should_refresh_cache():
            self._servers_cache = self._load_servers()
            self._cache_timestamp = datetime.now()
        
        return self._servers_cache.copy()
    
    def get_server(self, name: str) -> Optional[Server]:
        """Get a specific server by name."""
        servers = self.get_servers()
        return servers.get(name)
    
    def add_server(self, server: Server) -> None:
        """Add a new server to the registry."""
        servers = self.get_servers()
        
        if server.name in servers:
            raise ValueError(f"Server with name '{server.name}' already exists")
        
        servers[server.name] = server
        self._save_servers(servers)
    
    def update_server(self, server: Server) -> None:
        """Update an existing server in the registry."""
        servers = self.get_servers()
        
        if server.name not in servers:
            raise ValueError(f"Server with name '{server.name}' does not exist")
        
        server.updated_at = datetime.now()
        servers[server.name] = server
        self._save_servers(servers)
    
    def remove_server(self, name: str) -> None:
        """Remove a server from the registry."""
        servers = self.get_servers()
        
        if name not in servers:
            raise ValueError(f"Server with name '{name}' does not exist")
        
        del servers[name]
        self._save_servers(servers)
    


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
