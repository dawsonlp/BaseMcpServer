"""
Document processing domain module.

This module contains the core business logic for document conversion,
independent of any external frameworks or infrastructure concerns.
"""

from .formats import DocumentFormat, ConversionOptions, PDFEngine
from .document import Document, DocumentMetadata
from .converters import DocumentConverter, ConversionResult, ConverterRegistry
from .exceptions import DocumentProcessingError, ConversionError

__all__ = [
    'DocumentFormat',
    'ConversionOptions',
    'PDFEngine',
    'Document',
    'DocumentMetadata',
    'DocumentConverter',
    'ConversionResult',
    'ConverterRegistry',
    'DocumentProcessingError',
    'ConversionError',
]
