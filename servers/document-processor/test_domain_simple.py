#!/usr/bin/env python3
"""
Simple test script to verify the domain model works correctly.
This can be run without pytest to quickly validate the domain logic.
"""

import sys
from pathlib import Path

# Add the current directory to Python path so we can import domain
sys.path.insert(0, str(Path(__file__).parent))

from domain import (
    Document, DocumentMetadata, DocumentFormat, ConversionOptions, 
    PDFEngine, ConversionResult, ConverterRegistry
)


def test_document_creation():
    """Test basic document creation."""
    print("Testing document creation...")
    
    # Test creating a document from markdown
    doc = Document.from_markdown(
        content="# Hello World\n\nThis is a **test** document with *emphasis*.",
        title="Test Document",
        author="Test Author"
    )
    
    assert doc.content.startswith("# Hello World")
    assert doc.source_format == DocumentFormat.MARKDOWN
    assert doc.metadata.title == "Test Document"
    assert doc.metadata.author == "Test Author"
    print(f"  Word count: {doc.word_count}")
    assert doc.word_count > 0  # Just check it's positive
    assert doc.character_count > 0
    
    print("✅ Document creation works!")
    return doc


def test_document_formats():
    """Test document format properties."""
    print("Testing document formats...")
    
    # Test file extensions
    assert DocumentFormat.MARKDOWN.file_extension == ".md"
    assert DocumentFormat.HTML.file_extension == ".html"
    assert DocumentFormat.PDF.file_extension == ".pdf"
    assert DocumentFormat.DOCX.file_extension == ".docx"
    assert DocumentFormat.TXT.file_extension == ".txt"
    
    # Test MIME types
    assert DocumentFormat.HTML.mime_type == "text/html"
    assert DocumentFormat.PDF.mime_type == "application/pdf"
    
    print("✅ Document formats work!")


def test_conversion_options():
    """Test conversion options."""
    print("Testing conversion options...")
    
    options = ConversionOptions(
        filename="test_document",
        template_name="professional.html",
        pdf_engine=PDFEngine.WEASYPRINT,
        title="My Document",
        author="Test Author"
    )
    
    assert options.filename == "test_document"
    assert options.template_name == "professional.html"
    assert options.pdf_engine == PDFEngine.WEASYPRINT
    assert options.title == "My Document"
    assert options.custom_options == {}
    
    print("✅ Conversion options work!")


def test_conversion_results():
    """Test conversion result objects."""
    print("Testing conversion results...")
    
    # Test successful result
    success_result = ConversionResult.success_result(
        output_content="<html><body><h1>Hello World</h1></body></html>",
        target_format=DocumentFormat.HTML,
        engine_used="markdown",
        conversion_time_seconds=0.1
    )
    
    assert success_result.success is True
    assert success_result.target_format == DocumentFormat.HTML
    assert success_result.engine_used == "markdown"
    assert success_result.error_message is None
    
    # Test error result
    error_result = ConversionResult.error_result(
        error_message="Conversion failed",
        error_details="Invalid markdown syntax",
        target_format=DocumentFormat.PDF
    )
    
    assert error_result.success is False
    assert error_result.error_message == "Conversion failed"
    assert error_result.output_content is None
    
    print("✅ Conversion results work!")


def test_converter_registry():
    """Test converter registry."""
    print("Testing converter registry...")
    
    registry = ConverterRegistry()
    
    # Initially empty
    assert registry.get_converter(DocumentFormat.MARKDOWN, DocumentFormat.HTML) is None
    
    # Test listing (should be empty)
    converters = registry.list_converters()
    assert len(converters) == 0
    
    print("✅ Converter registry works!")


def test_pdf_engines():
    """Test PDF engine enum."""
    print("Testing PDF engines...")
    
    assert PDFEngine.WEASYPRINT.value == "weasyprint"
    assert PDFEngine.REPORTLAB.value == "reportlab"
    assert PDFEngine.PANDOC.value == "pandoc"
    
    # Test descriptions
    assert "WeasyPrint" in PDFEngine.WEASYPRINT.description
    assert "ReportLab" in PDFEngine.REPORTLAB.description
    assert "Pandoc" in PDFEngine.PANDOC.description
    
    print("✅ PDF engines work!")


def main():
    """Run all tests."""
    print("🚀 Testing Document Processor Domain Model")
    print("=" * 50)
    
    try:
        # Run all tests
        doc = test_document_creation()
        test_document_formats()
        test_conversion_options()
        test_conversion_results()
        test_converter_registry()
        test_pdf_engines()
        
        print("\n" + "=" * 50)
        print("🎉 All domain model tests passed!")
        print("\nDomain model summary:")
        print(f"  📄 Document: {doc.word_count} words, {doc.character_count} characters")
        print(f"  📝 Source format: {doc.source_format.value}")
        print(f"  👤 Author: {doc.metadata.author}")
        print(f"  📅 Created: {doc.metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  🔍 Preview: {doc.preview(50)}")
        
        print("\n✅ Domain model is ready for concrete converter implementations!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
