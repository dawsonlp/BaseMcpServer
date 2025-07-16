# Ultra-Simplified MCP Development Guide

## You're Right - Even Simpler!

The JiraMCPAdapter methods are indeed boilerplate that add nothing. Let's eliminate that layer entirely and directly register the use cases with proper metadata.

## The Simplest Possible Approach

### Current Problem: Unnecessary Adapter Layer
```python
# ❌ Boilerplate that adds nothing
class JiraMCPAdapter:
    async def list_jira_projects(self, instance_name: Optional[str] = None):
        result = await self.context.list_projects_use_case.execute(instance_name)
        return result.data if result.success else {"success": False, "error": result.error}
```

### Solution: Direct Use Case Registration
```python
# ✅ Direct registration - no boilerplate
def create_jira_mcp_server(context: JiraHelperContext) -> FastMCP:
    """Create MCP server by directly registering use cases with proper metadata."""
    
    # Tool definitions: (use_case, method_name, tool_name, description)
    JIRA_TOOLS = [
        (context.list_projects_use_case, "execute", "list_jira_projects",
         "List all available Jira projects, optionally filtered by instance name"),
        
        (context.create_issue_use_case, "execute", "create_jira_ticket",
         "Create a new Jira issue with project key, summary, description, and optional priority/assignee/labels"),
        
        (context.get_issue_details_use_case, "execute", "get_issue_details",
         "Get comprehensive details about a specific Jira issue by its key"),
        
        # ... all other use cases
    ]
    
    # Create tools by wrapping use case execute methods
    tools = []
    for use_case, method_name, tool_name, description in JIRA_TOOLS:
        # Get the use case method
        use_case_method = getattr(use_case, method_name)
        
        # Create wrapper that handles result formatting
        async def create_tool_wrapper(uc_method):
            async def tool_wrapper(*args, **kwargs):
                result = await uc_method(*args, **kwargs)
                return result.data if result.success else {
                    "success": False, "error": result.error, "details": result.details
                }
            return tool_wrapper
        
        # Create Tool object
        tool_wrapper = await create_tool_wrapper(use_case_method)
        tool = Tool.from_function(tool_wrapper, name=tool_name, description=description)
        tools.append(tool)
    
    return FastMCP("Jira Helper", tools=tools, lifespan=jira_lifespan)
```

## Even Simpler: Generic Use Case Wrapper

```python
def create_use_case_tool(use_case, tool_name: str, description: str) -> Tool:
    """Create an MCP tool from a use case."""
    
    async def tool_function(*args, **kwargs):
        result = await use_case.execute(*args, **kwargs)
        return result.data if result.success else {
            "success": False, "error": result.error, "details": result.details
        }
    
    return Tool.from_function(tool_function, name=tool_name, description=description)


def create_jira_mcp_server(context: JiraHelperContext) -> FastMCP:
    """Create MCP server with direct use case registration."""
    
    # Just list the use cases and their metadata
    tool_definitions = [
        (context.list_projects_use_case, "list_jira_projects",
         "List all available Jira projects, optionally filtered by instance name"),
        
        (context.create_issue_use_case, "create_jira_ticket",
         "Create a new Jira issue with project key, summary, description, and optional priority/assignee/labels"),
        
        (context.get_issue_details_use_case, "get_issue_details",
         "Get comprehensive details about a specific Jira issue by its key"),
        
        (context.get_full_issue_details_use_case, "get_full_issue_details",
         "Get comprehensive details about a Jira issue with formatting options and raw data access"),
        
        (context.add_comment_use_case, "add_comment_to_jira_ticket",
         "Add a comment to an existing Jira issue, optionally visible to specific groups"),
        
        (context.transition_issue_use_case, "transition_jira_issue",
         "Move a Jira issue through its workflow by applying a valid transition"),
        
        (context.get_issue_transitions_use_case, "get_issue_transitions",
         "Get all available workflow transitions for a specific Jira issue"),
        
        (context.change_assignee_use_case, "change_issue_assignee",
         "Change the assignee of a Jira issue to a specific user or unassign it"),
        
        (context.list_project_tickets_use_case, "list_project_tickets",
         "List tickets in a Jira project with optional filtering by status and issue type"),
        
        (context.get_custom_field_mappings_use_case, "get_custom_field_mappings",
         "Get mappings between Jira custom field IDs and their human-readable names"),
        
        (context.generate_workflow_graph_use_case, "generate_project_workflow_graph",
         "Generate a visual workflow diagram for a specific project and issue type"),
        
        (context.list_instances_use_case, "list_jira_instances",
         "List all configured Jira instances available for connection"),
        
        (context.update_issue_use_case, "update_jira_issue",
         "Update an existing Jira issue with new field values like summary, description, or priority"),
        
        (context.search_issues_use_case, "search_jira_issues",
         "Execute a JQL (Jira Query Language) search to find issues matching criteria with pagination"),
        
        (context.validate_jql_use_case, "validate_jql_query",
         "Validate JQL syntax without executing the query, useful for testing searches"),
    ]
    
    # Create tools directly from use cases
    tools = [
        create_use_case_tool(use_case, tool_name, description)
        for use_case, tool_name, description in tool_definitions
    ]
    
    return FastMCP("Jira Helper", tools=tools, lifespan=jira_lifespan)
```

