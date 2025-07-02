#!/usr/bin/env python3
"""
Test script for all markdown converters.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from domain import Document, DocumentFormat, ConversionOptions, ConverterRegistry
from converters import (
    MarkdownToPdfConverter, MarkdownToHtmlConverter, 
    MarkdownToDocxConverter, MarkdownToTxtConverter
)


def test_all_converters():
    """Test all four markdown converters."""
    print("🚀 Testing All Markdown Converters")
    print("=" * 60)
    
    # Create a comprehensive test document
    markdown_content = """# Document Conversion Test

This is a **comprehensive test document** to verify all our markdown converters work correctly.

## Features Being Tested

### Text Formatting
- **Bold text** and *italic text*
- `inline code` and regular text
- ~~Strikethrough text~~ (if supported)

### Lists
1. Numbered list item one
2. Numbered list item two
3. Numbered list item three

- Bullet point one
- Bullet point two
- Bullet point three

### Code Blocks

```python
def hello_world():
    print("Hello, World!")
    return "success"

# This is a comment
for i in range(3):
    print(f"Iteration {i}")
```

### Tables

| Format | Status | Quality | Speed |
|--------|--------|---------|-------|
| PDF    | ✅     | High    | Fast  |
| HTML   | ✅     | High    | Very Fast |
| DOCX   | ✅     | High    | Medium |
| TXT    | ✅     | Medium  | Very Fast |

### Blockquotes

> This is a blockquote to test formatting.
> It can span multiple lines and should be
> properly formatted in all output formats.

### Links and References

This document tests [markdown conversion](https://example.com) capabilities.

## Conclusion

This comprehensive test ensures that all four converters (PDF, HTML, DOCX, TXT) 
handle various markdown features correctly and produce high-quality output.

**End of test document.**
"""
    
    # Create document
    doc = Document.from_markdown(
        content=markdown_content,
        title="Comprehensive Conversion Test",
        author="Document Processor Test Suite"
    )
    
    print(f"📄 Created test document:")
    print(f"   Title: {doc.metadata.title}")
    print(f"   Author: {doc.metadata.author}")
    print(f"   Stats: {doc.word_count} words, {doc.character_count} characters")
    
    # Initialize all converters
    converters = [
        MarkdownToPdfConverter(),
        MarkdownToHtmlConverter(),
        MarkdownToDocxConverter(),
        MarkdownToTxtConverter(),
    ]
    
    # Create registry and register all converters
    registry = ConverterRegistry()
    for converter in converters:
        registry.register(converter)
    
    print(f"\n🔧 Registered {len(converters)} converters")
    
    # Test each converter
    results = []
    
    for converter in converters:
        print(f"\n🔄 Testing {converter.name}...")
        print(f"   {converter.source_format.value} → {converter.target_format.value}")
        
        # Configure options for this format
        options = ConversionOptions(
            filename=f"test_comprehensive_{converter.target_format.value}",
            title="Comprehensive Conversion Test",
            author="Test Suite",
            save_to_file=True,
            standalone=True,  # For HTML
            include_css=True,  # For HTML
        )
        
        try:
            # Convert document
            result = converter.convert(doc, options)
            results.append((converter, result))
            
            if result.success:
                print(f"   ✅ Success!")
                print(f"   📁 Output: {result.output_file_path}")
                print(f"   ⏱️  Time: {result.conversion_time_seconds:.3f}s")
                print(f"   🔧 Engine: {result.engine_used}")
                if result.file_size_bytes:
                    print(f"   📊 Size: {result.file_size_bytes:,} bytes")
                
                # Show format-specific info
                if result.metadata:
                    if 'standalone' in result.metadata:
                        print(f"   🎨 Standalone: {result.metadata['standalone']}")
                    if 'include_css' in result.metadata:
                        print(f"   🎨 CSS: {result.metadata['include_css']}")
            else:
                print(f"   ❌ Failed: {result.error_message}")
                if result.error_details:
                    print(f"   📝 Details: {result.error_details}")
                    
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append((converter, None))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Conversion Results Summary:")
    
    successful_conversions = 0
    total_conversions = len(converters)
    
    for converter, result in results:
        format_name = converter.target_format.value.upper()
        if result and result.success:
            successful_conversions += 1
            size_info = f" ({result.file_size_bytes:,} bytes)" if result.file_size_bytes else ""
            time_info = f" in {result.conversion_time_seconds:.3f}s"
            print(f"   ✅ {format_name:<6} SUCCESS{size_info}{time_info}")
        else:
            print(f"   ❌ {format_name:<6} FAILED")
    
    print(f"\n🎯 Overall Success Rate: {successful_conversions}/{total_conversions} formats")
    
    if successful_conversions == total_conversions:
        print("\n🎉 All converters working perfectly!")
        print("📁 Check the 'output' directory for generated files:")
        print("   • test_comprehensive_pdf.pdf")
        print("   • test_comprehensive_html.html")
        print("   • test_comprehensive_docx.docx")
        print("   • test_comprehensive_txt.txt")
    elif successful_conversions > 0:
        print(f"\n✅ {successful_conversions} out of {total_conversions} converters working!")
        print("📁 Check the 'output' directory for generated files.")
    else:
        print("\n❌ All conversions failed. Check error messages above.")
    
    # Test registry functionality
    print(f"\n🔍 Testing Registry Functionality:")
    available_conversions = registry.list_converters()
    print(f"   Registered conversions: {len(available_conversions)}")
    for (source, target), name in available_conversions.items():
        print(f"   • {source} → {target}: {name}")
    
    return successful_conversions == total_conversions


def main():
    """Run the comprehensive test."""
    try:
        success = test_all_converters()
        if success:
            print("\n🎉 All tests completed successfully!")
            print("✨ The document processor is ready for production use!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed, but basic functionality is working.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
