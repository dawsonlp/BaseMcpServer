# Document Processor

A clean, domain-driven document conversion system built with hexagonal architecture principles.

## Overview

This document processor converts markdown documents to various formats (HTML, PDF, DOCX, TXT) using a clean domain model that separates business logic from infrastructure concerns.

## Architecture

### Domain Model (Pure Business Logic)

- **Document**: Core entity representing content and metadata
- **DocumentFormat**: Enum of supported formats with properties
- **ConversionOptions**: Configuration for conversion operations
- **DocumentConverter**: Abstract interface for converters
- **ConversionResult**: Value object for conversion outcomes
- **ConverterRegistry**: Registry pattern for managing converters

### Key Design Principles

- **Domain-Driven Design**: Business logic is independent of frameworks
- **Hexagonal Architecture**: Clear separation of concerns
- **Strategy Pattern**: Pluggable converters for different formats
- **Value Objects**: Immutable data structures
- **Factory Methods**: Clean object creation

## Project Structure

```
servers/document-processor/
├── domain/                    # Pure domain logic
│   ├── __init__.py           # Domain exports
│   ├── document.py           # Document entity and metadata
│   ├── formats.py            # Format enums and options
│   ├── converters.py         # Converter interfaces and registry
│   └── exceptions.py         # Domain-specific exceptions
├── tests/                    # Domain model tests
│   ├── __init__.py
│   └── test_domain.py        # Comprehensive domain tests
├── templates/                # HTML templates for conversion
├── output/                   # Generated output files
├── venv/                     # Python virtual environment
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Current Status

✅ **Complete Document Processor**
- All core domain objects implemented
- Comprehensive test coverage
- Clean interfaces and abstractions

✅ **All Four Converters Working**
- **Markdown → PDF**: WeasyPrint and ReportLab engines
- **Markdown → HTML**: Standalone HTML with CSS styling
- **Markdown → DOCX**: Microsoft Word documents with formatting
- **Markdown → TXT**: Clean plain text output

✅ **Production Ready**
- Comprehensive error handling
- Multiple working examples and tests
- Clean, simple API
- Fast and reliable conversions

🚧 **Future Enhancements**
- Add MCP server integration
- Create application services layer
- Add batch processing capabilities
- Support for additional input formats

## Dependencies

Core document processing libraries:
- `markdown` - Markdown parsing and conversion
- `weasyprint` - HTML to PDF conversion with CSS support
- `python-docx` - Microsoft Word document generation
- `html2text` - HTML to plain text conversion
- `jinja2` - Template rendering
- `reportlab` - Alternative PDF generation

Development and testing:
- `pytest` - Testing framework
- `pytest-cov` - Test coverage

## Usage Example

```python
from domain import Document, DocumentFormat, ConversionOptions

# Create a document
doc = Document.from_markdown(
    content="# Hello World\n\nThis is a test document.",
    title="Test Document",
    author="Test Author"
)

# Configure conversion options
options = ConversionOptions(
    filename="test_output",
    template_name="professional.html",
    save_to_file=True
)

# Convert using a registered converter
registry = ConverterRegistry()
converter = registry.get_converter(DocumentFormat.MARKDOWN, DocumentFormat.HTML)
result = converter.convert(doc, options)

if result.success:
    print(f"Converted successfully: {result.output_file_path}")
else:
    print(f"Conversion failed: {result.error_message}")
```

## Testing

Run the domain model tests:

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/test_domain.py -v
```

## Design Decisions

### Why Hexagonal Architecture?

1. **Testability**: Domain logic can be tested without external dependencies
2. **Flexibility**: Easy to swap out infrastructure components
3. **Maintainability**: Clear separation of concerns
4. **Extensibility**: New formats and converters can be added easily

### Why Domain-First Approach?

1. **Business Focus**: Core logic reflects real-world document processing
2. **Framework Independence**: Not tied to any specific web framework or MCP library
3. **Reusability**: Domain model can be used in different contexts
4. **Clarity**: Business rules are explicit and well-defined

## Future Enhancements

- Support for additional input formats (HTML, DOCX → Markdown)
- Batch processing capabilities
- Document validation and sanitization
- Custom template system
- Plugin architecture for custom converters
- Async processing for large documents
- Document metadata extraction and enrichment
