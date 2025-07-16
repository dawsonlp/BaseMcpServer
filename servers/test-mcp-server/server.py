"""
Minimal MCP Server - Let FastMCP handle everything
"""
from mcp.server.fastmcp import FastMCP

# Create the simplest possible MCP server
mcp = FastMCP("TestServer")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Simple hello tool"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    # Let FastMCP handle everything - try SSE transport
    mcp.run(transport="sse")
