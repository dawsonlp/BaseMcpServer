"""
Use cases for document processing.

Use cases represent specific business operations that can be performed
by the application. They coordinate between the domain and application services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path

from domain import DocumentFormat
from .services import DocumentProcessingService, ConversionRequest, ConversionResponse


class UseCase(ABC):
    """Base class for all use cases."""
    
    def __init__(self, service: DocumentProcessingService):
        self.service = service


class ConvertDocumentUseCase(UseCase):
    """
    Use case for converting a document from one format to another.
    
    This encapsulates the business logic for document conversion,
    including validation, error handling, and response formatting.
    """
    
    def execute(
        self,
        content: Optional[str] = None,
        input_file: Optional[str] = None,
        output_format: str = "pdf",
        output_file: Optional[str] = None,
        output_directory: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        subject: Optional[str] = None,
        pdf_engine: str = "weasyprint",
        include_css: bool = True,
        standalone: bool = True
    ) -> ConversionResponse:
        """
        Execute the document conversion use case.
        
        Args:
            content: Markdown content to convert
            input_file: Path to input markdown file
            output_format: Target format (pdf, html, docx, txt)
            output_file: Output filename (without extension)
            output_directory: Output directory path
            title: Document title
            author: Document author
            subject: Document subject
            pdf_engine: PDF engine to use (weasyprint, reportlab, pandoc)
            include_css: Include CSS styling (for HTML)
            standalone: Create standalone document (for HTML)
            
        Returns:
            ConversionResponse with results or error information
        """
        try:
            # Validate and convert output format
            try:
                target_format = DocumentFormat(output_format.lower())
            except ValueError:
                return ConversionResponse(
                    success=False,
                    error_message=f"Unsupported output format: {output_format}. "
                                f"Supported formats: {[f.value for f in DocumentFormat]}"
                )
            
            # Create conversion request
            request = ConversionRequest(
                content=content,
                input_file=Path(input_file) if input_file else None,
                output_format=target_format,
                output_file=output_file,
                output_directory=output_directory,
                title=title,
                author=author,
                subject=subject,
                pdf_engine=pdf_engine,
                include_css=include_css,
                standalone=standalone
            )
            
            # Execute conversion
            return self.service.convert_document(request)
            
        except Exception as e:
            return ConversionResponse(
                success=False,
                error_message=f"Conversion failed: {str(e)}"
            )


class ListConvertersUseCase(UseCase):
    """
    Use case for listing available converters and formats.
    
    This provides information about what conversions are supported
    by the system.
    """
    
    def execute(self) -> Dict[str, List[str]]:
        """
        Execute the list converters use case.
        
        Returns:
            Dictionary mapping source formats to available target formats
        """
        return self.service.list_available_conversions()


class GetConverterInfoUseCase(UseCase):
    """
    Use case for getting detailed information about a specific converter.
    """
    
    def execute(self, source: str, target: str) -> Optional[Dict]:
        """
        Execute the get converter info use case.
        
        Args:
            source: Source format name
            target: Target format name
            
        Returns:
            Converter information or None if not found
        """
        return self.service.get_converter_info(source, target)


class ValidateInputUseCase(UseCase):
    """
    Use case for validating input before conversion.
    
    This can be used to check if a file exists, content is valid, etc.
    """
    
    def execute(
        self,
        content: Optional[str] = None,
        input_file: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Execute input validation.
        
        Args:
            content: Markdown content to validate
            input_file: Path to input file to validate
            
        Returns:
            Validation results
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        try:
            if not content and not input_file:
                result["valid"] = False
                result["errors"].append("Either content or input_file must be provided")
                return result
            
            if input_file:
                file_path = Path(input_file)
                if not file_path.exists():
                    result["valid"] = False
                    result["errors"].append(f"Input file not found: {input_file}")
                    return result
                
                # Get file info
                stat = file_path.stat()
                result["info"]["file_size"] = stat.st_size
                result["info"]["file_extension"] = file_path.suffix
                
                # Read content for analysis
                try:
                    content = file_path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    result["valid"] = False
                    result["errors"].append("File is not valid UTF-8 text")
                    return result
            
            if content:
                # Basic content validation
                if not content.strip():
                    result["warnings"].append("Content appears to be empty")
                
                # Content statistics
                result["info"]["word_count"] = len(content.split())
                result["info"]["character_count"] = len(content)
                result["info"]["line_count"] = len(content.split('\n'))
                
                # Check for markdown features
                features = []
                if '#' in content:
                    features.append("headers")
                if '**' in content or '*' in content:
                    features.append("emphasis")
                if '```' in content:
                    features.append("code_blocks")
                if '|' in content:
                    features.append("tables")
                if '[' in content and ']' in content:
                    features.append("links")
                
                result["info"]["markdown_features"] = features
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Validation error: {str(e)}")
        
        return result
