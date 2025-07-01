"""
Document converter interfaces and result objects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .document import Document
from .formats import DocumentFormat, ConversionOptions


@dataclass
class ConversionResult:
    """Result of a document conversion operation."""
    
    success: bool
    output_content: Optional[str] = None
    output_file_path: Optional[Path] = None
    target_format: Optional[DocumentFormat] = None
    file_size_bytes: Optional[int] = None
    conversion_time_seconds: Optional[float] = None
    engine_used: Optional[str] = None
    
    # Error information
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    
    # Metadata
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        if self.metadata is None:
            self.metadata = {}
        
        # Calculate file size if output file exists
        if self.output_file_path and self.output_file_path.exists() and self.file_size_bytes is None:
            self.file_size_bytes = self.output_file_path.stat().st_size
    
    @classmethod
    def success_result(
        cls,
        output_content: str = None,
        output_file_path: Path = None,
        target_format: DocumentFormat = None,
        engine_used: str = None,
        conversion_time_seconds: float = None,
        **kwargs
    ) -> 'ConversionResult':
        """Create a successful conversion result."""
        return cls(
            success=True,
            output_content=output_content,
            output_file_path=output_file_path,
            target_format=target_format,
            engine_used=engine_used,
            conversion_time_seconds=conversion_time_seconds,
            **kwargs
        )
    
    @classmethod
    def error_result(
        cls,
        error_message: str,
        error_details: str = None,
        target_format: DocumentFormat = None,
        **kwargs
    ) -> 'ConversionResult':
        """Create a failed conversion result."""
        return cls(
            success=False,
            error_message=error_message,
            error_details=error_details,
            target_format=target_format,
            **kwargs
        )


class DocumentConverter(ABC):
    """
    Abstract base class for document converters.
    
    This defines the interface that all concrete converters must implement.
    Each converter is responsible for converting from one format to another.
    """
    
    @property
    @abstractmethod
    def source_format(self) -> DocumentFormat:
        """The source format this converter accepts."""
        pass
    
    @property
    @abstractmethod
    def target_format(self) -> DocumentFormat:
        """The target format this converter produces."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this converter."""
        pass
    
    @abstractmethod
    def convert(self, document: Document, options: ConversionOptions) -> ConversionResult:
        """
        Convert a document to the target format.
        
        Args:
            document: The source document to convert
            options: Conversion options and settings
            
        Returns:
            ConversionResult with the conversion outcome
        """
        pass
    
    def can_convert(self, source_format: DocumentFormat, target_format: DocumentFormat) -> bool:
        """Check if this converter can handle the given format conversion."""
        return (
            source_format == self.source_format and 
            target_format == self.target_format
        )
    
    def validate_document(self, document: Document) -> None:
        """
        Validate that the document is suitable for conversion.
        
        Raises:
            ValueError: If the document is not valid for this converter
        """
        if document.source_format != self.source_format:
            raise ValueError(
                f"Document format {document.source_format.value} is not supported by "
                f"{self.name}. Expected {self.source_format.value}."
            )
        
        if not document.content.strip():
            raise ValueError("Document content cannot be empty")


class ConverterRegistry:
    """Registry for managing document converters."""
    
    def __init__(self):
        self._converters: Dict[tuple, DocumentConverter] = {}
    
    def register(self, converter: DocumentConverter) -> None:
        """Register a converter."""
        key = (converter.source_format, converter.target_format)
        self._converters[key] = converter
    
    def get_converter(
        self, 
        source_format: DocumentFormat, 
        target_format: DocumentFormat
    ) -> Optional[DocumentConverter]:
        """Get a converter for the specified format conversion."""
        key = (source_format, target_format)
        return self._converters.get(key)
    
    def list_converters(self) -> Dict[tuple, str]:
        """List all registered converters."""
        return {
            (src.value, tgt.value): converter.name
            for (src, tgt), converter in self._converters.items()
        }
    
    def get_supported_conversions(self, source_format: DocumentFormat) -> list[DocumentFormat]:
        """Get all target formats supported for a given source format."""
        return [
            target for (source, target) in self._converters.keys()
            if source == source_format
        ]