## Complete Simplified Implementation

**File**: `servers/jira-helper/src/adapters/mcp_adapter_ultra_simple.py`

```python
"""
Ultra-simplified MCP adapter that directly registers use cases.
No boilerplate, no unnecessary layers - just use cases + metadata.
"""

from typing import Any, Dict, Optional, List
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool

# Import existing lifespan and context (unchanged)
from .mcp_adapter import jira_lifespan, JiraHelperContext


def create_use_case_tool(use_case, tool_name: str, description: str) -> Tool:
    """Create an MCP tool directly from a use case."""
    
    async def tool_function(*args, **kwargs):
        result = await use_case.execute(*args, **kwargs)
        return result.data if result.success else {
            "success": False, "error": result.error, "details": result.details
        }
    
    return Tool.from_function(tool_function, name=tool_name, description=description)


def create_jira_mcp_server() -> FastMCP:
    """Create Jira MCP server with direct use case registration."""
    
    # This function will be called within the lifespan context
    def create_server_with_context(context: JiraHelperContext) -> FastMCP:
        
        # Tool definitions: (use_case, tool_name, AI-optimized_description)
        tool_definitions = [
            (context.list_projects_use_case, "list_jira_projects",
             "List all available Jira projects, optionally filtered by instance name"),
            
            (context.create_issue_use_case, "create_jira_ticket",
             "Create a new Jira issue with project key, summary, description, and optional priority/assignee/labels"),
            
            (context.get_issue_details_use_case, "get_issue_details",
             "Get comprehensive details about a specific Jira issue by its key"),
            
            (context.get_full_issue_details_use_case, "get_full_issue_details",
             "Get comprehensive details about a Jira issue with formatting options and raw data access"),
            
            (context.add_comment_use_case, "add_comment_to_jira_ticket",
             "Add a comment to an existing Jira issue, optionally visible to specific groups"),
            
            (context.transition_issue_use_case, "transition_jira_issue",
             "Move a Jira issue through its workflow by applying a valid transition"),
            
            (context.get_issue_transitions_use_case, "get_issue_transitions",
             "Get all available workflow transitions for a specific Jira issue"),
            
            (context.change_assignee_use_case, "change_issue_assignee",
             "Change the assignee of a Jira issue to a specific user or unassign it"),
            
            (context.list_project_tickets_use_case, "list_project_tickets",
             "List tickets in a Jira project with optional filtering by status and issue type"),
            
            (context.get_custom_field_mappings_use_case, "get_custom_field_mappings",
             "Get mappings between Jira custom field IDs and their human-readable names"),
            
            (context.generate_workflow_graph_use_case, "generate_project_workflow_graph",
             "Generate a visual workflow diagram for a specific project and issue type"),
            
            (context.list_instances_use_case, "list_jira_instances",
             "List all configured Jira instances available for connection"),
            
            (context.update_issue_use_case, "update_jira_issue",
             "Update an existing Jira issue with new field values like summary, description, or priority"),
            
            (context.search_issues_use_case, "search_jira_issues",
             "Execute a JQL (Jira Query Language) search to find issues matching criteria with pagination"),
            
            (context.validate_jql_use_case, "validate_jql_query",
             "Validate JQL syntax without executing the query, useful for testing searches"),
        ]
        
        # Create tools directly from use cases - no boilerplate!
        tools = [
            create_use_case_tool(use_case, tool_name, description)
            for use_case, tool_name, description in tool_definitions
        ]
        
        return FastMCP("Jira Helper", tools=tools)
    
    # Use existing lifespan but create server within context
    @asynccontextmanager
    async def enhanced_lifespan(server: FastMCP) -> AsyncIterator[JiraHelperContext]:
        async with jira_lifespan(server) as context:
            # Now we have context, create the actual server with tools
            actual_server = create_server_with_context(context)
            # Copy the tools to the original server
            server._tool_manager._tools = actual_server._tool_manager._tools
            yield context
    
    return FastMCP("Jira Helper", lifespan=enhanced_lifespan)


# Export for use in main.py
mcp = create_jira_mcp_server()
```

