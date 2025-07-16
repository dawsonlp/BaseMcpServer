"""
HTTP adapter for the Jira Helper MCP server.

This module implements a streamable HTTP adapter that provides MCP tools
via HTTP endpoints, enabling Docker deployment and multi-server integration
while maintaining DRY principles by sharing tool definitions with the direct MCP adapter.
"""

import logging
import json
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from .mcp_tools import create_mcp_tools, get_tool_schemas
from .mcp_adapter import JiraHelperContext, jira_lifespan
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


class JiraHelperHTTPServer:
    """HTTP server for Jira Helper MCP tools using streamable HTTP transport."""
    
    def __init__(self):
        self.context: Optional[JiraHelperContext] = None
        self.tools: Optional[Dict[str, Any]] = None
        
    @asynccontextmanager
    async def initialize(self):
        """Initialize the Jira Helper context and tools."""
        # Create a dummy FastMCP server for lifespan management
        dummy_server = FastMCP("Jira Helper HTTP", lifespan=jira_lifespan)
        
        # Initialize the context using the lifespan manager
        async with jira_lifespan(dummy_server) as context:
            self.context = context
            self.tools = create_mcp_tools(context)
            logger.info("Jira Helper HTTP server initialized successfully")
            
            # Keep the context alive for the duration of the server
            yield
            
    async def health_check(self, request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "healthy",
            "service": "jira-helper-mcp",
            "version": "1.0.0",
            "transport": "http"
        })
        
    async def list_tools(self, request: Request) -> JSONResponse:
        """List available MCP tools."""
        if not self.tools:
            return JSONResponse({"error": "Server not initialized"}, status_code=500)
            
        tool_schemas = get_tool_schemas()
        tools_list = []
        
        for tool_name, schema in tool_schemas.items():
            tools_list.append({
                "name": tool_name,
                "description": schema["description"],
                "inputSchema": schema["inputSchema"]
            })
            
        return JSONResponse({
            "tools": tools_list,
            "count": len(tools_list)
        })
        
    async def call_tool(self, request: Request) -> JSONResponse:
        """Call a specific MCP tool."""
        if not self.tools:
            return JSONResponse({"error": "Server not initialized"}, status_code=500)
            
        try:
            # Get tool name from path
            tool_name = request.path_params.get("tool_name")
            if not tool_name:
                return JSONResponse({"error": "Tool name required"}, status_code=400)
                
            # Get tool function
            tool_func = self.tools.get(tool_name)
            if not tool_func:
                return JSONResponse({"error": f"Tool '{tool_name}' not found"}, status_code=404)
                
            # Parse request body for tool arguments
            body = await request.body()
            if body:
                try:
                    arguments = json.loads(body)
                except json.JSONDecodeError:
                    return JSONResponse({"error": "Invalid JSON in request body"}, status_code=400)
            else:
                arguments = {}
                
            # Call the tool function
            result = await tool_func(**arguments)
            
            return JSONResponse({
                "tool": tool_name,
                "result": result,
                "success": True
            })
            
        except TypeError as e:
            # Handle invalid arguments
            return JSONResponse({
                "error": f"Invalid arguments for tool '{tool_name}': {str(e)}",
                "success": False
            }, status_code=400)
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {str(e)}")
            return JSONResponse({
                "error": f"Tool execution failed: {str(e)}",
                "success": False
            }, status_code=500)
            
    async def get_tool_schema(self, request: Request) -> JSONResponse:
        """Get schema for a specific tool."""
        tool_name = request.path_params.get("tool_name")
        if not tool_name:
            return JSONResponse({"error": "Tool name required"}, status_code=400)
            
        tool_schemas = get_tool_schemas()
        schema = tool_schemas.get(tool_name)
        
        if not schema:
            return JSONResponse({"error": f"Tool '{tool_name}' not found"}, status_code=404)
            
        return JSONResponse({
            "tool": tool_name,
            "schema": schema
        })
        
    async def mcp_endpoint(self, request: Request) -> JSONResponse:
        """MCP protocol endpoint for Cline integration."""
        if not self.tools:
            return JSONResponse({"error": "Server not initialized"}, status_code=500)
            
        try:
            # Parse the MCP request
            body = await request.body()
            if not body:
                return JSONResponse({"error": "Request body required"}, status_code=400)
                
            try:
                mcp_request = json.loads(body)
            except json.JSONDecodeError:
                return JSONResponse({"error": "Invalid JSON in request body"}, status_code=400)
                
            # Handle different MCP methods
            method = mcp_request.get("method")
            params = mcp_request.get("params", {})
            request_id = mcp_request.get("id")
            
            if method == "tools/list":
                # List available tools
                tool_schemas = get_tool_schemas()
                tools_list = []
                
                for tool_name, schema in tool_schemas.items():
                    tools_list.append({
                        "name": tool_name,
                        "description": schema["description"],
                        "inputSchema": schema["inputSchema"]
                    })
                    
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools_list
                    }
                })
                
            elif method == "tools/call":
                # Call a specific tool
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if not tool_name:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Tool name required"
                        }
                    }, status_code=400)
                    
                tool_func = self.tools.get(tool_name)
                if not tool_func:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found"
                        }
                    }, status_code=404)
                    
                # Call the tool function
                try:
                    result = await tool_func(**arguments)
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    })
                except Exception as e:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution failed: {str(e)}"
                        }
                    }, status_code=500)
                    
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found"
                    }
                }, status_code=404)
                
        except Exception as e:
            logger.error(f"Error in MCP endpoint: {str(e)}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }, status_code=500)


# Global server instance
server_instance = JiraHelperHTTPServer()


# Lifespan manager for the Starlette app
@asynccontextmanager
async def lifespan(app):
    """Manage application lifespan."""
    async with server_instance.initialize():
        yield


# Define routes
routes = [
    Route("/health", server_instance.health_check, methods=["GET"]),
    Route("/tools", server_instance.list_tools, methods=["GET"]),
    Route("/tools/{tool_name}", server_instance.call_tool, methods=["POST"]),
    Route("/tools/{tool_name}/schema", server_instance.get_tool_schema, methods=["GET"]),
    Route("/mcp", server_instance.mcp_endpoint, methods=["POST"]),
]

# Middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# Create Starlette application
app = Starlette(
    debug=True,
    routes=routes,
    middleware=middleware,
    lifespan=lifespan
)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    logger.info(f"Starting Jira Helper HTTP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_server()
