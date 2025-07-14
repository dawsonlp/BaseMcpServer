#!/usr/bin/env python3
"""
Simple test script to verify document conversion functionality.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, '/app/src')

def test_basic_imports():
    """Test that all our modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from domain.models import DocumentFormat, ConversionRequest
        print("✅ Domain models imported")
        
        from infrastructure.converters import MarkdownConverter
        print("✅ Markdown converter imported")
        
        from infrastructure.config import SettingsConfigurationProvider
        print("✅ Config imported")
        
        from infrastructure.storage import LocalFileStorage
        print("✅ Storage imported")
        
        from application.use_cases import ConvertDocumentUseCase
        print("✅ Use cases imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pandoc_availability():
    """Test that pandoc is available."""
    print("\n🔍 Testing pandoc availability...")
    
    import subprocess
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Pandoc available: {version_line}")
            return True
        else:
            print(f"❌ Pandoc error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Pandoc not available: {e}")
        return False

def test_simple_conversion():
    """Test a simple markdown to HTML conversion."""
    print("\n🔍 Testing simple conversion...")
    
    try:
        from domain.models import DocumentFormat, ConversionRequest
        from infrastructure.converters import MarkdownConverter
        from infrastructure.templates import Jinja2TemplateRenderer
        from pathlib import Path
        
        # Create test markdown
        test_markdown = """# Test Document

This is a **test** document with:

- Bullet points
- *Italic text*  
- [Links](https://example.com)

## Code Example

```python
print("Hello, World!")
```

> This is a blockquote.
"""
        
        # Create template renderer and converter
        template_renderer = Jinja2TemplateRenderer(Path("/app/templates"))
        converter = MarkdownConverter(template_renderer)
        
        # Create conversion request
        request = ConversionRequest(
            source_content=test_markdown,
            target_format=DocumentFormat.HTML,
            filename="test_doc"
        )
        
        # Perform conversion
        print("Converting markdown to HTML...")
        import asyncio
        result = asyncio.run(converter.convert(request))
        
        if result.success and result.document:
            print("✅ Conversion successful!")
            print(f"📄 Output length: {len(result.document.content)} characters")
            print(f"🔧 Engine used: {result.engine_used}")
            
            # Show first 200 characters
            preview = result.document.content[:200].replace('\n', '\\n')
            print(f"📝 Preview: {preview}...")
            
            # Save to output directory
            output_path = Path("/app/output/test_conversion.html")
            output_path.parent.mkdir(exist_ok=True)
            output_path.write_text(result.document.content)
            print(f"💾 Saved to: {output_path}")
            
            return True
        else:
            print(f"❌ Conversion failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting document processor tests...\n")
    
    # Test imports
    if not test_basic_imports():
        return False
    
    # Test pandoc
    if not test_pandoc_availability():
        return False
    
    # Test conversion
    if not test_simple_conversion():
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
