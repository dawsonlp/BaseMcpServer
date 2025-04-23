"""
Server models and management logic for MCP servers.

This module defines the data models for different types of MCP servers
(local stdio, local HTTP+SSE, and remote HTTP+SSE) and provides
functions for server management.
"""

from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any, Union, Literal
import json
import os
import shutil
from datetime import datetime


class ServerType(str, Enum):
    """Types of MCP servers that can be managed."""
    
    LOCAL_STDIO = "local_stdio"
    LOCAL_SSE = "local_sse"
    REMOTE_SSE = "remote_sse"


class ServerBase(BaseModel):
    """Base model for all types of MCP servers."""
    
    name: str
    server_type: ServerType
    disabled: bool = False
    auto_approve: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LocalServer(ServerBase):
    """Model for locally installed MCP servers."""
    
    source_dir: Path
    venv_dir: Path
    requirements_file: Optional[Path] = None
    wrapper_path: Optional[Path] = None
    port: Optional[int] = None  # Only used for LOCAL_SSE
    
    @validator('server_type')
    def validate_server_type(cls, v):
        if v not in [ServerType.LOCAL_STDIO, ServerType.LOCAL_SSE]:
            raise ValueError(f"Server type must be LOCAL_STDIO or LOCAL_SSE for LocalServer, got {v}")
        return v


class RemoteServer(ServerBase):
    """Model for remote MCP servers accessible via HTTP+SSE."""
    
    url: HttpUrl
    api_key: str
    
    @validator('server_type')
    def validate_server_type(cls, v):
        if v != ServerType.REMOTE_SSE:
            raise ValueError(f"Server type must be REMOTE_SSE for RemoteServer, got {v}")
        return v
    
    @validator('url')
    def validate_url(cls, v):
        # Ensure SSE endpoint is properly formatted
        str_url = str(v)
        if not str_url.endswith('/sse'):
            return HttpUrl(f"{str_url}/sse")
        return v


Server = Union[LocalServer, RemoteServer]


class ServerRegistry(BaseModel):
    """Registry of all configured MCP servers."""
    
    servers: Dict[str, Server] = Field(default_factory=dict)
    
    @classmethod
    def load(cls, path: Path) -> 'ServerRegistry':
        """Load server registry from a JSON file."""
        if not path.exists():
            return cls()
        
        try:
            data = json.loads(path.read_text())
            return cls.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to load server registry from {path}: {e}")
    
    def save(self, path: Path) -> None:
        """Save server registry to a JSON file."""
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        path.write_text(self.model_dump_json(indent=2))
    
    def add_server(self, server: Server) -> None:
        """Add a server to the registry."""
        if server.name in self.servers:
            raise ValueError(f"Server with name '{server.name}' already exists")
        
        self.servers[server.name] = server
    
    def get_server(self, name: str) -> Server:
        """Get a server by name."""
        if name not in self.servers:
            raise ValueError(f"Server with name '{name}' not found")
        
        return self.servers[name]
    
    def remove_server(self, name: str) -> None:
        """Remove a server from the registry."""
        if name not in self.servers:
            raise ValueError(f"Server with name '{name}' not found")
        
        del self.servers[name]
    
    def update_server(self, name: str, server: Server) -> None:
        """Update a server in the registry."""
        if name not in self.servers:
            raise ValueError(f"Server with name '{name}' not found")
        
        self.servers[name] = server


def get_mcp_home() -> Path:
    """Get the MCP home directory."""
    return Path.home() / ".mcp_servers"


def get_server_dir(name: str) -> Path:
    """Get the directory for a local server."""
    return get_mcp_home() / "servers" / name


def get_bin_dir() -> Path:
    """Get the directory for wrapper scripts."""
    return get_mcp_home() / "bin"


def get_config_dir() -> Path:
    """Get the directory for configuration files."""
    return get_mcp_home() / "config"


def get_registry_path() -> Path:
    """Get the path to the server registry file."""
    return get_config_dir() / "servers.json"


def get_vscode_cline_settings_path() -> Path:
    """Get the path to the VS Code Cline settings file."""
    return Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"


def create_directory_structure() -> None:
    """Create the MCP directory structure if it doesn't exist."""
    # Create main directories
    get_mcp_home().mkdir(parents=True, exist_ok=True)
    get_server_dir("").parent.mkdir(parents=True, exist_ok=True)
    get_bin_dir().mkdir(parents=True, exist_ok=True)
    get_config_dir().mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (get_config_dir() / "editors").mkdir(parents=True, exist_ok=True)
    
    # Create empty registry if it doesn't exist
    if not get_registry_path().exists():
        ServerRegistry().save(get_registry_path())
