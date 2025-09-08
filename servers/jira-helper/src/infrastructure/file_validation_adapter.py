"""
Infrastructure adapter for file validation operations.

This module implements file validation ports using standard Python libraries.
"""

import mimetypes
import os
from typing import List

from domain.file_models import FileContent, FileUploadPolicy
from domain.ports import FileValidationPort, Logger


class StandardFileValidationAdapter(FileValidationPort):
    """Adapter for file validation operations using standard Python libraries."""

    def __init__(self, logger: Logger):
        self._logger = logger
        # Initialize mimetypes module
        mimetypes.init()

    def validate_file_path(self, file_path: str) -> List[str]:
        """Validate that a file path is valid and accessible."""
        errors = []
        
        try:
            # Check if path is not empty
            if not file_path or not file_path.strip():
                errors.append("File path cannot be empty")
                return errors
            
            # Resolve and normalize path
            abs_path = os.path.abspath(file_path)
            
            # Check if file exists
            if not os.path.exists(abs_path):
                errors.append(f"File does not exist: {file_path}")
                return errors
            
            # Check if it's actually a file (not a directory)
            if not os.path.isfile(abs_path):
                errors.append(f"Path is not a file: {file_path}")
                return errors
            
            # Check if file is readable
            if not os.access(abs_path, os.R_OK):
                errors.append(f"File is not readable: {file_path}")
                return errors
            
            # Check file size (basic sanity check)
            try:
                size = os.path.getsize(abs_path)
                if size == 0:
                    errors.append(f"File is empty: {file_path}")
                elif size > 100 * 1024 * 1024:  # 100MB basic limit
                    errors.append(f"File is too large (>100MB): {file_path}")
            except OSError as e:
                errors.append(f"Cannot determine file size: {str(e)}")
            
        except Exception as e:
            errors.append(f"Error validating file path: {str(e)}")
        
        return errors

    def validate_file_content(self, file_content: FileContent, policy: FileUploadPolicy) -> List[str]:
        """Validate file content against upload policy."""
        errors = []
        
        try:
            # Validate file content object itself
            if not file_content.filename or not file_content.filename.strip():
                errors.append("Filename cannot be empty")
            
            if not file_content.content:
                errors.append("File content cannot be empty")
            
            if not file_content.mime_type or not file_content.mime_type.strip():
                errors.append("MIME type cannot be empty")
            
            # Validate against policy
            is_allowed, policy_error = policy.is_file_allowed(
                file_content.filename,
                file_content.mime_type,
                len(file_content.content)
            )
            
            if not is_allowed and policy_error:
                errors.append(policy_error)
            
            # Additional content validation
            if len(file_content.content) == 0:
                errors.append("File content is empty")
            
            # Check for potentially harmful content patterns
            if self._contains_suspicious_patterns(file_content.content):
                errors.append("File content contains suspicious patterns")
            
        except Exception as e:
            errors.append(f"Error validating file content: {str(e)}")
        
        return errors

    def detect_mime_type(self, file_path: str) -> str:
        """Detect MIME type of a file."""
        try:
            # Use mimetypes module to guess based on file extension
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type:
                return mime_type
            
            # Fall back to reading file signature if available
            return self._detect_mime_type_from_signature(file_path)
            
        except Exception as e:
            self._logger.warning(f"Failed to detect MIME type for {file_path}: {str(e)}")
            return "application/octet-stream"

    def detect_mime_type_from_content(self, content: bytes, filename: str) -> str:
        """Detect MIME type from file content and filename."""
        try:
            # First try to detect from filename
            mime_type, _ = mimetypes.guess_type(filename)
            
            if mime_type:
                return mime_type
            
            # Try to detect from content signature
            return self._detect_mime_type_from_content_signature(content)
            
        except Exception as e:
            self._logger.warning(f"Failed to detect MIME type from content: {str(e)}")
            return "application/octet-stream"

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError as e:
            raise ValueError(f"Cannot get file size for {file_path}: {str(e)}")

    def is_file_readable(self, file_path: str) -> bool:
        """Check if a file is readable."""
        try:
            return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
        except Exception:
            return False

    def _detect_mime_type_from_signature(self, file_path: str) -> str:
        """Detect MIME type from file signature/magic bytes."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)  # Read first 16 bytes
                return self._detect_mime_type_from_content_signature(header)
        except Exception:
            return "application/octet-stream"

    def _detect_mime_type_from_content_signature(self, content: bytes) -> str:
        """Detect MIME type from content signature/magic bytes."""
        if not content:
            return "application/octet-stream"
        
        # Common file signatures
        signatures = {
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'\xff\xd8\xff': 'image/jpeg',
            b'GIF8': 'image/gif',
            b'%PDF': 'application/pdf',
            b'PK\x03\x04': 'application/zip',
            b'PK\x05\x06': 'application/zip',
            b'PK\x07\x08': 'application/zip',
            b'\x50\x4b\x03\x04': 'application/zip',  # ZIP/Office docs
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': 'application/msword',  # Old Office
            b'{\rtf': 'application/rtf',
            b'<?xml': 'application/xml',
            b'<html': 'text/html',
            b'<!DOCTYPE html': 'text/html',
        }
        
        # Check against known signatures
        for signature, mime_type in signatures.items():
            if content.startswith(signature):
                return mime_type
        
        # Check if it's likely text
        try:
            content[:1024].decode('utf-8')
            return 'text/plain'
        except UnicodeDecodeError:
            pass
        
        return "application/octet-stream"

    def _contains_suspicious_patterns(self, content: bytes) -> bool:
        """Check for potentially harmful content patterns."""
        try:
            # Convert to text for pattern matching (if possible)
            try:
                text_content = content.decode('utf-8', errors='ignore').lower()
                
                # List of suspicious patterns
                suspicious_patterns = [
                    '<script',
                    'javascript:',
                    'vbscript:',
                    'eval(',
                    'exec(',
                    'system(',
                    'shell_exec',
                    'passthru',
                    'file_get_contents',
                    'curl_exec',
                    'base64_decode',
                    '__import__',
                    'subprocess',
                    'os.system',
                    'Runtime.getRuntime',
                    'ProcessBuilder',
                ]
                
                # Check for suspicious patterns
                for pattern in suspicious_patterns:
                    if pattern in text_content:
                        self._logger.warning(f"Found suspicious pattern: {pattern}")
                        return True
                        
            except Exception:
                # If we can't decode as text, check binary patterns
                pass
            
            # Check for executable file signatures
            executable_signatures = [
                b'MZ',  # Windows PE
                b'\x7fELF',  # Linux ELF
                b'\xfe\xed\xfa\xce',  # Mach-O (macOS) 32-bit
                b'\xfe\xed\xfa\xcf',  # Mach-O (macOS) 64-bit
                b'\xca\xfe\xba\xbe',  # Java class file
                b'\xca\xfe\xba\xbe',  # Fat Mach-O
            ]
            
            for signature in executable_signatures:
                if content.startswith(signature):
                    self._logger.warning(f"Found executable signature")
                    return True
            
            return False
            
        except Exception as e:
            self._logger.warning(f"Error checking for suspicious patterns: {str(e)}")
            return False
