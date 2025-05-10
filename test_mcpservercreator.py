#!/usr/bin/env python3
"""
Test driver for mcpservercreator to verify it generates syntactically valid code.

This script directly imports the functions from mcpservercreator and tests the file
generation without going through the installation and VS Code restart cycle.
"""

import os
import sys
import tempfile
import shutil
import importlib.util
import ast
from pathlib import Path

# Add mcpservercreator to the path
sys.path.append(str(Path("mcpservercreator/src").absolute()))

# Import mcpservercreator functions directly
try:
    from server import create_server_files, validate_code_snippet
    from config import settings
except ImportError:
    print("Error: Could not import mcpservercreator modules")
    sys.exit(1)


def test_mcpservercreator():
    """Test the mcpservercreator file generation."""
    print("\n=== Testing mcpservercreator file generation ===\n")
    
    # Create a temporary directory for the test server
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        server_name = "test-server"
        server_dir = temp_path / server_name
        server_dir.mkdir(exist_ok=True)
        
        # Sample code snippet with two MCP tools - Use triple single quotes to avoid nesting issues
        code_snippet = '''
import random

@mcp.tool()
def random_number(min_value: int = 1, max_value: int = 100) -> dict:
    """
    Generate a random number between min_value and max_value.
    
    Args:
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        
    Returns:
        Dictionary with the generated number
    """
    number = random.randint(min_value, max_value)
    return {"number": number}

@mcp.tool()
def random_choice(options: list) -> dict:
    """
    Choose a random item from the provided options.
    
    Args:
        options: List of options to choose from
        
    Returns:
        Dictionary with the chosen option
    """
    if not options:
        return {"error": "No options provided"}
    
    choice = random.choice(options)
    return {"choice": choice}
'''
        
        description = "Test MCP server for random number generation and selection"
        author = "Test Driver"
        
        try:
            # Validate the code snippet
            print("Validating code snippet...")
            tool_names = validate_code_snippet(code_snippet)
            print(f"Detected tools: {', '.join(tool_names)}")
            
            # Create the server files
            print(f"Creating server files in {server_dir}...")
            create_server_files(
                server_dir=server_dir,
                server_name=server_name,
                code_snippet=code_snippet,
                description=description,
                author=author,
                tool_names=tool_names
            )
            
            # Check if files were created
            src_dir = server_dir / "src"
            expected_files = [
                src_dir / "__init__.py",
                src_dir / "config.py",
                src_dir / "server.py",
                src_dir / "main.py",
                server_dir / "requirements.txt"
            ]
            
            print("\nChecking generated files:")
            all_files_exist = True
            for file_path in expected_files:
                exists = file_path.exists()
                print(f"  {file_path.name}: {'✅ Found' if exists else '❌ Missing'}")
                all_files_exist = all_files_exist and exists
            
            if not all_files_exist:
                print("❌ Error: Some expected files are missing")
                return False
            
            # Check if Python files are syntactically valid
            print("\nVerifying Python syntax in generated files:")
            python_files = [f for f in expected_files if f.suffix == '.py']
            all_syntax_valid = True
            
            for py_file in python_files:
                with open(py_file, 'r') as f:
                    source = f.read()
                
                try:
                    ast.parse(source)
                    print(f"  {py_file.name}: ✅ Valid Python syntax")
                except SyntaxError as e:
                    print(f"  {py_file.name}: ❌ Syntax Error: {str(e)}")
                    all_syntax_valid = False
            
            if not all_syntax_valid:
                print("❌ Error: Some files have syntax errors")
                return False
            
            # Check for server name consistency
            print("\nChecking server name consistency:")
            with open(src_dir / "config.py", 'r') as f:
                config_content = f.read()
            
            # Check if the server_name in config.py has -server suffix
            if f'server_name: str = os.getenv("SERVER_NAME", "{server_name}")' in config_content:
                print(f"  config.py: ✅ Server name is correct ({server_name})")
            else:
                print(f"  config.py: ❌ Server name is incorrect or has -server suffix")
                return False
            
            # Verify proper indentation in server.py
            print("\nVerifying tool function indentation in server.py:")
            with open(src_dir / "server.py", 'r') as f:
                server_content = f.read()
            
            # Check if tools are defined inside register_tools_and_resources
            if '@mcp.tool()' in server_content and 'def register_tools_and_resources(mcp: FastMCP)' in server_content:
                tool_definition_pos = server_content.find('@mcp.tool()')
                function_definition_pos = server_content.find('def register_tools_and_resources(mcp: FastMCP)')
                
                if tool_definition_pos > function_definition_pos:
                    print("  server.py: ✅ Tool definitions are inside register_tools_and_resources")
                else:
                    print("  server.py: ❌ Tool definitions are outside register_tools_and_resources")
                    return False
            else:
                print("  server.py: ❌ Missing tool definitions or register_tools_and_resources function")
                return False
            
            # Success!
            print("\n✅ All tests passed! mcpservercreator is generating valid code.")
            return True
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            return False


if __name__ == "__main__":
    success = test_mcpservercreator()
    sys.exit(0 if success else 1)
