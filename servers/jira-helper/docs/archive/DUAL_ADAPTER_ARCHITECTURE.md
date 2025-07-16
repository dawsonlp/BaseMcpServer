# Dual Adapter Architecture for Jira Helper

This document describes the dual adapter architecture implemented in the Jira Helper MCP server, which supports both direct MCP communication and streamable HTTP transport while maintaining DRY principles.

## Architecture Overview

The Jira Helper now supports two deployment modes:

1. **Direct MCP Adapter** - Traditional MCP server using direct I/O communication
2. **Streamable HTTP Adapter** - HTTP-based MCP server for Docker deployment and multi-server integration

Both adapters share the same underlying business logic and tool definitions, ensuring DRY compliance and consistent functionality.

## Key Components

### Shared Components

#### `mcp_tools.py`
- Contains shared MCP tool definitions used by both adapters
- Implements `create_mcp_tools(context)` function that returns tool functions
- Provides `get_tool_schemas()` for tool metadata
- Ensures single source of truth for all MCP tool implementations

#### `mcp_adapter.py` (Refactored)
- Direct MCP adapter using FastMCP framework
- Uses shared tools from `mcp_tools.py`
- Maintains hexagonal architecture with dependency injection
- Supports traditional MCP client connections

#### `http_adapter.py`
- HTTP adapter using Starlette framework
- Exposes MCP tools via REST endpoints
- Uses same shared tools and context as direct adapter
- Supports Docker deployment and multi-server scenarios

## Deployment Modes

### Direct MCP Mode

**Use Case**: Traditional MCP client integration, local development

**Entry Point**: `src/main.py`

**Command**:
```bash
python src/main.py
```

**Features**:
- Direct I/O communication with MCP clients
- Low latency
- Traditional MCP protocol support

### HTTP Mode

**Use Case**: Docker deployment, multi-server integration, web-based access

**Entry Point**: `src/http_main.py`

**Command**:
```bash
python src/http_main.py
```

**Docker**:
```bash
docker build -f Dockerfile.http -t jira-helper-http .
docker run -p 8000:8000 jira-helper-http
```

**Docker Compose**:
```bash
docker compose -f docker-compose.http.yml up
```

**Features**:
- HTTP REST API endpoints
- Health checks and monitoring
- CORS support for web clients
- Containerized deployment

## API Endpoints (HTTP Mode)

### Health Check
```
GET /health
```
Returns server health status and metadata.

### List Tools
```
GET /tools
```
Returns list of available MCP tools with schemas.

### Call Tool
```
POST /tools/{tool_name}
Content-Type: application/json

{
  "argument1": "value1",
  "argument2": "value2"
}
```
Executes the specified MCP tool with provided arguments.

### Get Tool Schema
```
GET /tools/{tool_name}/schema
```
Returns the input schema for a specific tool.

## DRY Architecture Implementation

### Shared Tool Definitions

Both adapters use the same tool implementations from `mcp_tools.py`:

```python
# Direct MCP Adapter
@mcp.tool()
async def list_jira_projects(instance_name: Optional[str] = None) -> Dict[str, Any]:
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["list_jira_projects"](instance_name)

# HTTP Adapter
async def call_tool(self, request: Request) -> JSONResponse:
    tool_func = self.tools.get(tool_name)  # Same tools from create_mcp_tools()
    result = await tool_func(**arguments)
    return JSONResponse({"result": result})
```

### Shared Context and Services

Both adapters use the same:
- `JiraHelperContext` for dependency injection
- `jira_lifespan` for service initialization
- Use cases and domain services
- Infrastructure adapters

## Configuration

Both modes use the same configuration file (`config.yaml`) and support the same environment variables and Jira instance configurations.

## Testing Both Modes

### Direct MCP Mode Test
```bash
# Start the direct MCP server
python src/main.py

# Test with MCP client (in another terminal)
# Use your preferred MCP client to connect
```

### HTTP Mode Test
```bash
# Start the HTTP server
python src/http_main.py

# Test health endpoint
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/tools

# Call a tool
curl -X POST http://localhost:8000/tools/list_jira_projects \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Benefits of Dual Adapter Architecture

1. **DRY Compliance**: Single implementation of all MCP tools
2. **Deployment Flexibility**: Choose the right adapter for your use case
3. **Consistent Functionality**: Same business logic regardless of transport
4. **Hexagonal Architecture**: Clean separation of concerns
5. **Easy Testing**: Both modes can be tested independently
6. **Future-Proof**: Easy to add new transport mechanisms

## Migration Path

Existing users can continue using the direct MCP adapter without changes. The HTTP adapter provides additional deployment options without breaking existing functionality.

## Development Workflow

When adding new MCP tools:

1. Add tool implementation to `mcp_tools.py`
2. Add tool schema to `get_tool_schemas()`
3. Both adapters automatically support the new tool
4. Test both direct and HTTP modes

This ensures that new functionality is immediately available in both deployment modes without code duplication.
