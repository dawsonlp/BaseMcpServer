"""
Document format definitions and conversion options.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class DocumentFormat(Enum):
    """Supported document formats for conversion."""
    
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    
    @property
    def file_extension(self) -> str:
        """Get the file extension for this format."""
        extensions = {
            DocumentFormat.MARKDOWN: ".md",
            DocumentFormat.HTML: ".html",
            DocumentFormat.PDF: ".pdf",
            DocumentFormat.DOCX: ".docx",
            DocumentFormat.TXT: ".txt",
        }
        return extensions[self]
    
    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format."""
        mime_types = {
            DocumentFormat.MARKDOWN: "text/markdown",
            DocumentFormat.HTML: "text/html",
            DocumentFormat.PDF: "application/pdf",
            DocumentFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            DocumentFormat.TXT: "text/plain",
        }
        return mime_types[self]


class PDFEngine(Enum):
    """Available PDF generation engines."""
    
    WEASYPRINT = "weasyprint"
    REPORTLAB = "reportlab"
    PANDOC = "pandoc"
    
    @property
    def description(self) -> str:
        """Get a description of the PDF engine."""
        descriptions = {
            PDFEngine.WEASYPRINT: "WeasyPrint - Best CSS support, modern HTML to PDF",
            PDFEngine.REPORTLAB: "ReportLab - Lightweight, programmatic PDF generation",
            PDFEngine.PANDOC: "Pandoc - Universal document converter",
        }
        return descriptions[self]


@dataclass
class ConversionOptions:
    """Options for document conversion."""
    
    # General options
    filename: Optional[str] = None
    template_name: Optional[str] = None
    
    # PDF-specific options
    pdf_engine: PDFEngine = PDFEngine.WEASYPRINT
    page_size: str = "A4"
    margin: str = "1in"
    
    # HTML-specific options
    include_css: bool = True
    standalone: bool = True
    
    # Output options
    save_to_file: bool = True
    output_directory: Optional[str] = None
    
    # Metadata
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    
    # Custom options for extensibility
    custom_options: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize custom options if not provided."""
        if self.custom_options is None:
            self.custom_options = {}
