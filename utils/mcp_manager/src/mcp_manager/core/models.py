"""
Core data models for MCP Manager 3.0.

Defines all data structures used throughout the application.
"""

from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import json


class ServerType(str, Enum):
    """Types of MCP servers."""
    LOCAL = "local"
    REMOTE = "remote"


class TransportType(str, Enum):
    """Transport protocols for MCP servers."""
    STDIO = "stdio"
    SSE = "sse"


class InstallationType(str, Enum):
    """Installation methods for local servers."""
    VENV = "venv"
    PIPX = "pipx"
    SYSTEM = "system"


class ProcessStatus(str, Enum):
    """Process status states."""
    RUNNING = "running"
    STOPPED = "stopped"
    CRASHED = "crashed"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


class HealthStatus(str, Enum):
    """Health status indicators."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ConfigStatus(str, Enum):
    """Configuration status."""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    UNKNOWN = "unknown"


class SyncStatus(str, Enum):
    """Platform sync status."""
    SYNCED = "synced"
    OUT_OF_SYNC = "out_of_sync"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"


class SourceType(str, Enum):
    """Server installation source types."""
    LOCAL = "local"
    GIT = "git"
    TEMPLATE = "template"
    UNKNOWN = "unknown"


class PlatformType(str, Enum):
    """AI platform types."""
    CLINE = "cline"
    CLAUDE_DESKTOP = "claude_desktop"


class Server(BaseModel):
    """Base server model."""
    name: str
    server_type: ServerType
    transport: TransportType = TransportType.STDIO
    enabled: bool = True
    auto_approve: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Local server specific fields
    source_dir: Optional[Path] = None
    source_type: Optional[SourceType] = None
    installation_type: Optional[InstallationType] = None
    venv_dir: Optional[Path] = None
    requirements_file: Optional[Path] = None
    port: Optional[int] = None
    
    # Remote server specific fields
    url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    
    # Configuration
    config_file: Optional[Path] = None
    environment: Dict[str, str] = Field(default_factory=dict)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Server name must contain only alphanumeric characters, hyphens, and underscores")
        return v
    
    @validator('server_type', pre=True)
    def convert_legacy_server_type(cls, v):
        """Convert legacy server type values for backward compatibility."""
        if isinstance(v, str):
            # Convert legacy values to new enum values
            legacy_mapping = {
                'local_stdio': 'local',
                'local_sse': 'local',
                'remote_stdio': 'remote',
                'remote_sse': 'remote'
            }
            return legacy_mapping.get(v, v)
        return v
    
    def is_local(self) -> bool:
        return self.server_type == ServerType.LOCAL
    
    def is_remote(self) -> bool:
        return self.server_type == ServerType.REMOTE
    
    def get_main_script_path(self) -> Optional[Path]:
        """Get the path to the main.py script."""
        if not self.is_local() or not self.source_dir:
            return None
        
        # Check common locations
        for path in [
            self.source_dir / "main.py",
            self.source_dir / "src" / "main.py",
            self.source_dir / "code" / "main.py"
        ]:
            if path.exists():
                return path
        
        return None
    
    def get_python_executable(self) -> Optional[Path]:
        """Get the Python executable path for this server."""
        if not self.is_local() or not self.venv_dir:
            return None
        
        import sys
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "python.exe"
        else:
            return self.venv_dir / "bin" / "python"


class ProcessInfo(BaseModel):
    """Information about a running process."""
    pid: int
    server_name: str
    transport: TransportType
    port: Optional[int] = None
    started_at: datetime
    command: List[str]
    working_dir: Path
    environment: Dict[str, str] = Field(default_factory=dict)
    
    def is_running(self) -> bool:
        """Check if the process is still running."""
        try:
            import psutil
            return psutil.pid_exists(self.pid)
        except ImportError:
            # Fallback without psutil
            import os
            try:
                os.kill(self.pid, 0)
                return True
            except OSError:
                return False
    
    def get_uptime(self) -> timedelta:
        """Get process uptime."""
        return datetime.now() - self.started_at
    
    def get_memory_usage(self) -> Optional[int]:
        """Get process memory usage in MB."""
        try:
            import psutil
            process = psutil.Process(self.pid)
            return process.memory_info().rss // 1024 // 1024
        except (ImportError, psutil.NoSuchProcess):
            return None


class ServerState(BaseModel):
    """Complete state information for a server."""
    name: str
    server: Server
    process_status: ProcessStatus = ProcessStatus.STOPPED
    health_status: HealthStatus = HealthStatus.UNKNOWN
    config_status: ConfigStatus = ConfigStatus.UNKNOWN
    platform_sync: Dict[str, SyncStatus] = Field(default_factory=dict)
    
    # Runtime information
    process_info: Optional[ProcessInfo] = None
    last_error: Optional[str] = None
    last_health_check: Optional[datetime] = None
    health_score: float = 0.0
    
    # Performance metrics
    uptime: Optional[timedelta] = None
    memory_usage_mb: Optional[int] = None
    cpu_usage_percent: Optional[float] = None
    
    def is_running(self) -> bool:
        """Check if server is running."""
        return (
            self.process_status == ProcessStatus.RUNNING and
            self.process_info is not None and
            self.process_info.is_running()
        )
    
    def is_healthy(self) -> bool:
        """Check if server is healthy."""
        return self.health_status == HealthStatus.HEALTHY
    
    def update_from_process(self):
        """Update state from process information."""
        if self.process_info:
            if self.process_info.is_running():
                self.process_status = ProcessStatus.RUNNING
                self.uptime = self.process_info.get_uptime()
                self.memory_usage_mb = self.process_info.get_memory_usage()
            else:
                self.process_status = ProcessStatus.STOPPED
                self.process_info = None
                self.uptime = None
                self.memory_usage_mb = None


class HealthCheck(BaseModel):
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None


class HealthReport(BaseModel):
    """Complete health report for a server."""
    server_name: str
    overall_status: HealthStatus
    checks: List[HealthCheck]
    timestamp: datetime = Field(default_factory=datetime.now)
    health_score: float = 0.0
    
    def calculate_health_score(self):
        """Calculate overall health score (0.0 to 1.0)."""
        if not self.checks:
            self.health_score = 0.0
            return
        
        healthy_count = sum(1 for check in self.checks if check.status == HealthStatus.HEALTHY)
        self.health_score = healthy_count / len(self.checks)
        
        # Update overall status based on score
        if self.health_score >= 0.8:
            self.overall_status = HealthStatus.HEALTHY
        elif self.health_score >= 0.5:
            self.overall_status = HealthStatus.DEGRADED
        else:
            self.overall_status = HealthStatus.UNHEALTHY


class ValidationError(BaseModel):
    """Configuration validation error."""
    field: str
    message: str
    suggestion: Optional[str] = None
    severity: str = "error"  # error, warning, info


class ValidationResult(BaseModel):
    """Result of configuration validation."""
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    
    def add_error(self, field: str, message: str, suggestion: Optional[str] = None):
        """Add a validation error."""
        self.errors.append(ValidationError(
            field=field, 
            message=message, 
            suggestion=suggestion,
            severity="error"
        ))
        self.is_valid = False
    
    def add_warning(self, field: str, message: str, suggestion: Optional[str] = None):
        """Add a validation warning."""
        self.warnings.append(ValidationError(
            field=field,
            message=message, 
            suggestion=suggestion,
            severity="warning"
        ))


class PlatformInfo(BaseModel):
    """Information about an AI platform integration."""
    name: str
    display_name: str
    installed: bool = False
    config_path: Optional[Path] = None
    sync_status: SyncStatus = SyncStatus.NOT_CONFIGURED
    server_count: int = 0
    last_sync: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if platform is available for use."""
        return self.installed and self.config_path and self.config_path.exists()


class SystemInfo(BaseModel):
    """System information for diagnostics."""
    python_version: str
    platform: str
    mcp_home: Path
    total_servers: int
    running_servers: int
    platforms: List[PlatformInfo]
    disk_usage_mb: int
    last_updated: datetime = Field(default_factory=datetime.now)
