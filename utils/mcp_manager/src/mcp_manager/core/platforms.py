"""
Platform integration system for MCP Manager.

This module provides integration with various MCP client platforms like
VS Code/Cline and Claude Desktop, handling configuration synchronization,
discovery, and platform-specific features.
"""

import json
import os
import platform
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from mcp_manager.core.models import Server, PlatformType, ServerType, TransportType
from mcp_manager.core.logging import MCPManagerLogger


class PlatformConfig(BaseModel):
    """Platform-specific configuration."""
    platform: PlatformType
    config_path: Path
    servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    last_sync: Optional[datetime] = None
    sync_enabled: bool = True
    auto_sync: bool = True


class PlatformAdapter(ABC):
    """Abstract base class for platform adapters."""
    
    def __init__(self, logger: Optional[MCPManagerLogger] = None):
        self.logger = logger or MCPManagerLogger()
        self._config: Optional[PlatformConfig] = None
    
    @property
    @abstractmethod
    def platform_type(self) -> PlatformType:
        """Return the platform type this adapter handles."""
        pass
    
    @property
    @abstractmethod
    def config_paths(self) -> List[Path]:
        """Return possible configuration file paths for this platform."""
        pass
    
    @abstractmethod
    def is_installed(self) -> bool:
        """Check if the platform is installed on this system."""
        pass
    
    @abstractmethod
    def discover_config(self) -> Optional[Path]:
        """Discover the platform's configuration file."""
        pass
    
    @abstractmethod
    def read_config(self, config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Read the platform's configuration."""
        pass
    
    @abstractmethod
    def write_config(self, config: Dict[str, Any], config_path: Optional[Path] = None) -> bool:
        """Write configuration to the platform."""
        pass
    
    @abstractmethod
    def get_servers(self) -> List[Server]:
        """Get all servers configured for this platform."""
        pass
    
    @abstractmethod
    def add_server(self, server: Server) -> bool:
        """Add a server to the platform configuration."""
        pass
    
    @abstractmethod
    def remove_server(self, server_name: str) -> bool:
        """Remove a server from the platform configuration."""
        pass
    
    @abstractmethod
    def sync_from_platform(self) -> List[Server]:
        """Sync servers from platform to MCP Manager."""
        pass
    
    @abstractmethod
    def sync_to_platform(self, servers: List[Server]) -> bool:
        """Sync servers from MCP Manager to platform."""
        pass


class ClinePlatformAdapter(PlatformAdapter):
    """Adapter for VS Code/Cline platform integration."""
    
    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.CLINE
    
    @property
    def config_paths(self) -> List[Path]:
        """VS Code/Cline configuration paths."""
        home = Path.home()
        
        # Different paths based on operating system
        if platform.system() == "Darwin":  # macOS
            base_path = home / "Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings"
        elif platform.system() == "Windows":
            base_path = home / "AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings"
        else:  # Linux
            base_path = home / ".config/Code/User/globalStorage/saoudrizwan.claude-dev/settings"
        
        return [
            base_path / "cline_mcp_settings.json",
            base_path / "mcp_settings.json"  # Alternative name
        ]
    
    def is_installed(self) -> bool:
        """Check if VS Code/Cline is installed."""
        try:
            # Check for VS Code installation
            if platform.system() == "Darwin":
                vscode_path = Path("/Applications/Visual Studio Code.app")
            elif platform.system() == "Windows":
                vscode_path = Path("C:/Users") / os.environ.get("USERNAME", "") / "AppData/Local/Programs/Microsoft VS Code"
            else:  # Linux
                vscode_path = Path("/usr/bin/code") 
            
            # Also check if the extension directory exists
            for config_path in self.config_paths:
                if config_path.parent.exists():
                    return True
            
            return vscode_path.exists()
        except Exception as e:
            self.logger.debug(f"Error checking VS Code/Cline installation: {e}")
            return False
    
    def discover_config(self) -> Optional[Path]:
        """Discover VS Code/Cline configuration file."""
        for config_path in self.config_paths:
            if config_path.exists():
                return config_path
        
        # Return the first path as default (will be created if needed)
        return self.config_paths[0]
    
    def read_config(self, config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Read VS Code/Cline MCP configuration."""
        if not config_path:
            config_path = self.discover_config()
        
        if not config_path or not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading Cline config from {config_path}: {e}")
            return None
    
    def write_config(self, config: Dict[str, Any], config_path: Optional[Path] = None) -> bool:
        """Write configuration to VS Code/Cline."""
        if not config_path:
            config_path = self.discover_config()
        
        if not config_path:
            return False
        
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with proper formatting
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Updated Cline configuration at {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing Cline config to {config_path}: {e}")
            return False
    
    def get_servers(self) -> List[Server]:
        """Get all servers configured in VS Code/Cline."""
        config = self.read_config()
        if not config or 'mcpServers' not in config:
            return []
        
        servers = []
        for name, server_config in config['mcpServers'].items():
            try:
                # Parse Cline server configuration
                server = self._parse_cline_server(name, server_config)
                if server:
                    servers.append(server)
            except Exception as e:
                self.logger.warning(f"Error parsing Cline server {name}: {e}")
        
        return servers
    
    def _parse_cline_server(self, name: str, config: Dict[str, Any]) -> Optional[Server]:
        """Parse a Cline server configuration into our Server model."""
        try:
            # Determine transport type
            if 'command' in config:
                transport = TransportType.STDIO
                command = config['command']
                args = config.get('args', [])
                port = None
                host = None
            elif 'url' in config:
                transport = TransportType.SSE
                command = None
                args = []
                # Parse URL for host/port
                url = config['url']
                if '://' in url:
                    # Extract host/port from URL
                    parts = url.split('://', 1)[1].split('/', 1)
                    host_port = parts[0]
                    if ':' in host_port:
                        host, port_str = host_port.rsplit(':', 1)
                        port = int(port_str)
                    else:
                        host = host_port
                        port = 80 if url.startswith('http://') else 443
                else:
                    host = 'localhost'
                    port = None
            else:
                self.logger.warning(f"Unknown server configuration format for {name}")
                return None
            
            # Determine server type (best guess)
            server_type = ServerType.PIPX  # Default assumption for Cline servers
            
            return Server(
                name=name,
                type=server_type,
                transport=transport,
                command=command,
                args=args,
                port=port,
                host=host,
                env=config.get('env', {}),
                enabled=True,  # Assume enabled if in Cline config
                description=f"Imported from Cline configuration",
                metadata={
                    'imported_from': 'cline',
                    'original_config': config
                }
            )
        except Exception as e:
            self.logger.error(f"Error parsing Cline server {name}: {e}")
            return None
    
    def _server_to_cline_config(self, server: Server) -> Dict[str, Any]:
        """Convert our Server model to Cline configuration format."""
        if server.transport == TransportType.STDIO:
            config = {
                'command': server.command,
                'args': server.args or []
            }
        elif server.transport == TransportType.SSE:
            # Construct URL
            protocol = 'https' if server.port == 443 else 'http'
            host = server.host or 'localhost'
            url = f"{protocol}://{host}"
            if server.port and server.port not in [80, 443]:
                url += f":{server.port}"
            config = {'url': url}
        else:
            raise ValueError(f"Unsupported transport type: {server.transport}")
        
        if server.env:
            config['env'] = server.env
        
        return config
    
    def add_server(self, server: Server) -> bool:
        """Add a server to VS Code/Cline configuration."""
        config = self.read_config() or {}
        
        if 'mcpServers' not in config:
            config['mcpServers'] = {}
        
        try:
            cline_config = self._server_to_cline_config(server)
            config['mcpServers'][server.name] = cline_config
            return self.write_config(config)
        except Exception as e:
            self.logger.error(f"Error adding server {server.name} to Cline: {e}")
            return False
    
    def remove_server(self, server_name: str) -> bool:
        """Remove a server from VS Code/Cline configuration."""
        config = self.read_config()
        if not config or 'mcpServers' not in config:
            return True  # Already not present
        
        if server_name in config['mcpServers']:
            del config['mcpServers'][server_name]
            return self.write_config(config)
        
        return True  # Server wasn't present
    
    def sync_from_platform(self) -> List[Server]:
        """Import servers from VS Code/Cline to MCP Manager."""
        return self.get_servers()
    
    def sync_to_platform(self, servers: List[Server]) -> bool:
        """Export servers from MCP Manager to VS Code/Cline."""
        config = self.read_config() or {}
        
        if 'mcpServers' not in config:
            config['mcpServers'] = {}
        
        # Clear existing servers and add all from MCP Manager
        config['mcpServers'] = {}
        
        for server in servers:
            try:
                cline_config = self._server_to_cline_config(server)
                config['mcpServers'][server.name] = cline_config
            except Exception as e:
                self.logger.warning(f"Skipping server {server.name} - conversion error: {e}")
        
        return self.write_config(config)


class ClaudeDesktopAdapter(PlatformAdapter):
    """Adapter for Claude Desktop platform integration."""
    
    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.CLAUDE_DESKTOP
    
    @property
    def config_paths(self) -> List[Path]:
        """Claude Desktop configuration paths."""
        home = Path.home()
        
        if platform.system() == "Darwin":  # macOS
            return [home / "Library/Application Support/Claude/claude_desktop_config.json"]
        elif platform.system() == "Windows":
            return [home / "AppData/Roaming/Claude/claude_desktop_config.json"]
        else:  # Linux
            return [home / ".config/claude/claude_desktop_config.json"]
    
    def is_installed(self) -> bool:
        """Check if Claude Desktop is installed."""
        try:
            if platform.system() == "Darwin":
                app_path = Path("/Applications/Claude.app")
                return app_path.exists()
            elif platform.system() == "Windows":
                # Check common installation paths
                program_files = Path("C:/Program Files/Claude")
                program_files_x86 = Path("C:/Program Files (x86)/Claude")
                return program_files.exists() or program_files_x86.exists()
            else:  # Linux
                # Check if claude command is available or config directory exists
                for config_path in self.config_paths:
                    if config_path.parent.exists():
                        return True
                return False
        except Exception as e:
            self.logger.debug(f"Error checking Claude Desktop installation: {e}")
            return False
    
    def discover_config(self) -> Optional[Path]:
        """Discover Claude Desktop configuration file."""
        for config_path in self.config_paths:
            if config_path.exists():
                return config_path
        
        # Return the first path as default
        return self.config_paths[0]
    
    def read_config(self, config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Read Claude Desktop configuration."""
        if not config_path:
            config_path = self.discover_config()
        
        if not config_path or not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading Claude Desktop config from {config_path}: {e}")
            return None
    
    def write_config(self, config: Dict[str, Any], config_path: Optional[Path] = None) -> bool:
        """Write configuration to Claude Desktop."""
        if not config_path:
            config_path = self.discover_config()
        
        if not config_path:
            return False
        
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with proper formatting
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Updated Claude Desktop configuration at {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing Claude Desktop config to {config_path}: {e}")
            return False
    
    def get_servers(self) -> List[Server]:
        """Get all servers configured in Claude Desktop."""
        config = self.read_config()
        if not config or 'mcpServers' not in config:
            return []
        
        servers = []
        for name, server_config in config['mcpServers'].items():
            try:
                server = self._parse_claude_server(name, server_config)
                if server:
                    servers.append(server)
            except Exception as e:
                self.logger.warning(f"Error parsing Claude Desktop server {name}: {e}")
        
        return servers
    
    def _parse_claude_server(self, name: str, config: Dict[str, Any]) -> Optional[Server]:
        """Parse a Claude Desktop server configuration."""
        try:
            # Claude Desktop uses similar format to Cline
            if 'command' in config:
                transport = TransportType.STDIO
                command = config['command']
                args = config.get('args', [])
                port = None
                host = None
            else:
                self.logger.warning(f"Unknown Claude Desktop server configuration format for {name}")
                return None
            
            return Server(
                name=name,
                type=ServerType.PIPX,  # Default assumption
                transport=transport,
                command=command,
                args=args,
                port=port,
                host=host,
                env=config.get('env', {}),
                enabled=True,
                description=f"Imported from Claude Desktop configuration",
                metadata={
                    'imported_from': 'claude_desktop',
                    'original_config': config
                }
            )
        except Exception as e:
            self.logger.error(f"Error parsing Claude Desktop server {name}: {e}")
            return None
    
    def _server_to_claude_config(self, server: Server) -> Dict[str, Any]:
        """Convert our Server model to Claude Desktop configuration format."""
        if server.transport != TransportType.STDIO:
            raise ValueError("Claude Desktop only supports stdio transport")
        
        config = {
            'command': server.command,
            'args': server.args or []
        }
        
        if server.env:
            config['env'] = server.env
        
        return config
    
    def add_server(self, server: Server) -> bool:
        """Add a server to Claude Desktop configuration."""
        config = self.read_config() or {}
        
        if 'mcpServers' not in config:
            config['mcpServers'] = {}
        
        try:
            claude_config = self._server_to_claude_config(server)
            config['mcpServers'][server.name] = claude_config
            return self.write_config(config)
        except Exception as e:
            self.logger.error(f"Error adding server {server.name} to Claude Desktop: {e}")
            return False
    
    def remove_server(self, server_name: str) -> bool:
        """Remove a server from Claude Desktop configuration."""
        config = self.read_config()
        if not config or 'mcpServers' not in config:
            return True
        
        if server_name in config['mcpServers']:
            del config['mcpServers'][server_name]
            return self.write_config(config)
        
        return True
    
    def sync_from_platform(self) -> List[Server]:
        """Import servers from Claude Desktop to MCP Manager."""
        return self.get_servers()
    
    def sync_to_platform(self, servers: List[Server]) -> bool:
        """Export servers from MCP Manager to Claude Desktop."""
        config = self.read_config() or {}
        
        if 'mcpServers' not in config:
            config['mcpServers'] = {}
        
        # Clear existing servers and add all from MCP Manager
        config['mcpServers'] = {}
        
        for server in servers:
            try:
                # Only add stdio servers to Claude Desktop
                if server.transport == TransportType.STDIO:
                    claude_config = self._server_to_claude_config(server)
                    config['mcpServers'][server.name] = claude_config
                else:
                    self.logger.info(f"Skipping server {server.name} - Claude Desktop only supports stdio transport")
            except Exception as e:
                self.logger.warning(f"Skipping server {server.name} - conversion error: {e}")
        
        return self.write_config(config)


class PlatformManager:
    """Manages integration with multiple MCP client platforms."""
    
    def __init__(self, logger: Optional[MCPManagerLogger] = None):
        self.logger = logger or MCPManagerLogger()
        self._adapters: Dict[PlatformType, PlatformAdapter] = {}
        
        # Register platform adapters
        self._register_adapters()
    
    def _register_adapters(self) -> None:
        """Register all available platform adapters."""
        self._adapters[PlatformType.CLINE] = ClinePlatformAdapter(self.logger)
        self._adapters[PlatformType.CLAUDE_DESKTOP] = ClaudeDesktopAdapter(self.logger)
    
    def get_adapter(self, platform: PlatformType) -> Optional[PlatformAdapter]:
        """Get adapter for a specific platform."""
        return self._adapters.get(platform)
    
    def discover_platforms(self) -> List[PlatformType]:
        """Discover which platforms are installed on this system."""
        installed = []
        for platform_type, adapter in self._adapters.items():
            if adapter.is_installed():
                installed.append(platform_type)
        return installed
    
    def get_platform_configs(self) -> List[PlatformConfig]:
        """Get configuration information for all discovered platforms."""
        configs = []
        
        for platform_type in self.discover_platforms():
            adapter = self._adapters[platform_type]
            config_path = adapter.discover_config()
            
            if config_path:
                platform_config = PlatformConfig(
                    platform=platform_type,
                    config_path=config_path,
                    servers={},  # Will be populated on demand
                    sync_enabled=True
                )
                configs.append(platform_config)
        
        return configs
    
    def sync_from_platform(self, platform: PlatformType) -> List[Server]:
        """Import servers from a specific platform."""
        adapter = self._adapters.get(platform)
        if not adapter:
            raise ValueError(f"No adapter available for platform: {platform}")
        
        return adapter.sync_from_platform()
    
    def sync_to_platform(self, platform: PlatformType, servers: List[Server]) -> bool:
        """Export servers to a specific platform."""
        adapter = self._adapters.get(platform)
        if not adapter:
            raise ValueError(f"No adapter available for platform: {platform}")
        
        return adapter.sync_to_platform(servers)
    
    def sync_all_platforms(self, servers: List[Server], platforms: Optional[List[PlatformType]] = None) -> Dict[PlatformType, bool]:
        """Sync servers to all or specified platforms."""
        results = {}
        
        target_platforms = platforms or self.discover_platforms()
        
        for platform_type in target_platforms:
            try:
                result = self.sync_to_platform(platform_type, servers)
                results[platform_type] = result
                if result:
                    self.logger.info(f"Successfully synced to {platform_type.value}")
                else:
                    self.logger.warning(f"Failed to sync to {platform_type.value}")
            except Exception as e:
                self.logger.error(f"Error syncing to {platform_type.value}: {e}")
                results[platform_type] = False
        
        return results
    
    def import_from_all_platforms(self) -> Dict[PlatformType, List[Server]]:
        """Import servers from all discovered platforms."""
        results = {}
        
        for platform_type in self.discover_platforms():
            try:
                servers = self.sync_from_platform(platform_type)
                results[platform_type] = servers
                self.logger.info(f"Imported {len(servers)} servers from {platform_type.value}")
            except Exception as e:
                self.logger.error(f"Error importing from {platform_type.value}: {e}")
                results[platform_type] = []
        
        return results
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get status information for all platforms."""
        status = {}
        
        for platform_type, adapter in self._adapters.items():
            platform_status = {
                'installed': adapter.is_installed(),
                'config_path': None,
                'servers_count': 0,
                'last_sync': None
            }
            
            if platform_status['installed']:
                config_path = adapter.discover_config()
                if config_path:
                    platform_status['config_path'] = str(config_path)
                    try:
                        servers = adapter.get_servers()
                        platform_status['servers_count'] = len(servers)
                    except Exception as e:
                        self.logger.debug(f"Error counting servers for {platform_type.value}: {e}")
            
            status[platform_type.value] = platform_status
        
        return status
