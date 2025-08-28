"""
Core state management for MCP Manager 3.0.

This module provides centralized state management, directory structure,
and configuration handling.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

from mcp_manager.core.models import (
    Server, ServerState, ProcessInfo, SystemInfo, PlatformInfo,
    ProcessStatus, HealthStatus, ConfigStatus, SyncStatus
)


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


def get_processes_file() -> Path:
    """Get the path to the processes tracking file."""
    return get_config_dir() / "processes.json"


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


def migrate_from_old_location() -> bool:
    """Migrate existing data from ~/.mcp_servers to ~/.config/mcp-manager."""
    old_home = Path.home() / ".mcp_servers"
    new_home = get_mcp_home()
    
    # If old directory exists and new directory doesn't exist (or is empty)
    if old_home.exists() and not new_home.exists():
        try:
            # Create parent directory
            new_home.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the entire old directory to new location
            shutil.copytree(old_home, new_home)
            
            print(f"✓ Migrated MCP manager data from {old_home} to {new_home}")
            return True
        except Exception as e:
            print(f"⚠ Warning: Failed to migrate data from {old_home}: {e}")
            return False
    
    return False


def create_directory_structure() -> None:
    """Create the MCP directory structure if it doesn't exist."""
    # First, try to migrate from old location
    migrate_from_old_location()
    
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
        registry_file.write_text('{"servers": {}, "version": "3.0", "created_at": "' + 
                               datetime.now().isoformat() + '"}')
    
    processes_file = get_processes_file()
    if not processes_file.exists():
        processes_file.write_text('{"processes": {}, "last_updated": "' + 
                                datetime.now().isoformat() + '"}')


