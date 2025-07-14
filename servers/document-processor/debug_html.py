#!/usr/bin/env python3
"""
Debug script to see what HTML is being generated.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from domain import Document, ConversionOptions, PDFEngine
from converters import MarkdownToPdfConverter


def main():
    """Debug HTML generation."""
    print("🔍 Debugging HTML Generation")
    print("=" * 50)
    
    # Create a simple document
    doc = Document.from_markdown(
        content="# Test\n\nThis is a **test** document.",
        title="Debug Test"
    )
    
    # Create converter
    converter = MarkdownToPdfConverter()
    
    # Test 1: Raw markdown to HTML
    print("1. Raw markdown to HTML:")
    html_content = converter._markdown_to_html(doc, ConversionOptions())
    print(f"Length: {len(html_content)} characters")
    print("Content preview:")
    print(html_content[:200] + "..." if len(html_content) > 200 else html_content)
    print()
    
    # Test 2: With template
    print("2. With template applied:")
    options = ConversionOptions(template_name="simple.html")
    try:
        templated_html = converter._apply_template(html_content, doc, options)
        print(f"Length: {len(templated_html)} characters")
        print("Content preview:")
        print(templated_html[:300] + "..." if len(templated_html) > 300 else templated_html)
        
        # Check if it starts with DOCTYPE
        starts_with_doctype = templated_html.strip().startswith('<!DOCTYPE')
        starts_with_html = templated_html.strip().startswith('<html')
        print(f"Starts with DOCTYPE: {starts_with_doctype}")
        print(f"Starts with <html: {starts_with_html}")
        
    except Exception as e:
        print(f"Template error: {e}")


if __name__ == "__main__":
    main()
