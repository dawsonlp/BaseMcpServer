"""
Tests for the domain model.
"""

import pytest
from datetime import datetime
from pathlib import Path

from domain import (
    Document, DocumentMetadata, DocumentFormat, ConversionOptions, 
    PDFEngine, ConversionResult, DocumentConverter, ConverterRegistry
)
from domain.exceptions import DocumentProcessingError, ConversionError


class TestDocumentMetadata:
    """Test DocumentMetadata class."""
    
    def test_default_creation(self):
        """Test creating metadata with defaults."""
        metadata = DocumentMetadata()
        
        assert metadata.title is None
        assert metadata.author is None
        assert isinstance(metadata.created_at, datetime)
        assert metadata.custom_metadata == {}
    
    def test_with_values(self):
        """Test creating metadata with specific values."""
        metadata = DocumentMetadata(
            title="Test Document",
            author="Test Author",
            subject="Testing"
        )
        
        assert metadata.title == "Test Document"
        assert metadata.author == "Test Author"
        assert metadata.subject == "Testing"


class TestDocument:
    """Test Document class."""
    
    def test_from_markdown(self):
        """Test creating document from markdown."""
        content = "# Hello World\n\nThis is a test."
        doc = Document.from_markdown(
            content=content,
            title="Test Doc",
            author="Test Author"
        )
        
        assert doc.content == content
        assert doc.source_format == DocumentFormat.MARKDOWN
        assert doc.metadata.title == "Test Doc"
        assert doc.metadata.author == "Test Author"
    
    def test_word_count(self):
        """Test word count calculation."""
        doc = Document.from_markdown("Hello world this is a test")
        assert doc.word_count == 6
    
    def test_character_count(self):
        """Test character count."""
        content = "Hello"
        doc = Document.from_markdown(content)
        assert doc.character_count == 5
    
    def test_preview(self):
        """Test document preview."""
        long_content = "A" * 300
        doc = Document.from_markdown(long_content)
        preview = doc.preview(max_chars=50)
        
        assert len(preview) == 53  # 50 + "..."
        assert preview.endswith("...")
    
    def test_empty_content_raises_error(self):
        """Test that empty content raises an error."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(
                content="",
                source_format=DocumentFormat.MARKDOWN,
                metadata=DocumentMetadata()
            )


class TestDocumentFormat:
    """Test DocumentFormat enum."""
    
    def test_file_extensions(self):
        """Test file extension properties."""
        assert DocumentFormat.MARKDOWN.file_extension == ".md"
        assert DocumentFormat.HTML.file_extension == ".html"
        assert DocumentFormat.PDF.file_extension == ".pdf"
        assert DocumentFormat.DOCX.file_extension == ".docx"
        assert DocumentFormat.TXT.file_extension == ".txt"
    
    def test_mime_types(self):
        """Test MIME type properties."""
        assert DocumentFormat.MARKDOWN.mime_type == "text/markdown"
        assert DocumentFormat.HTML.mime_type == "text/html"
        assert DocumentFormat.PDF.mime_type == "application/pdf"


class TestConversionOptions:
    """Test ConversionOptions class."""
    
    def test_defaults(self):
        """Test default values."""
        options = ConversionOptions()
        
        assert options.filename is None
        assert options.pdf_engine == PDFEngine.WEASYPRINT
        assert options.page_size == "A4"
        assert options.save_to_file is True
        assert options.custom_options == {}
    
    def test_custom_options(self):
        """Test custom options."""
        options = ConversionOptions(
            filename="test.pdf",
            pdf_engine=PDFEngine.REPORTLAB,
            custom_options={"test": "value"}
        )
        
        assert options.filename == "test.pdf"
        assert options.pdf_engine == PDFEngine.REPORTLAB
        assert options.custom_options["test"] == "value"


class TestConversionResult:
    """Test ConversionResult class."""
    
    def test_success_result(self):
        """Test creating a successful result."""
        result = ConversionResult.success_result(
            output_content="<html>test</html>",
            target_format=DocumentFormat.HTML,
            engine_used="markdown"
        )
        
        assert result.success is True
        assert result.output_content == "<html>test</html>"
        assert result.target_format == DocumentFormat.HTML
        assert result.engine_used == "markdown"
        assert result.error_message is None
    
    def test_error_result(self):
        """Test creating an error result."""
        result = ConversionResult.error_result(
            error_message="Conversion failed",
            error_details="Invalid markdown syntax",
            target_format=DocumentFormat.PDF
        )
        
        assert result.success is False
        assert result.error_message == "Conversion failed"
        assert result.error_details == "Invalid markdown syntax"
        assert result.target_format == DocumentFormat.PDF
        assert result.output_content is None


class MockConverter(DocumentConverter):
    """Mock converter for testing."""
    
    @property
    def source_format(self) -> DocumentFormat:
        return DocumentFormat.MARKDOWN
    
    @property
    def target_format(self) -> DocumentFormat:
        return DocumentFormat.HTML
    
    @property
    def name(self) -> str:
        return "Mock Markdown to HTML Converter"
    
    def convert(self, document: Document, options: ConversionOptions) -> ConversionResult:
        return ConversionResult.success_result(
            output_content=f"<html><body>{document.content}</body></html>",
            target_format=self.target_format,
            engine_used="mock"
        )


class TestConverterRegistry:
    """Test ConverterRegistry class."""
    
    def test_register_and_get_converter(self):
        """Test registering and retrieving converters."""
        registry = ConverterRegistry()
        converter = MockConverter()
        
        registry.register(converter)
        
        retrieved = registry.get_converter(
            DocumentFormat.MARKDOWN, 
            DocumentFormat.HTML
        )
        
        assert retrieved is converter
    
    def test_get_nonexistent_converter(self):
        """Test getting a converter that doesn't exist."""
        registry = ConverterRegistry()
        
        result = registry.get_converter(
            DocumentFormat.MARKDOWN,
            DocumentFormat.PDF
        )
        
        assert result is None
    
    def test_list_converters(self):
        """Test listing all converters."""
        registry = ConverterRegistry()
        converter = MockConverter()
        registry.register(converter)
        
        converters = registry.list_converters()
        
        assert ("markdown", "html") in converters
        assert converters[("markdown", "html")] == "Mock Markdown to HTML Converter"
    
    def test_get_supported_conversions(self):
        """Test getting supported conversions for a format."""
        registry = ConverterRegistry()
        converter = MockConverter()
        registry.register(converter)
        
        supported = registry.get_supported_conversions(DocumentFormat.MARKDOWN)
        
        assert DocumentFormat.HTML in supported