class StateManager:
    """Centralized state management for all servers."""
    
    def __init__(self):
        self.config_dir = get_mcp_home()
        self.registry_file = get_registry_file()
        self.processes_file = get_processes_file()
        self._servers_cache: Optional[Dict[str, Server]] = None
        self._processes_cache: Optional[Dict[str, ProcessInfo]] = None
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
            servers = {}
            
            for name, server_data in data.get("servers", {}).items():
                try:
                    servers[name] = Server.model_validate(server_data)
                except Exception as e:
                    print(f"Warning: Failed to load server {name}: {e}")
            
            return servers
        except Exception as e:
            print(f"Error loading servers registry: {e}")
            return {}
    
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
                "version": "3.0",
                "last_updated": datetime.now().isoformat()
            }
            
            # Write to file
            self.registry_file.write_text(json.dumps(registry_data, indent=2))
            
            # Clear cache to force reload
            self._servers_cache = None
            
        except Exception as e:
            raise RuntimeError(f"Failed to save servers registry: {e}")
    
    def _load_processes(self) -> Dict[str, ProcessInfo]:
        """Load process information from file."""
        if not self.processes_file.exists():
            return {}
        
        try:
            data = json.loads(self.processes_file.read_text())
            processes = {}
            
            for name, process_data in data.get("processes", {}).items():
                try:
                    processes[name] = ProcessInfo.model_validate(process_data)
                except Exception as e:
                    print(f"Warning: Failed to load process info for {name}: {e}")
            
            return processes
        except Exception as e:
            print(f"Error loading process information: {e}")
            return {}
    
    def _save_processes(self, processes: Dict[str, ProcessInfo]):
        """Save process information to file."""
        try:
            # Convert processes to dict format
            processes_data = {}
            for name, process in processes.items():
                processes_data[name] = process.model_dump(mode='json')
            
            # Create processes structure
            data = {
                "processes": processes_data,
                "last_updated": datetime.now().isoformat()
            }
            
            # Write to file
            self.processes_file.write_text(json.dumps(data, indent=2))
            
            # Clear cache to force reload
            self._processes_cache = None
            
        except Exception as e:
            raise RuntimeError(f"Failed to save process information: {e}")
    
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
    
    def get_processes(self) -> Dict[str, ProcessInfo]:
        """Get all running processes."""
        if self._processes_cache is None or self._should_refresh_cache():
            self._processes_cache = self._load_processes()
        
        return self._processes_cache.copy()
    
    def get_process(self, name: str) -> Optional[ProcessInfo]:
        """Get process information for a specific server."""
        processes = self.get_processes()
        return processes.get(name)
    
    def add_process(self, process: ProcessInfo) -> None:
        """Add process information for a running server."""
        processes = self.get_processes()
        processes[process.server_name] = process
        self._save_processes(processes)
    
    def remove_process(self, name: str) -> None:
        """Remove process information for a server."""
        processes = self.get_processes()
        
        if name in processes:
            del processes[name]
            self._save_processes(processes)
    
    def get_server_state(self, name: str) -> Optional[ServerState]:
        """Get complete state information for a server."""
        server = self.get_server(name)
        if not server:
            return None
        
        process = self.get_process(name)
        
        # Create server state
        state = ServerState(
            name=name,
            server=server,
            process_info=process
        )
        
        # Update state from process information
        state.update_from_process()
        
        # Determine configuration status
        if server.is_local() and server.config_file:
            if server.config_file.exists():
                state.config_status = ConfigStatus.VALID
            else:
                state.config_status = ConfigStatus.MISSING
        else:
            state.config_status = ConfigStatus.VALID
        
        # Check platform sync status
        state.platform_sync = self._get_platform_sync_status(name)
        
        return state
    
    def get_all_server_states(self) -> Dict[str, ServerState]:
        """Get state information for all servers."""
        servers = self.get_servers()
        states = {}
        
        for name in servers.keys():
            state = self.get_server_state(name)
            if state:
                states[name] = state
        
        return states
    
    def _get_platform_sync_status(self, name: str) -> Dict[str, SyncStatus]:
        """Check sync status across platforms for a server."""
        sync_status = {}
        
        # Check VS Code/Cline
        cline_path = get_vscode_cline_settings_path()
        if cline_path.exists():
            try:
                cline_config = json.loads(cline_path.read_text())
                if name in cline_config.get("mcpServers", {}):
                    sync_status["cline"] = SyncStatus.SYNCED
                else:
                    sync_status["cline"] = SyncStatus.OUT_OF_SYNC
            except Exception:
                sync_status["cline"] = SyncStatus.ERROR
        else:
            sync_status["cline"] = SyncStatus.NOT_CONFIGURED
        
        # Check Claude Desktop
        claude_path = get_claude_desktop_settings_path()
        if claude_path.exists():
            try:
                claude_config = json.loads(claude_path.read_text())
                if name in claude_config.get("mcpServers", {}):
                    sync_status["claude"] = SyncStatus.SYNCED
                else:
                    sync_status["claude"] = SyncStatus.OUT_OF_SYNC
            except Exception:
                sync_status["claude"] = SyncStatus.ERROR
        else:
            sync_status["claude"] = SyncStatus.NOT_CONFIGURED
        
        return sync_status
    
    def get_system_info(self) -> SystemInfo:
        """Get comprehensive system information."""
        import sys
        import platform
        
        servers = self.get_servers()
        states = self.get_all_server_states()
        
        running_count = sum(1 for state in states.values() if state.is_running())
        
        # Get platform information
        platforms = []
        
        # Check VS Code/Cline
        cline_path = get_vscode_cline_settings_path()
        cline_info = PlatformInfo(
            name="cline",
            display_name="VS Code Cline",
            installed=cline_path.parent.exists(),
            config_path=cline_path if cline_path.exists() else None,
        )
        if cline_path.exists():
            try:
                config = json.loads(cline_path.read_text())
                cline_info.server_count = len(config.get("mcpServers", {}))
                cline_info.sync_status = SyncStatus.SYNCED
            except Exception:
                cline_info.sync_status = SyncStatus.ERROR
        platforms.append(cline_info)
        
        # Check Claude Desktop
        claude_path = get_claude_desktop_settings_path()
        claude_info = PlatformInfo(
            name="claude",
            display_name="Claude Desktop",
            installed=claude_path.parent.exists(),
            config_path=claude_path if claude_path.exists() else None,
        )
        if claude_path.exists():
            try:
                config = json.loads(claude_path.read_text())
                claude_info.server_count = len(config.get("mcpServers", {}))
                claude_info.sync_status = SyncStatus.SYNCED
            except Exception:
                claude_info.sync_status = SyncStatus.ERROR
        platforms.append(claude_info)
        
        # Calculate disk usage
        try:
            mcp_home = get_mcp_home()
            total_size = 0
            for file_path in mcp_home.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            disk_usage_mb = total_size // (1024 * 1024)
        except Exception:
            disk_usage_mb = 0
        
        return SystemInfo(
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            platform=platform.system(),
            mcp_home=get_mcp_home(),
            total_servers=len(servers),
            running_servers=running_count,
            platforms=platforms,
            disk_usage_mb=disk_usage_mb
        )
    
    def cleanup_stale_processes(self) -> List[str]:
        """Remove stale process entries and return list of cleaned up servers."""
        processes = self.get_processes()
        cleaned = []
        
        for name, process in list(processes.items()):
            if not process.is_running():
                del processes[name]
                cleaned.append(name)
        
        if cleaned:
            self._save_processes(processes)
        
        return cleaned


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
