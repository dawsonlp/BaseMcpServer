# MCP SDK Architecture Analysis

## Executive Summary

After analyzing the Python MCP SDK source code, I've discovered that **the SDK already has excellent separation of concerns**. The issue isn't with the SDK design - it's with how we're using it. The SDK provides a clean, transport-agnostic core with FastMCP as a convenience wrapper.

## Key Findings

### 1. The SDK Has Perfect Architecture Already

```
Low-Level MCP Server (mcp.server.lowlevel.Server)
    ↓ (transport-agnostic)
FastMCP (mcp.server.fastmcp.FastMCP) 
    ↓ (convenience wrapper)
Transport Implementations (stdio, sse, streamable-http)
```

### 2. FastMCP is NOT the Problem

FastMCP actually provides exactly what you want:
- **Transport-agnostic server core** (`self._mcp_server = MCPServer()`)
- **Clean tool registration** (`self._tool_manager`)
- **Runtime transport selection** (`mcp.run(transport="sse")`)

### 3. The Real Architecture

#### Core Components (Transport-Agnostic)
```python
# Low-level server - completely transport agnostic
from mcp.server.lowlevel.server import Server as MCPServer

server = MCPServer("MyServer")

@server.call_tool()
async def handle_tool_call(name: str, arguments: dict) -> list[ContentBlock]:
    # Pure business logic - no transport awareness
    pass

# Run with any transport
async with stdio_server() as (read, write):
    await server.run(read, write, InitializationOptions())
```

#### FastMCP Wrapper (Still Transport-Agnostic)
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MyServer")

@mcp.tool()
def my_tool(param: str) -> str:
    # Pure business logic
    return f"Result: {param}"

# Transport chosen at runtime
mcp.run(transport="stdio")    # or "sse" or "streamable-http"
```

## What We've Been Doing Wrong

### Problem: Multiple Entry Points
We've been creating separate entry points for each transport:
- `main.py` (stdio)
- `streamable_main.py` (streamable-http) 
- `sse_main.py` (sse)

### Solution: Single Entry Point with Runtime Selection
```python
# single_main.py
from adapters.mcp_adapter import mcp
import sys

def main():
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()
```

Usage:
```bash
python single_main.py stdio
python single_main.py sse  
python single_main.py streamable-http
```

## Recommended Architecture Pattern

### 1. Pure Business Logic Layer
```python
# business/jira_operations.py - No MCP dependencies
async def list_projects(jira_context, instance_name=None):
    return await jira_context.project_service.list_projects(instance_name)

async def create_issue(jira_context, project_key, summary, description):
    return await jira_context.issue_service.create_issue(project_key, summary, description)
```

### 2. MCP Tool Registration Layer
```python
# mcp/tool_registry.py
from mcp.server.fastmcp import FastMCP
from business.jira_operations import list_projects, create_issue

def create_jira_mcp_server(context) -> FastMCP:
    mcp = FastMCP("Jira Helper")
    
    @mcp.tool()
    async def list_jira_projects(instance_name: str = None):
        return await list_projects(context, instance_name)
    
    @mcp.tool() 
    async def create_jira_ticket(project_key: str, summary: str, description: str):
        return await create_issue(context, project_key, summary, description)
    
    return mcp
```

### 3. Universal Entry Point
```python
# main.py - Single entry point for all transports
import sys
from contextlib import asynccontextmanager
from mcp.tool_registry import create_jira_mcp_server
from infrastructure.context import create_jira_context

@asynccontextmanager
async def jira_lifespan(server):
    context = await create_jira_context()
    yield context

def main():
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    # Create context
    context = create_jira_context()
    
    # Create MCP server with business logic
    mcp = create_jira_mcp_server(context)
    
    # Run with selected transport
    if transport == "sse":
        mcp.settings.port = port
    
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()
```

### 4. Deployment Scripts
```python
# deploy/stdio.py
from main import main
import sys
sys.argv = ["main.py", "stdio"]
main()

# deploy/sse.py  
from main import main
import sys
sys.argv = ["main.py", "sse", "8000"]
main()

# deploy/docker_sse.py
from main import main
import sys
sys.argv = ["main.py", "sse", "8000"]
main()
```

## Benefits of This Approach

### 1. Single Source of Truth
- One place to define all tools
- One place to manage business logic
- One entry point for all transports

### 2. Runtime Transport Selection
```bash
# Development
python main.py stdio

# Cline integration  
python main.py sse

# Other MCP clients (when fixed)
python main.py streamable-http

# Docker deployment
docker run my-server sse 8000
```

### 3. Easy Testing
```python
# Test business logic independently
async def test_list_projects():
    context = create_test_context()
    result = await list_projects(context)
    assert result["success"] == True

# Test MCP integration
async def test_mcp_tool():
    mcp = create_jira_mcp_server(test_context)
    # Test tool registration and execution
```

### 4. Clean Separation
- **Business Logic**: Pure functions, no MCP awareness
- **MCP Layer**: Tool registration and protocol handling  
- **Transport Layer**: Runtime selection, no business logic
- **Deployment Layer**: Environment-specific configuration

## Implementation Plan

### Phase 1: Refactor Existing Jira Helper
1. **Extract business logic** from MCP decorators
2. **Create tool registry** that wraps business logic
3. **Single entry point** with transport selection
4. **Update deployment scripts** to use single entry point

### Phase 2: Create Reusable Pattern
1. **Abstract the pattern** into a reusable library
2. **Document best practices** for MCP server development
3. **Create templates** for new MCP servers

### Phase 3: Optimize for Cline
1. **Default to SSE transport** for HTTP deployment
2. **Streamline configuration** for Cline compatibility
3. **Add Cline-specific optimizations**

## Conclusion

The MCP SDK already provides exactly what you want - **clean separation between business logic and transport**. We just need to use it correctly:

1. **Use FastMCP properly** - single instance, runtime transport selection
2. **Separate business logic** from MCP decorators  
3. **Single entry point** with transport parameter
4. **Runtime configuration** instead of compile-time coupling

This approach gives us:
- ✅ **Transport-agnostic business logic**
- ✅ **Runtime transport selection** 
- ✅ **Single source of truth**
- ✅ **Easy deployment flexibility**
- ✅ **Clean testing story**

The SDK isn't the problem - our usage pattern is. Let's fix that!
