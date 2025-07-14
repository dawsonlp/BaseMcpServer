"""
Document entity and related value objects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from .formats import DocumentFormat


@dataclass
class DocumentMetadata:
    """Metadata associated with a document."""
    
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    source_file: Optional[Path] = None
    file_size_bytes: Optional[int] = None
    
    # Custom metadata for extensibility
    custom_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize custom metadata if not provided."""
        if self.custom_metadata is None:
            self.custom_metadata = {}
        
        # Set created_at if not provided
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Document:
    """
    Core document entity representing content and its metadata.
    
    This is the central domain object that represents a document
    in any format with its associated content and metadata.
    """
    
    content: str
    source_format: DocumentFormat
    metadata: DocumentMetadata
    
    def __post_init__(self):
        """Validate document after initialization."""
        if not self.content:
            raise ValueError("Document content cannot be empty")
        
        if not isinstance(self.source_format, DocumentFormat):
            raise ValueError("source_format must be a DocumentFormat enum")
        
        if not isinstance(self.metadata, DocumentMetadata):
            raise ValueError("metadata must be a DocumentMetadata instance")
    
    @classmethod
    def from_markdown(
        cls, 
        content: str, 
        title: Optional[str] = None,
        author: Optional[str] = None,
        **metadata_kwargs
    ) -> 'Document':
        """Create a document from markdown content."""
        metadata = DocumentMetadata(
            title=title,
            author=author,
            **metadata_kwargs
        )
        return cls(
            content=content,
            source_format=DocumentFormat.MARKDOWN,
            metadata=metadata
        )
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'Document':
        """Create a document from a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine format from file extension
        extension = file_path.suffix.lower()
        format_mapping = {
            '.md': DocumentFormat.MARKDOWN,
            '.markdown': DocumentFormat.MARKDOWN,
            '.html': DocumentFormat.HTML,
            '.htm': DocumentFormat.HTML,
            '.txt': DocumentFormat.TXT,
        }
        
        source_format = format_mapping.get(extension)
        if source_format is None:
            raise ValueError(f"Unsupported file format: {extension}")
        
        # Read content
        content = file_path.read_text(encoding='utf-8')
        
        # Create metadata
        stat = file_path.stat()
        metadata = DocumentMetadata(
            title=file_path.stem,
            source_file=file_path,
            file_size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )
        
        return cls(
            content=content,
            source_format=source_format,
            metadata=metadata
        )
    
    @property
    def word_count(self) -> int:
        """Get approximate word count of the document."""
        return len(self.content.split())
    
    @property
    def character_count(self) -> int:
        """Get character count of the document."""
        return len(self.content)
    
    def preview(self, max_chars: int = 200) -> str:
        """Get a preview of the document content."""
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars] + "..."
