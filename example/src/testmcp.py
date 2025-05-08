from mcp.server.fastmcp import FastMCP

# Create MCP server
server = FastMCP("somename")

# Define a simple calculator tool
@server.tool()
def calculator(operation: str, x: float, y: float) -> dict:
    """
    A simple calculator tool.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        x: First number
        y: Second number
    
    Returns:
        Result as a dictionary
    """
    if operation == "add":
        result = x + y
    elif operation == "subtract":
        result = x - y
    elif operation == "multiply":
        result = x * y
    elif operation == "divide":
        if y == 0:
            raise ValueError("Cannot divide by zero")
        result = x / y
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    return {"result": result}

# Run the server with stdio transport
if __name__ == "__main__":
    server.run("stdio")
