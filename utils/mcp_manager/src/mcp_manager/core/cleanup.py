"""
File cleanup management for MCP Manager.

Handles safe removal of server-related files and directories.
"""

import shutil
from pathlib import Path
from typing import List, Optional

from mcp_manager.core.models import Server, FileInfo, CleanupResult
from mcp_manager.core.state import get_server_dir, get_logs_dir


class CleanupManager:
    """Manages safe cleanup of server files and directories."""
    
    def __init__(self):
        """Initialize cleanup manager."""
        pass
    
    def cleanup_server_files(
        self,
        server: Server,
        dry_run: bool = False
    ) -> CleanupResult:
        """
        Clean up all files associated with a server.
        
        Args:
            server: Server whose files to clean up
            dry_run: If True, don't actually remove files
        
        Returns:
            CleanupResult with details of cleaned files
        """
        result = CleanupResult(success=True)
        
        # Get all files to clean
        files_to_clean = self._get_server_files(server)
        
        for file_info in files_to_clean:
            if not file_info.exists:
                # File already doesn't exist, skip
                continue
            
            if dry_run:
                # In dry run, just track what would be cleaned
                result.add_cleaned_file(file_info.path, file_info.size_mb)
            else:
                # Actually remove the file/directory
                try:
                    if file_info.path.is_file():
                        file_info.path.unlink()
                        result.add_cleaned_file(file_info.path, file_info.size_mb)
                    elif file_info.path.is_dir():
                        shutil.rmtree(file_info.path)
                        result.add_cleaned_file(file_info.path, file_info.size_mb)
                except (OSError, PermissionError) as e:
                    result.add_failed_file(file_info.path, str(e))
        
        return result
    
    def calculate_cleanup_size(self, server: Server) -> float:
        """
        Calculate total size of files that would be cleaned up.
        
        Args:
            server: Server to calculate cleanup size for
        
        Returns:
            Total size in MB
        """
        files = self._get_server_files(server)
        total_size = sum(f.size_mb for f in files if f.exists)
        return round(total_size, 2)
    
    def find_unused_files(self, server_names: List[str]) -> List[FileInfo]:
        """
        Find files in the server directories that don't belong to any server.
        
        Args:
            server_names: List of valid server names
        
        Returns:
            List of FileInfo for orphaned files
        """
        unused_files = []
        
        # Check server directory
        server_parent = get_server_dir("").parent
        if server_parent.exists():
            for item in server_parent.iterdir():
                if item.is_dir() and item.name not in server_names:
                    # This is an orphaned server directory
                    file_info = FileInfo.from_path(item, "orphaned_server")
                    unused_files.append(file_info)
        
        # Check logs directory
        logs_dir = get_logs_dir()
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                # Extract server name from log filename (server-name.log)
                server_name = log_file.stem
                if server_name not in server_names:
                    file_info = FileInfo.from_path(log_file, "orphaned_log")
                    unused_files.append(file_info)
        
        return unused_files
    
    def _get_server_files(self, server: Server) -> List[FileInfo]:
        """
        Get list of all files associated with a server.
        
        Args:
            server: Server to get files for
        
        Returns:
            List of FileInfo objects
        """
        files = []
        
        # Virtual environment directory
        if server.venv_dir:
            files.append(FileInfo.from_path(server.venv_dir, "venv"))
        
        # Source directory (only if not a shared location)
        # We should be careful not to delete source code for local development servers
        # Only delete if it's in the managed server directory
        server_managed_dir = get_server_dir(server.name)
        if server.source_dir and server.source_dir != server_managed_dir:
            # Only include if source_dir is within managed directory
            try:
                if server.source_dir.is_relative_to(server_managed_dir):
                    files.append(FileInfo.from_path(server.source_dir, "source"))
            except (ValueError, AttributeError):
                # is_relative_to may not exist in older Python or comparison fails
                # Don't include source_dir to be safe
                pass
        
        # Log file
        log_file = get_logs_dir() / f"{server.name}.log"
        files.append(FileInfo.from_path(log_file, "log"))
        
        # Config file (if in managed directory)
        if server.config_file:
            try:
                if server.config_file.is_relative_to(server_managed_dir):
                    files.append(FileInfo.from_path(server.config_file, "config"))
            except (ValueError, AttributeError):
                pass
        
        # Entire managed server directory
        files.append(FileInfo.from_path(server_managed_dir, "server_dir"))
        
        return files
    
    def calculate_directory_size(self, path: Path) -> float:
        """
        Calculate the total size of a directory in MB.
        
        Args:
            path: Directory path
        
        Returns:
            Size in MB
        """
        if not path.exists():
            return 0.0
        
        if path.is_file():
            return path.stat().st_size / (1024 * 1024)
        
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        pass
        except (OSError, PermissionError):
            # Skip directories we can't access
            pass
        
        return round(total_size / (1024 * 1024), 2)
    
    def safe_remove_file(self, path: Path) -> tuple[bool, Optional[str]]:
        """
        Safely remove a single file with error handling.
        
        Args:
            path: Path to remove
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not path.exists():
                return True, None
            
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            
            return True, None
        except PermissionError as e:
            return False, f"Permission denied: {e}"
        except OSError as e:
            return False, f"OS error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def safe_remove_directory(
        self,
        path: Path,
        recursive: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Safely remove a directory with error handling.
        
        Args:
            path: Directory path to remove
            recursive: If True, remove contents recursively
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not path.exists():
                return True, None
            
            if not path.is_dir():
                return False, "Path is not a directory"
            
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()  # Only works if directory is empty
            
            return True, None
        except PermissionError as e:
            return False, f"Permission denied: {e}"
        except OSError as e:
            return False, f"OS error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"


# Global cleanup manager instance
_cleanup_manager: Optional[CleanupManager] = None


def get_cleanup_manager() -> CleanupManager:
    """Get the global cleanup manager instance."""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = CleanupManager()
    return _cleanup_manager
