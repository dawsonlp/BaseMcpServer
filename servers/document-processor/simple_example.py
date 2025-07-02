#!/usr/bin/env python3
"""
Simple example showing how to convert markdown to all four formats.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from domain import Document, ConversionOptions
from converters import (
    MarkdownToPdfConverter, MarkdownToHtmlConverter, 
    MarkdownToDocxConverter, MarkdownToTxtConverter
)


def main():
    """Simple example of converting to all formats."""
    print("📚 Simple Document Converter Example")
    print("=" * 50)
    
    # Create a simple document
    markdown_text = """# My Document

This is a simple example of converting **markdown** to multiple formats.

## Features

- Easy to use
- Multiple output formats
- Clean, readable results

### Code Example

```python
# Convert markdown to any format
doc = Document.from_markdown(content)
result = converter.convert(doc, options)
```

That's it! Simple and effective.
"""
    
    # Create document
    doc = Document.from_markdown(
        content=markdown_text,
        title="Simple Example",
        author="User"
    )
    
    print(f"📄 Document: '{doc.metadata.title}' ({doc.word_count} words)")
    
    # Convert to all formats
    converters = [
        ("PDF", MarkdownToPdfConverter()),
        ("HTML", MarkdownToHtmlConverter()),
        ("DOCX", MarkdownToDocxConverter()),
        ("TXT", MarkdownToTxtConverter()),
    ]
    
    print("\n🔄 Converting to all formats...")
    
    for format_name, converter in converters:
        options = ConversionOptions(
            filename=f"simple_example_{format_name.lower()}",
            title="Simple Example",
            author="User",
            save_to_file=True,
            standalone=True,
            include_css=True,
        )
        
        result = converter.convert(doc, options)
        
        if result.success:
            print(f"   ✅ {format_name:<6} → {result.output_file_path}")
        else:
            print(f"   ❌ {format_name:<6} → Failed: {result.error_message}")
    
    print("\n✨ Done! Check the output directory for your files.")


if __name__ == "__main__":
    main()
