"""
Backup management for MCP Manager.

Handles creation, restoration, and management of configuration backups.
"""

import json
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from mcp_manager.core.models import BackupInfo
from mcp_manager.core.state import get_config_dir


class BackupManager:
    """Manages configuration backups with automatic retention."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory for backups (default: ~/.config/mcp-manager/backups)
        """
        self.backup_dir = backup_dir or (get_config_dir() / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 10
    
    def create_backup(
        self,
        config_file: Path,
        prefix: str = "backup"
    ) -> Path:
        """
        Create a timestamped backup of a configuration file.
        
        Args:
            config_file: Path to the config file to backup
            prefix: Prefix for the backup filename (default: "backup")
        
        Returns:
            Path to the created backup file
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            OSError: If backup creation fails
        """
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_file.stem}.{prefix}.{timestamp}{config_file.suffix}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Copy the file
            shutil.copy2(config_file, backup_path)
            return backup_path
        except Exception as e:
            raise OSError(f"Failed to create backup: {e}")
    
    def list_backups(
        self,
        config_type: str,
        limit: Optional[int] = None
    ) -> List[BackupInfo]:
        """
        List available backups for a specific configuration type.
        
        Args:
            config_type: Type of config (registry, cline, claude)
            limit: Maximum number of backups to return (newest first)
        
        Returns:
            List of BackupInfo objects, sorted by timestamp (newest first)
        """
        # Determine filename pattern based on config type
        patterns = {
            "registry": "servers.backup.*.json",
            "cline": "cline_mcp_settings.backup.*.json",
            "claude": "claude_desktop_config.backup.*.json"
        }
        
        pattern = patterns.get(config_type, f"*.backup.*.json")
        backup_files = list(self.backup_dir.glob(pattern))
        
        # Create BackupInfo objects
        backups = [
            BackupInfo.from_path(path, config_type)
            for path in backup_files
            if path.is_file()
        ]
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b.timestamp, reverse=True)
        
        # Apply limit if specified
        if limit:
            backups = backups[:limit]
        
        return backups
    
    def restore_backup(
        self,
        backup_file: Path,
        target_file: Path,
        create_backup_of_target: bool = True
    ) -> bool:
        """
        Restore a backup file to its original location.
        
        Args:
            backup_file: Path to the backup file
            target_file: Path where to restore the backup
            create_backup_of_target: Whether to backup existing target first
        
        Returns:
            True if restoration successful
        
        Raises:
            FileNotFoundError: If backup file doesn't exist
            OSError: If restoration fails
        """
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        try:
            # Validate backup file is valid JSON/YAML
            try:
                content = backup_file.read_text()
                json.loads(content)  # Validate it's valid JSON
            except json.JSONDecodeError as e:
                raise OSError(f"Backup file is not valid JSON: {e}")
            
            # Create backup of current target if it exists
            if create_backup_of_target and target_file.exists():
                self.create_backup(target_file, prefix="pre-restore")
            
            # Ensure target directory exists
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore the backup
            shutil.copy2(backup_file, target_file)
            return True
            
        except Exception as e:
            raise OSError(f"Failed to restore backup: {e}")
    
    def cleanup_old_backups(
        self,
        config_type: Optional[str] = None,
        keep_count: int = 10
    ) -> int:
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            config_type: Type of config to clean (None = all types)
            keep_count: Number of backups to keep per type
        
        Returns:
            Number of backup files removed
        """
        removed_count = 0
        
        if config_type:
            # Clean specific config type
            config_types = [config_type]
        else:
            # Clean all config types
            config_types = ["registry", "cline", "claude"]
        
        for cfg_type in config_types:
            backups = self.list_backups(cfg_type)
            
            # Remove old backups beyond keep_count
            if len(backups) > keep_count:
                old_backups = backups[keep_count:]
                for backup in old_backups:
                    try:
                        backup.path.unlink()
                        removed_count += 1
                    except OSError:
                        # Continue on error
                        pass
        
        return removed_count
    
    def get_backup_by_timestamp(
        self,
        config_type: str,
        timestamp_str: str
    ) -> Optional[BackupInfo]:
        """
        Get a specific backup by its timestamp string.
        
        Args:
            config_type: Type of config (registry, cline, claude)
            timestamp_str: Timestamp string in format YYYYMMDD_HHMMSS
        
        Returns:
            BackupInfo if found, None otherwise
        """
        backups = self.list_backups(config_type)
        
        try:
            target_timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
            for backup in backups:
                if backup.timestamp == target_timestamp:
                    return backup
        except ValueError:
            # Invalid timestamp format
            pass
        
        return None
    
    def get_latest_backup(
        self,
        config_type: str
    ) -> Optional[BackupInfo]:
        """
        Get the most recent backup for a configuration type.
        
        Args:
            config_type: Type of config (registry, cline, claude)
        
        Returns:
            BackupInfo if found, None otherwise
        """
        backups = self.list_backups(config_type, limit=1)
        return backups[0] if backups else None
    
    def get_total_backup_size(self) -> float:
        """
        Calculate total size of all backups in MB.
        
        Returns:
            Total size in MB
        """
        total_size = 0.0
        
        for backup_file in self.backup_dir.glob("*.backup.*"):
            if backup_file.is_file():
                try:
                    total_size += backup_file.stat().st_size
                except OSError:
                    pass
        
        return round(total_size / (1024 * 1024), 2)


# Global backup manager instance
_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """Get the global backup manager instance."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
