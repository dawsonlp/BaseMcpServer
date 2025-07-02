"""
Domain ports (interfaces) for document processing.

These define the contracts that external adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from .models import ConversionRequest, ConversionResult, FileInfo, DocumentFormat, PDFEngine


class DocumentConverter(ABC):
    """Port for document conversion operations."""
    
    @abstractmethod
    async def convert(self, request: ConversionRequest) -> ConversionResult:
        """Convert a document from one format to another."""
        pass
    
    @abstractmethod
    def supports_format(self, format: DocumentFormat) -> bool:
        """Check if the converter supports a specific format."""
        pass


class FileStorage(ABC):
    """Port for file storage operations."""
    
    @abstractmethod
    async def save_file(self, content: str, file_path: Path) -> bool:
        """Save content to a file."""
        pass
    
    @abstractmethod
    async def list_files(self, directory: Path) -> List[FileInfo]:
        """List files in a directory."""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists."""
        pass
    
    @abstractmethod
    async def get_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Get information about a file."""
        pass


class TemplateRenderer(ABC):
    """Port for template rendering operations."""
    
    @abstractmethod
    async def render(self, template_name: str, content: str) -> str:
        """Render content using a template."""
        pass
    
    @abstractmethod
    async def list_templates(self) -> List[str]:
        """List available templates."""
        pass
    
    @abstractmethod
    async def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        pass


class ConfigurationProvider(ABC):
    """Port for configuration access."""
    
    @abstractmethod
    def get_output_directory(self) -> Path:
        """Get the output directory path."""
        pass
    
    @abstractmethod
    def get_input_directory(self) -> Path:
        """Get the input directory path."""
        pass
    
    @abstractmethod
    def get_template_directory(self) -> Path:
        """Get the template directory path."""
        pass
    
    @abstractmethod
    def get_default_pdf_engine(self) -> PDFEngine:
        """Get the default PDF engine."""
        pass
    
    @abstractmethod
    def get_max_file_size_mb(self) -> int:
        """Get the maximum file size in MB."""
        pass
