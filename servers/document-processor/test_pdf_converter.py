#!/usr/bin/env python3
"""
Test script for the markdown to PDF converter.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from domain import Document, DocumentFormat, ConversionOptions, PDFEngine, ConverterRegistry
from converters import MarkdownToPdfConverter


def test_markdown_to_pdf():
    """Test markdown to PDF conversion."""
    print("🚀 Testing Markdown to PDF Converter")
    print("=" * 50)
    
    # Create a sample markdown document
    markdown_content = """# Document Processing Test

This is a **test document** to verify our markdown to PDF conversion works correctly.

## Features Tested

- **Bold text** and *italic text*
- Lists and bullet points
- Code blocks and `inline code`
- Tables and formatting

### Sample Code Block

```python
def hello_world():
    print("Hello, World!")
    return "success"
```

### Sample Table

| Feature | Status | Notes |
|---------|--------|-------|
| Markdown parsing | ✅ | Working |
| PDF generation | 🧪 | Testing |
| Template support | ✅ | Available |

## Conclusion

This document tests various markdown features to ensure they convert properly to PDF format.

> This is a blockquote to test formatting.

**End of test document.**
"""
    
    # Create document
    doc = Document.from_markdown(
        content=markdown_content,
        title="PDF Conversion Test",
        author="Document Processor Test Suite"
    )
    
    print(f"📄 Created document: {doc.word_count} words, {doc.character_count} characters")
    print(f"📝 Title: {doc.metadata.title}")
    print(f"👤 Author: {doc.metadata.author}")
    
    # Test different PDF engines
    engines_to_test = [
        PDFEngine.WEASYPRINT,
        PDFEngine.REPORTLAB,
    ]
    
    # Create converter
    converter = MarkdownToPdfConverter()
    
    # Register converter
    registry = ConverterRegistry()
    registry.register(converter)
    
    print(f"\n🔧 Converter: {converter.name}")
    print(f"📥 Source format: {converter.source_format.value}")
    print(f"📤 Target format: {converter.target_format.value}")
    
    # Test conversions
    results = []
    
    for engine in engines_to_test:
        print(f"\n🔄 Testing {engine.value} engine...")
        
        # Configure conversion options
        options = ConversionOptions(
            filename=f"test_document_{engine.value}",
            template_name="simple.html",
            pdf_engine=engine,
            title="PDF Conversion Test",
            author="Test Suite",
            page_size="A4"
        )
        
        try:
            # Convert document
            result = converter.convert(doc, options)
            results.append((engine, result))
            
            if result.success:
                print(f"  ✅ Success! Generated: {result.output_file_path}")
                print(f"  ⏱️  Conversion time: {result.conversion_time_seconds:.2f} seconds")
                print(f"  📊 File size: {result.file_size_bytes} bytes")
                print(f"  🔧 Engine used: {result.engine_used}")
            else:
                print(f"  ❌ Failed: {result.error_message}")
                if result.error_details:
                    print(f"  📝 Details: {result.error_details}")
                    
        except Exception as e:
            print(f"  💥 Exception: {e}")
            results.append((engine, None))
    
    # Test without template
    print(f"\n🔄 Testing without template...")
    options_no_template = ConversionOptions(
        filename="test_document_no_template",
        pdf_engine=PDFEngine.WEASYPRINT,
        title="No Template Test"
    )
    
    try:
        result = converter.convert(doc, options_no_template)
        if result.success:
            print(f"  ✅ Success! Generated: {result.output_file_path}")
        else:
            print(f"  ❌ Failed: {result.error_message}")
    except Exception as e:
        print(f"  💥 Exception: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Conversion Results Summary:")
    
    successful_conversions = 0
    for engine, result in results:
        if result and result.success:
            successful_conversions += 1
            print(f"  ✅ {engine.value}: SUCCESS")
        else:
            print(f"  ❌ {engine.value}: FAILED")
    
    print(f"\n🎯 Success rate: {successful_conversions}/{len(results)} engines")
    
    if successful_conversions > 0:
        print("\n✅ Markdown to PDF conversion is working!")
        print("📁 Check the 'output' directory for generated PDF files.")
    else:
        print("\n❌ All conversions failed. Check error messages above.")
    
    return successful_conversions > 0


def main():
    """Run the test."""
    try:
        success = test_markdown_to_pdf()
        if success:
            print("\n🎉 Test completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