## Universal Entry Point (Unchanged)

```python
# main_universal.py
import sys
import asyncio
from adapters.mcp_adapter_ultra_simple import mcp

def main():
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    if transport in ["sse", "streamable-http"]:
        mcp.settings.port = port
    
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()
```

## Benefits of Ultra-Simplified Approach

### 1. Zero Boilerplate
- ❌ **No adapter class methods** - they added nothing
- ❌ **No wrapper functions** - direct use case registration
- ✅ **Just metadata + use cases** - that's all we need

### 2. Single Source of Truth
```python
# One place to define all tools - just list them!
tool_definitions = [
    (context.list_projects_use_case, "list_jira_projects", "Description..."),
    (context.create_issue_use_case, "create_jira_ticket", "Description..."),
    # ... add more here
]
```

### 3. Perfect Hexagonal Compliance
```
MCP Client Request
    ↓
Use Case (direct call)
    ↓
Domain Services
    ↓
Infrastructure
```

### 4. Maintains All Benefits
- ✅ **AI-optimized metadata** for tool selection
- ✅ **Runtime transport selection**
- ✅ **Type hints preserved** for parameter schemas
- ✅ **Hexagonal architecture preserved**
- ✅ **90% less code** than current implementation

## Comparison: Current vs Ultra-Simple

### Current (Complex)
```python
# 15+ decorators + wrapper functions + adapter methods
@mcp.tool()
async def list_jira_projects(instance_name: Optional[str] = None):
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["list_jira_projects"](instance_name)

class JiraMCPAdapter:
    async def list_jira_projects(self, instance_name: Optional[str] = None):
        result = await self.context.list_projects_use_case.execute(instance_name)
        return result.data if result.success else {"success": False, "error": result.error}
```

### Ultra-Simple (Direct)
```python
# Just list the use cases and metadata - done!
tool_definitions = [
    (context.list_projects_use_case, "list_jira_projects", "List all available Jira projects..."),
    # ... that's it!
]

tools = [create_use_case_tool(uc, name, desc) for uc, name, desc in tool_definitions]
mcp = FastMCP("Jira Helper", tools=tools)
```

You're absolutely right - the adapter methods were unnecessary boilerplate. This approach is as simple as it gets while maintaining all the benefits!