class TestDocumentConverter:
    """Test DocumentConverter abstract class."""
    
    def test_can_convert(self):
        """Test can_convert method."""
        converter = MockConverter()
        
        assert converter.can_convert(DocumentFormat.MARKDOWN, DocumentFormat.HTML) is True
        assert converter.can_convert(DocumentFormat.MARKDOWN, DocumentFormat.PDF) is False
        assert converter.can_convert(DocumentFormat.HTML, DocumentFormat.HTML) is False
    
    def test_validate_document_success(self):
        """Test successful document validation."""
        converter = MockConverter()
        doc = Document.from_markdown("# Test")
        
        # Should not raise an exception
        converter.validate_document(doc)
    
    def test_validate_document_wrong_format(self):
        """Test document validation with wrong format."""
        converter = MockConverter()
        doc = Document(
            content="<html>test</html>",
            source_format=DocumentFormat.HTML,
            metadata=DocumentMetadata()
        )
        
        with pytest.raises(ValueError, match="Document format html is not supported"):
            converter.validate_document(doc)
    
    def test_validate_empty_document(self):
        """Test validation of empty document."""
        converter = MockConverter()
        doc = Document(
            content="   ",  # Only whitespace
            source_format=DocumentFormat.MARKDOWN,
            metadata=DocumentMetadata()
        )
        
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            converter.validate_document(doc)


if __name__ == "__main__":
    pytest.main([__file__])
