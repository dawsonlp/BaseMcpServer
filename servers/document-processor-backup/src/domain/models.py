"""
Domain models for document processing.

Pure domain objects with no external dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pathlib import Path


class DocumentFormat(Enum):
    """Supported document formats."""
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    TEXT = "text"


class PDFEngine(Enum):
    """Available PDF generation engines."""
    WEASYPRINT = "weasyprint"
    PDFKIT = "pdfkit"
    REPORTLAB = "reportlab"
    PANDOC = "pandoc"


@dataclass(frozen=True)
class Document:
    """Immutable document representation."""
    content: str
    format: DocumentFormat
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        if not self.content:
            raise ValueError("Document content cannot be empty")


@dataclass(frozen=True)
class ConversionRequest:
    """Request for document conversion."""
    source_content: str
    target_format: DocumentFormat
    filename: Optional[str] = None
    template_name: Optional[str] = None
    pdf_engine: Optional[PDFEngine] = None
    
    def __post_init__(self):
        if not self.source_content:
            raise ValueError("Source content cannot be empty")


@dataclass(frozen=True)
class ConversionResult:
    """Result of document conversion."""
    success: bool
    document: Optional[Document] = None
    file_path: Optional[Path] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    engine_used: Optional[str] = None
    
    def __post_init__(self):
        if self.success and not self.document:
            raise ValueError("Successful conversion must include document")
        if not self.success and not self.error_message:
            raise ValueError("Failed conversion must include error message")


@dataclass(frozen=True)
class FileInfo:
    """Information about a file."""
    name: str
    path: Path
    size_bytes: int
    modified_time: float
    extension: str
