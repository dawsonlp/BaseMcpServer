#!/usr/bin/env python3
"""
Script to install the example MCP server using our modified mcp_manager code.
This script handles Python path issues by adding the correct parent directory to sys.path.
"""

import os
import sys
from pathlib import Path

# Add the project root to sys.path so we can import utils.mcp_manager
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Now import the install function
from utils.mcp_manager.src.mcp_manager.commands.install import install_local_server

def main():
    print("Installing example MCP server...")
    
    # Source directory for the example server
    example_dir = project_root / "example"
    
    try:
        # Use our modified install_local_server function directly
        install_local_server("example", example_dir, port=None, force=True)
        print("Successfully installed example MCP server")
    except Exception as e:
        print(f"Error installing example MCP server: {e}")
        sys.exit(1)
    
    print("\nNext steps:")
    print("1. Configure VS Code Cline integration")
    print("2. Test the MCP server connection")

if __name__ == "__main__":
    main()
