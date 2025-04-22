# FastMCP vs Low-Level Server Implementation

This document explains the differences between the low-level MCP Server implementation and the more ergonomic FastMCP approach, including migration considerations and best practices.

## Overview

The MCP Python SDK offers two main approaches for creating MCP servers:

1. **Low-Level Server** (`mcp.server.lowlevel.Server`): Direct access to the MCP protocol with more manual implementation.
2. **FastMCP** (`mcp.server.fastmcp.FastMCP`): High-level, ergonomic API with simplified abstractions.

This project has been migrated from the low-level Server implementation to FastMCP to leverage its improved developer experience and additional features.

## Key Differences

### Implementation Complexity

**Low-Level Server:**
```python
server = Server("server-name")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="example",
            description="An example tool",
            inputSchema={
                "type": "object",
                "required": ["input"],
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input string to process",
                    }
                },
            },
        )
    ]

@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name != "example":
        raise ValueError(f"Unknown tool: {name}")
    
    if "input" not in arguments:
        raise ValueError("Missing required argument 'input'")
    
    input_value = arguments["input"]
    processed_result = f"Processed: {input_value}"
    
    return [types.TextContent(type="text", text=processed_result)]
```

**FastMCP:**
```python
mcp = FastMCP("server-name")

@mcp.tool()
def example(input: str) -> str:
    """An example tool that processes input text"""
    return f"Processed: {input}"
```

### Key Benefits of FastMCP

1. **Reduced Boilerplate**: Significantly less code required for the same functionality.
2. **Type Safety**: Automatic type validation and conversion based on Python type hints.
3. **Automatic Schema Generation**: Input schemas are automatically generated from function signatures.
4. **Simplified Error Handling**: Errors from tools are properly formatted and returned to clients.
5. **Context Object**: Easy access to MCP capabilities like logging and progress reporting.
6. **ASGI Integration**: Built-in support for ASGI servers like Starlette and FastAPI.
7. **Resource Templates**: Simplified handling of parameterized resources.
8. **Lifespan Management**: Type-safe application lifecycle management.

## Feature Comparison

| Feature | Low-Level Server | FastMCP |
|---------|-----------------|---------|
| MCP Protocol Support | Full | Full |
| Code Verbosity | High | Low |
| Type Safety | Manual | Automatic |
| Schema Generation | Manual | Automatic |
| Error Handling | Manual | Automatic |
| Progress Reporting | Manual | Built-in via Context |
| Logging | Manual | Built-in via Context |
| ASGI Integration | Manual | Built-in |
| Resource Templates | Manual | Automatic Parameter Binding |
| Lifespan Management | Basic | Type-safe with Context |

## Migration Guide

### Step 1: Change Server Creation

```python
# Before: Low-level Server
from mcp.server.lowlevel import Server
server = Server("server-name")

# After: FastMCP
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("server-name")
```

### Step 2: Convert Tool Definitions

```python
# Before: Low-level Server
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="example",
            description="An example tool",
            inputSchema={...},
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | ...]:
    if name == "example":
        # Implementation
        return [types.TextContent(type="text", text="result")]

# After: FastMCP
@mcp.tool()
def example(parameter1: str, parameter2: int) -> str:
    """Tool description here"""
    # Implementation
    return "result"
```

### Step 3: Convert Resource Definitions

```python
# Before: Low-level Server
@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="resource://example",
            name="Example Resource",
            description="An example resource",
            mimeType="text/plain",
        )
    ]

@server.read_resource()
async def read_resource(uri: AnyUrl) -> Iterable[ReadResourceContents]:
    if uri == "resource://example":
        return [ReadResourceContents(content="Resource content", mime_type="text/plain")]

# After: FastMCP
@mcp.resource("resource://example")
def example_resource() -> str:
    """An example resource"""
    return "Resource content"

# Template resource with parameters
@mcp.resource("resource://{param}/data")
def parameterized_resource(param: str) -> str:
    """Resource with parameters"""
    return f"Data for {param}"
```

### Step 4: Update Server Execution

```python
# Before: Manual Starlette setup
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)
uvicorn.run(app, host=settings.host, port=settings.port)

# After: Built-in FastMCP execution
if __name__ == "__main__":
    mcp.run("sse")  # or "stdio" for CLI usage
```

## Best Practices with FastMCP

1. **Use Type Hints**: Leverage Python type hints for automatic schema generation and validation.

   ```python
   @mcp.tool()
   def analyze_data(data: list[int], threshold: float = 0.5) -> dict:
       """
       The type hints automatically create the correct schema and validate inputs.
       Optional parameters like threshold get default values.
       """
       return {"result": [x for x in data if x > threshold]}
   ```

2. **Use Context for Advanced Features**: The Context object provides access to MCP capabilities.

   ```python
   @mcp.tool()
   async def long_task(items: list[str], ctx: Context) -> str:
       """Process multiple items with progress tracking"""
       for i, item in enumerate(items):
           # Log to client
           await ctx.info(f"Processing {item}")
           
           # Report progress
           await ctx.report_progress(i, len(items))
           
           # Process item
           # ...
           
       return "Processing complete"
   ```

3. **Use Resource Templates** for dynamic resources:

   ```python
   @mcp.resource("users://{user_id}/profile")
   async def get_user_profile(user_id: str) -> str:
       """Get profile for a specific user"""
       user = await db.get_user(user_id)
       return json.dumps(user.profile)
   ```

4. **Use Lifespan for Setup/Teardown**:

   ```python
   from contextlib import asynccontextmanager
   from collections.abc import AsyncIterator

   @asynccontextmanager
   async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
       # Initialize on startup
       db = await Database.connect()
       try:
           yield {"db": db}
       finally:
           # Cleanup on shutdown
           await db.disconnect()

   mcp = FastMCP("My App", lifespan=lifespan)

   @mcp.tool()
   def query_db(query: str, ctx: Context) -> list:
       """Query the database"""
       db = ctx.request_context.lifespan_context["db"]
       return db.execute(query)
   ```

5. **Leverage Built-in Server Support**:

   ```python
   # For development with automatic reloading
   # Run: python -m mcp dev server.py

   # For Claude Desktop integration
   # Run: python -m mcp install server.py

   # For direct execution with stdio (CLI)
   if __name__ == "__main__":
       mcp.run("stdio")

   # For HTTP server
   if __name__ == "__main__":
       mcp.run("sse")
   ```

## Conclusion

FastMCP significantly simplifies MCP server development while providing a more robust feature set. The migration from low-level Server to FastMCP reduces code complexity, improves maintainability, and enables easier access to advanced MCP features.

For additional information, refer to the [MCP Python SDK documentation](https://modelcontextprotocol.io).
