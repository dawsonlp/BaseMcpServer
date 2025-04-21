"""
MCP server implementation for the example server.

This module defines the MCP server and its tools/resources.
"""

from mcp.server.fastmcp import FastMCP
import random
from typing import List, Dict, Optional


def create_mcp_server():
    """
    Create and configure an MCP server instance using FastMCP.
    
    Returns:
        FastMCP: A configured FastMCP server instance
    """
    # Create a FastMCP server instance with a unique name
    mcp = FastMCP("example-mcp-server")
    
    # Add a calculator tool
    @mcp.tool()
    def calculator(operation: str, x: float, y: float) -> Dict[str, float]:
        """
        A simple calculator tool that performs basic arithmetic operations.
        
        Args:
            operation: The arithmetic operation (add, subtract, multiply, divide)
            x: The first number
            y: The second number
            
        Returns:
            A dictionary containing the result
        """
        if operation.lower() == "add":
            result = x + y
        elif operation.lower() == "subtract":
            result = x - y
        elif operation.lower() == "multiply":
            result = x * y
        elif operation.lower() == "divide":
            if y == 0:
                raise ValueError("Cannot divide by zero")
            result = x / y
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
        return {"result": result}
    
    # Add a weather tool that returns simulated weather data
    @mcp.tool()
    def get_weather(city: str, country: Optional[str] = None) -> Dict[str, any]:
        """
        Get simulated weather data for a given location.
        
        Args:
            city: The city name
            country: The country code (optional)
            
        Returns:
            Simulated weather data
        """
        # In a real implementation, this would call a weather API
        # This is just a simulation
        location = f"{city}, {country}" if country else city
        
        # Simulate random weather data
        conditions = random.choice(["Sunny", "Cloudy", "Rainy", "Snowy", "Windy"])
        temperature = round(random.uniform(-10, 40), 1)
        humidity = random.randint(0, 100)
        
        return {
            "location": location,
            "temperature": temperature,
            "unit": "Celsius",
            "conditions": conditions,
            "humidity": humidity
        }
    
    # Add a resource that returns a list of quotes
    @mcp.resource("resource://quotes")
    def quotes_resource() -> List[Dict[str, str]]:
        """
        A resource that provides a list of inspirational quotes.
        
        Returns:
            A list of quote dictionaries
        """
        return [
            {"text": "The best way to predict the future is to invent it.", "author": "Alan Kay"},
            {"text": "It's not that I'm so smart, it's just that I stay with problems longer.", "author": "Albert Einstein"},
            {"text": "Simplicity is the ultimate sophistication.", "author": "Leonardo da Vinci"},
            {"text": "Code is like humor. When you have to explain it, it's bad.", "author": "Cory House"}
        ]
    
    # Add a parameterized resource
    @mcp.resource("resource://quotes/{index}")
    def quote_by_index(index: int) -> Dict[str, str]:
        """
        Get a specific quote by its index.
        
        Args:
            index: The index of the quote (0-3)
            
        Returns:
            A quote dictionary
        """
        quotes = [
            {"text": "The best way to predict the future is to invent it.", "author": "Alan Kay"},
            {"text": "It's not that I'm so smart, it's just that I stay with problems longer.", "author": "Albert Einstein"},
            {"text": "Simplicity is the ultimate sophistication.", "author": "Leonardo da Vinci"},
            {"text": "Code is like humor. When you have to explain it, it's bad.", "author": "Cory House"}
        ]
        
        if index < 0 or index >= len(quotes):
            raise ValueError(f"Index out of range: {index}")
        
        return quotes[index]
    
    return mcp
