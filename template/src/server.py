"""
MCP server implementation template.

This module defines the MCP server and provides templates for tools and resources.
Customize this file to implement your own MCP server functionality.
"""

from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Any, Optional


def create_mcp_server():
    """
    Create and configure an MCP server instance using FastMCP.
    
    Returns:
        FastMCP: A configured FastMCP server instance
    """
    # Create a FastMCP server instance with a unique name
    # Replace "your-mcp-server-name" with your actual server name
    mcp = FastMCP("your-mcp-server-name")
    
    # EXAMPLE TOOL - Replace with your own tools
    @mcp.tool()
    def example_tool(param1: str, param2: int, optional_param: Optional[bool] = None) -> Dict[str, Any]:
        """
        Example tool template - Replace with your own implementation.
        
        This demonstrates how to create a tool with required and optional parameters.
        
        Args:
            param1: First parameter (string)
            param2: Second parameter (integer)
            optional_param: Optional parameter (boolean)
            
        Returns:
            A dictionary containing the result
        """
        # Replace this implementation with your actual tool logic
        result = {
            "param1_received": param1,
            "param2_received": param2,
            "optional_param_received": optional_param,
            "message": "This is a placeholder. Implement your tool logic here."
        }
        
        return result
    
    # EXAMPLE RESOURCE - Replace with your own resources
    @mcp.resource("resource://example")
    def example_resource() -> Dict[str, Any]:
        """
        Example resource template - Replace with your own implementation.
        
        This demonstrates how to create a simple resource that returns data.
        
        Returns:
            A dictionary containing the resource data
        """
        # Replace this implementation with your actual resource data
        return {
            "name": "Example Resource",
            "type": "template",
            "message": "This is a placeholder. Replace with your own resource data."
        }
    
    # EXAMPLE PARAMETERIZED RESOURCE - Replace with your own implementation
    @mcp.resource("resource://example/{id}")
    def example_parameterized_resource(id: str) -> Dict[str, Any]:
        """
        Example parameterized resource template - Replace with your own implementation.
        
        This demonstrates how to create a resource that accepts a path parameter.
        
        Args:
            id: An identifier passed in the resource URI
            
        Returns:
            A dictionary containing the resource data
        """
        # Replace this implementation with your actual resource logic
        return {
            "id": id,
            "name": f"Resource with ID {id}",
            "message": "This is a placeholder. Implement your parameterized resource logic here."
        }
    
    # Add more tools and resources as needed
    # For example:
    #
    # @mcp.tool()
    # def your_custom_tool(...):
    #     """Tool documentation"""
    #     # Your implementation
    #
    # @mcp.resource("resource://your-custom-resource")
    # def your_custom_resource(...):
    #     """Resource documentation"""
    #     # Your implementation
    
    return mcp
