#!/usr/bin/env python3
"""
Simple example showing how to use the document processor.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from domain import Document, ConversionOptions, PDFEngine
from converters import MarkdownToPdfConverter


def main():
    """Demonstrate simple usage of the document processor."""
    print("📚 Document Processor - Simple Usage Example")
    print("=" * 50)
    
    # Step 1: Create a document from markdown
    markdown_text = """# My Report

## Introduction

This is a simple example of converting **markdown** to PDF using our document processor.

### Features

- Clean domain model
- Multiple PDF engines
- Template support
- Easy to use API

### Code Example

```python
# Simple usage
doc = Document.from_markdown(content, title="My Report")
converter = MarkdownToPdfConverter()
result = converter.convert(doc, options)
```

## Conclusion

The document processor makes it easy to convert markdown to high-quality PDF documents.
"""
    
    # Create document
    doc = Document.from_markdown(
        content=markdown_text,
        title="My Report",
        author="Example User"
    )
    
    print(f"✅ Created document: '{doc.metadata.title}'")
    print(f"📊 Stats: {doc.word_count} words, {doc.character_count} characters")
    
    # Step 2: Create converter
    converter = MarkdownToPdfConverter()
    print(f"🔧 Using: {converter.name}")
    
    # Step 3: Configure options
    options = ConversionOptions(
        filename="my_report",
        template_name="simple.html",  # Use our template
        pdf_engine=PDFEngine.WEASYPRINT,
        title="My Report",
        author="Example User",
        page_size="A4"
    )
    
    print(f"⚙️  Engine: {options.pdf_engine.value}")
    print(f"📄 Template: {options.template_name}")
    
    # Step 4: Convert to PDF
    print("\n🔄 Converting to PDF...")
    result = converter.convert(doc, options)
    
    # Step 5: Check result
    if result.success:
        print(f"✅ Success! PDF generated:")
        print(f"   📁 File: {result.output_file_path}")
        print(f"   📊 Size: {result.file_size_bytes:,} bytes")
        print(f"   ⏱️  Time: {result.conversion_time_seconds:.2f} seconds")
        print(f"   🔧 Engine: {result.engine_used}")
        
        # Show metadata
        if result.metadata:
            print(f"   📝 Original words: {result.metadata.get('original_word_count')}")
            print(f"   🎨 Template: {result.metadata.get('template_used')}")
    else:
        print(f"❌ Conversion failed:")
        print(f"   Error: {result.error_message}")
        if result.error_details:
            print(f"   Details: {result.error_details}")
    
    print("\n" + "=" * 50)
    print("🎉 Example completed!")
    print("💡 This demonstrates the clean, simple API of our document processor.")


if __name__ == "__main__":
    main()
