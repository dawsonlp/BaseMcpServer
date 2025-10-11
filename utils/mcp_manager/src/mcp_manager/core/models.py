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


# Removal-related models

class FileInfo(BaseModel):
    """Information about a file to be removed."""
    path: Path
    size_mb: float
    type: str  # venv, log, config, source, etc.
    exists: bool = True
    
    @classmethod
    def from_path(cls, path: Path, file_type: str) -> "FileInfo":
        """Create FileInfo from a path."""
        exists = path.exists()
        size_mb = 0.0
        
        if exists:
            try:
                if path.is_file():
                    size_mb = path.stat().st_size / (1024 * 1024)
                elif path.is_dir():
                    # Calculate directory size
                    total_size = sum(
                        f.stat().st_size 
                        for f in path.rglob('*') 
                        if f.is_file()
                    )
                    size_mb = total_size / (1024 * 1024)
            except (OSError, PermissionError):
                pass
        
        return cls(
            path=path,
            size_mb=round(size_mb, 2),
            type=file_type,
            exists=exists
        )


class BackupInfo(BaseModel):
    """Information about a backup file."""
    path: Path
    timestamp: datetime
    size_mb: float
    config_type: str  # registry, cline, claude
    
    @classmethod
    def from_path(cls, path: Path, config_type: str) -> "BackupInfo":
        """Create BackupInfo from a backup file path."""
        # Extract timestamp from filename: name.backup.YYYYMMDD_HHMMSS.ext
        # Example: servers.backup.20250929_141530.json
        import re
        timestamp_match = re.search(r'\.backup\.(\d{8}_\d{6})\.', path.name)
        
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        else:
            # Fallback to file modification time
            timestamp = datetime.fromtimestamp(path.stat().st_mtime)
        
        size_mb = path.stat().st_size / (1024 * 1024) if path.exists() else 0.0
        
        return cls(
            path=path,
            timestamp=timestamp,
            size_mb=round(size_mb, 2),
            config_type=config_type
        )


class RemovalImpact(BaseModel):
    """Impact analysis for server removal."""
    server_name: str
    registry_exists: bool
    platform_configs: Dict[str, bool]  # platform_name -> exists
    files_to_remove: List[FileInfo]
    total_size_mb: float
    is_running: bool
    warnings: List[str] = Field(default_factory=list)
    
    def calculate_total_size(self):
        """Calculate total size of all files to be removed."""
        self.total_size_mb = sum(f.size_mb for f in self.files_to_remove if f.exists)
        self.total_size_mb = round(self.total_size_mb, 2)


class CleanupResult(BaseModel):
    """Result of file cleanup operation."""
    success: bool
    cleaned_files: List[Path] = Field(default_factory=list)
    failed_files: Dict[Path, str] = Field(default_factory=dict)  # path -> error message
    space_freed_mb: float = 0.0
    errors: List[str] = Field(default_factory=list)
    
    def add_cleaned_file(self, path: Path, size_mb: float):
        """Add a successfully cleaned file."""
        self.cleaned_files.append(path)
        self.space_freed_mb += size_mb
        self.space_freed_mb = round(self.space_freed_mb, 2)
    
    def add_failed_file(self, path: Path, error: str):
        """Add a file that failed to clean."""
        self.failed_files[path] = error
        self.errors.append(f"Failed to remove {path}: {error}")
        self.success = False


class RemovalResult(BaseModel):
    """Result of a removal operation."""
    success: bool
    server_name: str
    removed_from: List[str] = Field(default_factory=list)  # registry, cline, claude
    cleaned_files: List[Path] = Field(default_factory=list)
    space_freed_mb: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    backups_created: List[Path] = Field(default_factory=list)
    
    def add_removal(self, location: str):
        """Add a successful removal location."""
        self.removed_from.append(location)
    
    def add_backup(self, backup_path: Path):
        """Add a created backup."""
        self.backups_created.append(backup_path)
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def merge_cleanup_result(self, cleanup_result: CleanupResult):
        """Merge results from file cleanup."""
        self.cleaned_files.extend(cleanup_result.cleaned_files)
        self.space_freed_mb += cleanup_result.space_freed_mb
        self.space_freed_mb = round(self.space_freed_mb, 2)
        self.errors.extend(cleanup_result.errors)
        if not cleanup_result.success:
            self.success = False
