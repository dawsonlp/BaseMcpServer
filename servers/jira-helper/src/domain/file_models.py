"""
Domain models for file operations in the Jira Helper.

This module contains domain entities for file attachments and upload operations.
These models are framework-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import BinaryIO

from domain.base import validate_required_fields


class AttachmentMimeType(Enum):
    """Supported MIME types for file attachments."""
    # Documents
    PDF = "application/pdf"
    DOC = "application/msword"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLS = "application/vnd.ms-excel"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    PPT = "application/vnd.ms-powerpoint"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    
    # Text
    TXT = "text/plain"
    CSV = "text/csv"
    RTF = "application/rtf"
    
    # Images
    JPG = "image/jpeg"
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    SVG = "image/svg+xml"
    
    # Archives
    ZIP = "application/zip"
    RAR = "application/x-rar-compressed"
    TAR = "application/x-tar"
    GZIP = "application/gzip"
    
    # Code/Config
    JSON = "application/json"
    XML = "application/xml"
    YAML = "application/x-yaml"
    
    # Other
    BINARY = "application/octet-stream"


@validate_required_fields('id', 'filename', 'size', 'mime_type', 'created')
@dataclass
class JiraAttachment:
    """Represents a Jira issue attachment."""
    id: str
    filename: str
    size: int  # Size in bytes
    mime_type: str
    created: str  # ISO datetime string
    author_name: str | None = None
    author_key: str | None = None
    download_url: str | None = None
    thumbnail_url: str | None = None
    
    def __post_init__(self):
        """Validate the attachment."""
        if self.size < 0:
            raise ValueError("Attachment size cannot be negative")
        
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty")
            
        # Validate filename doesn't contain invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in self.filename for char in invalid_chars):
            raise ValueError(f"Filename contains invalid characters: {invalid_chars}")
    
    def get_size_in_mb(self) -> float:
        """Get attachment size in megabytes."""
        return self.size / (1024 * 1024)
    
    def get_size_in_kb(self) -> float:
        """Get attachment size in kilobytes."""
        return self.size / 1024
    
    def is_image(self) -> bool:
        """Check if the attachment is an image."""
        image_types = [
            AttachmentMimeType.JPG.value,
            AttachmentMimeType.JPEG.value,
            AttachmentMimeType.PNG.value,
            AttachmentMimeType.GIF.value,
            AttachmentMimeType.SVG.value
        ]
        return self.mime_type in image_types
    
    def is_document(self) -> bool:
        """Check if the attachment is a document."""
        document_types = [
            AttachmentMimeType.PDF.value,
            AttachmentMimeType.DOC.value,
            AttachmentMimeType.DOCX.value,
            AttachmentMimeType.XLS.value,
            AttachmentMimeType.XLSX.value,
            AttachmentMimeType.PPT.value,
            AttachmentMimeType.PPTX.value,
            AttachmentMimeType.TXT.value,
            AttachmentMimeType.CSV.value,
            AttachmentMimeType.RTF.value
        ]
        return self.mime_type in document_types
    
    def is_archive(self) -> bool:
        """Check if the attachment is an archive."""
        archive_types = [
            AttachmentMimeType.ZIP.value,
            AttachmentMimeType.RAR.value,
            AttachmentMimeType.TAR.value,
            AttachmentMimeType.GZIP.value
        ]
        return self.mime_type in archive_types
    
    def get_file_extension(self) -> str:
        """Get the file extension from the filename."""
        if '.' in self.filename:
            return self.filename.split('.')[-1].lower()
        return ""


@validate_required_fields('issue_key', 'file_path')
@dataclass
class FileUploadRequest:
    """Represents a request to upload a file to a Jira issue."""
    issue_key: str
    file_path: str
    comment: str | None = None
    
    def __post_init__(self):
        """Validate the file upload request."""
        if not self.issue_key.strip():
            raise ValueError("Issue key cannot be empty")
            
        if not self.file_path.strip():
            raise ValueError("File path cannot be empty")
        
        # Basic validation of issue key format (PROJECT-NUMBER)
        if '-' not in self.issue_key:
            raise ValueError("Issue key must be in format PROJECT-NUMBER (e.g., PROJ-123)")
    
    def has_comment(self) -> bool:
        """Check if a comment is included with the upload."""
        return self.comment is not None and self.comment.strip() != ""
    
    def get_filename_from_path(self) -> str:
        """Extract filename from the file path."""
        import os
        return os.path.basename(self.file_path)


@validate_required_fields('filename', 'content', 'mime_type')
@dataclass
class FileContent:
    """Represents file content for upload operations."""
    filename: str
    content: bytes
    mime_type: str
    size: int | None = None
    
    def __post_init__(self):
        """Validate and set file content properties."""
        if not self.filename.strip():
            raise ValueError("Filename cannot be empty")
            
        if not self.content:
            raise ValueError("File content cannot be empty")
        
        # Set size if not provided
        if self.size is None:
            self.size = len(self.content)
        
        # Validate size matches content length
        if self.size != len(self.content):
            raise ValueError("Size does not match content length")
    
    def get_size_in_mb(self) -> float:
        """Get file size in megabytes."""
        return self.size / (1024 * 1024) if self.size else 0
    
    def is_size_valid(self, max_size_mb: int = 10) -> bool:
        """Check if file size is within limits."""
        return self.get_size_in_mb() <= max_size_mb
    
    def get_file_extension(self) -> str:
        """Get the file extension from the filename."""
        if '.' in self.filename:
            return self.filename.split('.')[-1].lower()
        return ""


@validate_required_fields('issue_key')
@dataclass
class FileUploadResult:
    """Represents the result of a file upload operation."""
    issue_key: str
    uploaded: bool = False
    attachment: JiraAttachment | None = None
    error: str | None = None
    
    def is_successful(self) -> bool:
        """Check if the upload was successful."""
        return self.uploaded and self.error is None and self.attachment is not None
    
    def get_attachment_id(self) -> str | None:
        """Get the attachment ID if upload was successful."""
        return self.attachment.id if self.attachment else None
    
    def get_attachment_url(self) -> str | None:
        """Get the attachment download URL if available."""
        return self.attachment.download_url if self.attachment else None


@validate_required_fields('issue_key', 'attachment_id')
@dataclass
class AttachmentDeleteRequest:
    """Represents a request to delete an attachment from a Jira issue."""
    issue_key: str
    attachment_id: str
    
    def __post_init__(self):
        """Validate the attachment delete request."""
        if not self.issue_key.strip():
            raise ValueError("Issue key cannot be empty")
            
        if not self.attachment_id.strip():
            raise ValueError("Attachment ID cannot be empty")


@validate_required_fields('issue_key', 'attachment_id')
@dataclass
class AttachmentDeleteResult:
    """Represents the result of an attachment delete operation."""
    issue_key: str
    attachment_id: str
    deleted: bool = False
    error: str | None = None
    
    def is_successful(self) -> bool:
        """Check if the deletion was successful."""
        return self.deleted and self.error is None


@validate_required_fields('issue_key')
@dataclass
class AttachmentListRequest:
    """Represents a request to list attachments for a Jira issue."""
    issue_key: str
    include_thumbnails: bool = False
    
    def __post_init__(self):
        """Validate the attachment list request."""
        if not self.issue_key.strip():
            raise ValueError("Issue key cannot be empty")


@validate_required_fields('issue_key')
@dataclass
class AttachmentListResult:
    """Represents the result of listing attachments for an issue."""
    issue_key: str
    attachments: list[JiraAttachment] = field(default_factory=list)
    error: str | None = None
    
    def is_successful(self) -> bool:
        """Check if the operation was successful."""
        return self.error is None
    
    def get_attachment_count(self) -> int:
        """Get the number of attachments."""
        return len(self.attachments)
    
    def has_attachments(self) -> bool:
        """Check if the issue has any attachments."""
        return len(self.attachments) > 0
    
    def get_total_size(self) -> int:
        """Get the total size of all attachments in bytes."""
        return sum(attachment.size for attachment in self.attachments)
    
    def get_total_size_mb(self) -> float:
        """Get the total size of all attachments in megabytes."""
        return self.get_total_size() / (1024 * 1024)
    
    def get_attachments_by_type(self, mime_type: str) -> list[JiraAttachment]:
        """Get attachments filtered by MIME type."""
        return [att for att in self.attachments if att.mime_type == mime_type]
    
    def get_image_attachments(self) -> list[JiraAttachment]:
        """Get all image attachments."""
        return [att for att in self.attachments if att.is_image()]
    
    def get_document_attachments(self) -> list[JiraAttachment]:
        """Get all document attachments."""
        return [att for att in self.attachments if att.is_document()]


@validate_required_fields('max_size_mb', 'allowed_extensions')
@dataclass
class FileUploadPolicy:
    """Represents file upload policy and restrictions."""
    max_size_mb: int
    allowed_extensions: list[str] = field(default_factory=list)
    allowed_mime_types: list[str] = field(default_factory=list)
    blocked_extensions: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the file upload policy."""
        if self.max_size_mb <= 0:
            raise ValueError("Maximum size must be greater than 0")
        
        if self.max_size_mb > 100:  # Reasonable upper limit
            raise ValueError("Maximum size cannot exceed 100 MB")
        
        # Convert extensions to lowercase for consistency
        self.allowed_extensions = [ext.lower() for ext in self.allowed_extensions]
        self.blocked_extensions = [ext.lower() for ext in self.blocked_extensions]
    
    def is_file_allowed(self, filename: str, mime_type: str, size_bytes: int) -> tuple[bool, str | None]:
        """Check if a file meets the upload policy. Returns (allowed, reason)."""
        # Check size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > self.max_size_mb:
            return False, f"File size ({size_mb:.2f} MB) exceeds maximum allowed size ({self.max_size_mb} MB)"
        
        # Get file extension
        extension = ""
        if '.' in filename:
            extension = filename.split('.')[-1].lower()
        
        # Check blocked extensions
        if extension in self.blocked_extensions:
            return False, f"File extension '{extension}' is blocked"
        
        # Check allowed extensions (if specified)
        if self.allowed_extensions and extension not in self.allowed_extensions:
            return False, f"File extension '{extension}' is not in allowed list: {self.allowed_extensions}"
        
        # Check allowed MIME types (if specified)
        if self.allowed_mime_types and mime_type not in self.allowed_mime_types:
            return False, f"MIME type '{mime_type}' is not in allowed list"
        
        return True, None
    
    def get_default_policy() -> 'FileUploadPolicy':
        """Get a default file upload policy."""
        return FileUploadPolicy(
            max_size_mb=10,
            allowed_extensions=[
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'txt', 'csv', 'rtf', 'md', 'jpg', 'jpeg', 'png', 'gif',
                'zip', 'tar', 'json', 'xml', 'yaml', 'yml'
            ],
            blocked_extensions=['exe', 'bat', 'cmd', 'scr', 'vbs', 'jar']
        )
