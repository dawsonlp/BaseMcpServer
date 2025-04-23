"""
MCP server implementation for the DirectlyRunTest server.

This module defines tools and resources for the MCP server.
"""

from typing import Dict
from mcp.server.fastmcp import FastMCP


def register_tools_and_resources(mcp: FastMCP):
    """
    Register tools and resources with the provided MCP server instance.
    
    Args:
        mcp: A FastMCP server instance to register tools and resources with
    """
    
    # Add the test_directly tool
    @mcp.tool()
    def test_directly(text: str) -> Dict[str, str]:
        """
        A simple test tool that counts the characters in the input text.
        
        Args:
            text: The input text to measure
            
        Returns:
            A dictionary containing the result message
        """
        char_count = len(text)
        result = f"tried with {char_count} characters"
        
        return {"result": result}
