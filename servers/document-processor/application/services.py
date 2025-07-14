"""
Application services for document processing.

These services orchestrate domain logic and provide a clean interface
for different delivery mechanisms (CLI, MCP server, web API, etc.).
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from domain import (
    Document, DocumentFormat, ConversionOptions, ConversionResult,
    ConverterRegistry, DocumentProcessingError
)
from converters import (
    MarkdownToPdfConverter, MarkdownToHtmlConverter,
    MarkdownToDocxConverter, MarkdownToTxtConverter
)


@dataclass
class ConversionRequest:
    """Request object for document conversion."""
    
    content: Optional[str] = None
    input_file: Optional[Path] = None
    output_format: DocumentFormat = DocumentFormat.PDF
    output_file: Optional[str] = None
    output_directory: Optional[str] = None
    
    # Document metadata
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    
    # Format-specific options
    pdf_engine: str = "weasyprint"
    include_css: bool = True
    standalone: bool = True
    
    def __post_init__(self):
        """Validate the request."""
        if not self.content and not self.input_file:
            raise ValueError("Either content or input_file must be provided")
        
        if self.input_file and not Path(self.input_file).exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")


@dataclass
class ConversionResponse:
    """Response object for document conversion."""
    
    success: bool
    output_file: Optional[Path] = None
    output_content: Optional[str] = None
    format: Optional[DocumentFormat] = None
    file_size: Optional[int] = None
    conversion_time: Optional[float] = None
    engine_used: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class DocumentProcessingService:
    """
    Main application service for document processing.
    
    This service provides a clean interface for document conversion
    that can be used by different delivery mechanisms.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the service.
        
        Args:
            output_dir: Default output directory for converted files
        """
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize converter registry
        self.registry = ConverterRegistry()
        self._register_converters()
    
    def _register_converters(self):
        """Register all available converters."""
        converters = [
            MarkdownToPdfConverter(output_dir=self.output_dir),
            MarkdownToHtmlConverter(output_dir=self.output_dir),
            MarkdownToDocxConverter(output_dir=self.output_dir),
            MarkdownToTxtConverter(output_dir=self.output_dir),
        ]
        
        for converter in converters:
            self.registry.register(converter)
    
    def convert_document(self, request: ConversionRequest) -> ConversionResponse:
        """
        Convert a document according to the request.
        
        Args:
            request: Conversion request with all parameters
            
        Returns:
            ConversionResponse with results or error information
        """
        try:
            # Create document from request
            document = self._create_document_from_request(request)
            
            # Get appropriate converter
            converter = self.registry.get_converter(
                DocumentFormat.MARKDOWN, 
                request.output_format
            )
            
            if not converter:
                return ConversionResponse(
                    success=False,
                    error_message=f"No converter available for markdown → {request.output_format.value}"
                )
            
            # Create conversion options
            options = self._create_conversion_options(request)
            
            # Perform conversion
            result = converter.convert(document, options)
            
            # Convert domain result to application response
            return self._create_response_from_result(result, request.output_format)
            
        except Exception as e:
            return ConversionResponse(
                success=False,
                error_message=str(e)
            )
    
    def list_available_conversions(self) -> Dict[str, List[str]]:
        """
        List all available conversion formats.
        
        Returns:
            Dictionary mapping source formats to available target formats
        """
        conversions = self.registry.list_converters()
        
        # Group by source format
        result = {}
        for (source, target), converter_name in conversions.items():
            if source not in result:
                result[source] = []
            result[source].append(target)
        
        return result
    
    def get_converter_info(self, source: str, target: str) -> Optional[Dict]:
        """
        Get information about a specific converter.
        
        Args:
            source: Source format name
            target: Target format name
            
        Returns:
            Converter information or None if not found
        """
        try:
            source_format = DocumentFormat(source)
            target_format = DocumentFormat(target)
            
            converter = self.registry.get_converter(source_format, target_format)
            if converter:
                return {
                    "name": converter.name,
                    "source_format": converter.source_format.value,
                    "target_format": converter.target_format.value,
                }
        except ValueError:
            pass
        
        return None
    
    def _create_document_from_request(self, request: ConversionRequest) -> Document:
        """Create a Document object from the request."""
        if request.content:
            content = request.content
        else:
            content = Path(request.input_file).read_text(encoding='utf-8')
        
        return Document.from_markdown(
            content=content,
            title=request.title,
            author=request.author,
            subject=request.subject
        )
    
    def _create_conversion_options(self, request: ConversionRequest) -> ConversionOptions:
        """Create ConversionOptions from the request."""
        from domain.formats import PDFEngine
        
        # Map string to PDFEngine enum
        pdf_engine = PDFEngine.WEASYPRINT
        if request.pdf_engine.lower() == "reportlab":
            pdf_engine = PDFEngine.REPORTLAB
        elif request.pdf_engine.lower() == "pandoc":
            pdf_engine = PDFEngine.PANDOC
        
        return ConversionOptions(
            filename=request.output_file,
            output_directory=request.output_directory or str(self.output_dir),
            title=request.title,
            author=request.author,
            subject=request.subject,
            pdf_engine=pdf_engine,
            include_css=request.include_css,
            standalone=request.standalone,
            save_to_file=True
        )
    
    def _create_response_from_result(self, result: ConversionResult, format: DocumentFormat) -> ConversionResponse:
        """Convert domain ConversionResult to application ConversionResponse."""
        return ConversionResponse(
            success=result.success,
            output_file=result.output_file_path,
            output_content=result.output_content,
            format=format,
            file_size=result.file_size_bytes,
            conversion_time=result.conversion_time_seconds,
            engine_used=result.engine_used,
            error_message=result.error_message,
            metadata=result.metadata
        )
