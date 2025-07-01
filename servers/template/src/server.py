"""
MCP server implementation template.

This module defines template tools and resources for the MCP server.
Customize this file to implement your own MCP server functionality.
"""

from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP
from config import settings


def register_tools_and_resources(srv: FastMCP):
    """
    Register tools and resources with the provided MCP server instance.
    
    Args:
        srv: A FastMCP server instance to register tools and resources with
    """
    # EXAMPLE TOOL - Replace with your own tools
    @srv.tool()
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
    @srv.resource("resource://example")
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
    @srv.resource("resource://example/{id}")
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
    # @srv.tool()
    # def your_custom_tool(...):
    #     """Tool documentation"""
    #     # Your implementation
    #
    # @srv.resource("resource://your-custom-resource")
    # def your_custom_resource(...):
    #     """Resource documentation"""
    #     # Your implementation
