"""
Infrastructure adapter for file system operations.

This module implements file system ports using standard Python libraries.
"""

import os
import stat
from datetime import datetime
from typing import Any, Dict

from domain.ports import FileSystemPort, Logger


class StandardFileSystemAdapter(FileSystemPort):
    """Adapter for file system operations using standard Python libraries."""

    def __init__(self, logger: Logger):
        self._logger = logger

    def read_file(self, file_path: str) -> bytes:
        """Read file content from the file system."""
        try:
            self._logger.debug(f"Reading file: {file_path}")
            
            # Resolve path to absolute
            abs_path = os.path.abspath(file_path)
            
            # Security check - ensure path is readable
            if not self.file_exists(abs_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(abs_path, 'rb') as f:
                content = f.read()
            
            self._logger.debug(f"Read {len(content)} bytes from {file_path}")
            return content
            
        except Exception as e:
            self._logger.error(f"Failed to read file {file_path}: {str(e)}")
            raise

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        try:
            abs_path = os.path.abspath(file_path)
            return os.path.isfile(abs_path)
        except Exception as e:
            self._logger.error(f"Error checking file existence {file_path}: {str(e)}")
            return False

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information (size, modified time, etc.)."""
        try:
            self._logger.debug(f"Getting file info for: {file_path}")
            
            abs_path = os.path.abspath(file_path)
            
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            stat_result = os.stat(abs_path)
            
            info = {
                "path": abs_path,
                "size": stat_result.st_size,
                "size_mb": round(stat_result.st_size / (1024 * 1024), 2),
                "modified_time": datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
                "created_time": datetime.fromtimestamp(stat_result.st_ctime).isoformat(),
                "accessed_time": datetime.fromtimestamp(stat_result.st_atime).isoformat(),
                "is_file": os.path.isfile(abs_path),
                "is_directory": os.path.isdir(abs_path),
                "is_readable": os.access(abs_path, os.R_OK),
                "is_writable": os.access(abs_path, os.W_OK),
                "permissions": oct(stat_result.st_mode)[-3:],  # Last 3 digits
                "owner_uid": stat_result.st_uid,
                "group_gid": stat_result.st_gid,
            }
            
            # Add filename and extension
            filename = os.path.basename(abs_path)
            info["filename"] = filename
            info["basename"] = os.path.splitext(filename)[0]
            info["extension"] = os.path.splitext(filename)[1].lstrip('.')
            
            # Add directory information
            info["directory"] = os.path.dirname(abs_path)
            info["parent_directory"] = os.path.basename(os.path.dirname(abs_path))
            
            self._logger.debug(f"File info retrieved for {file_path}: {info['size']} bytes")
            return info
            
        except Exception as e:
            self._logger.error(f"Failed to get file info for {file_path}: {str(e)}")
            raise

    def resolve_path(self, file_path: str) -> str:
        """Resolve a file path to an absolute path."""
        try:
            # Expand user directory (~) and environment variables
            expanded_path = os.path.expanduser(os.path.expandvars(file_path))
            
            # Convert to absolute path
            abs_path = os.path.abspath(expanded_path)
            
            # Normalize the path (resolve . and .. components)
            normalized_path = os.path.normpath(abs_path)
            
            self._logger.debug(f"Resolved path: {file_path} -> {normalized_path}")
            return normalized_path
            
        except Exception as e:
            self._logger.error(f"Failed to resolve path {file_path}: {str(e)}")
            raise ValueError(f"Cannot resolve path: {str(e)}")


class FileUploadPolicyAdapter:
    """Adapter for file upload policy management."""

    def __init__(self, logger: Logger):
        self._logger = logger
        self._default_policy = None

    def get_default_policy(self):
        """Get the default file upload policy."""
        if self._default_policy is None:
            from domain.file_models import FileUploadPolicy
            self._default_policy = FileUploadPolicy.get_default_policy()
        return self._default_policy

    def get_policy_for_instance(self, instance_name: str):
        """Get file upload policy for a specific Jira instance."""
        # For now, return default policy
        # This could be extended to read instance-specific policies from config
        self._logger.debug(f"Using default policy for instance: {instance_name}")
        return self.get_default_policy()

    def get_policy_for_project(self, project_key: str, instance_name: str | None = None):
        """Get file upload policy for a specific project."""
        # For now, return default policy
        # This could be extended to read project-specific policies from config
        self._logger.debug(f"Using default policy for project: {project_key}")
        return self.get_default_policy()

    def validate_against_policy(
        self, 
        filename: str, 
        mime_type: str, 
        size_bytes: int, 
        policy
    ) -> tuple[bool, str | None]:
        """Validate a file against a policy."""
        try:
            return policy.is_file_allowed(filename, mime_type, size_bytes)
        except Exception as e:
            self._logger.error(f"Error validating against policy: {str(e)}")
            return False, f"Policy validation error: {str(e)}"
