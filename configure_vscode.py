#!/usr/bin/env python3
"""
Script to configure VS Code Cline integration with the installed MCP server.
This script handles Python path issues by adding the correct parent directory to sys.path.
"""

import os
import sys
from pathlib import Path

# Add the project root to sys.path so we can import utils.mcp_manager
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Now import the configure_editor function
from utils.mcp_manager.src.mcp_manager.commands.configure import configure_editor
from utils.mcp_manager.src.mcp_manager.server import create_directory_structure

def main():
    print("Configuring VS Code Cline integration...")
    
    # Create the MCP directory structure if it doesn't exist
    create_directory_structure()
    
    try:
        # Configure VS Code Cline integration
        configure_editor("vscode", backup=True)
        print("Successfully configured VS Code Cline integration")
    except Exception as e:
        print(f"Error configuring VS Code Cline integration: {e}")
        sys.exit(1)
    
    print("\nNext steps:")
    print("1. Restart VS Code")
    print("2. Test the MCP server connection using the 'example' server")

if __name__ == "__main__":
    main()
