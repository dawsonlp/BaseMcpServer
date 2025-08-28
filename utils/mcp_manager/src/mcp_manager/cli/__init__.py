"""
CLI package for MCP Manager.

Contains command-line interface components including commands and common utilities.
This package entry point imports the main CLI application.
"""

from mcp_manager.cli.app import app

__all__ = ['app']
