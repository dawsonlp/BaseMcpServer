"""
CLI interface for document processing.

This module provides a command-line interface using Typer that wraps
the application layer use cases.
"""

from .main import app

__all__ = ['app']
