#!/usr/bin/env python3
"""
Entry point for the Document Processor CLI.

This script provides a clean entry point that avoids module import warnings.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from cli.main import app

if __name__ == "__main__":
    app()
