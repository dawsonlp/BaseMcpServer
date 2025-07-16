# MCP SDK Already Has Bulk Tool Registration!

## Discovery

The MCP SDK already provides exactly what you want - bulk tool registration through the FastMCP constructor!

## How It Works

### FastMCP Constructor
```python
FastMCP(
    name: str | None = None,
    instructions: str | None = None,
    tools: list[Tool] | None = None,  # <-- This is what we want!
    **settings: Any,
)
```

### Tool.from_function() Method
The SDK provides `Tool.from_function()` to convert regular functions into Tool objects:

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool

# Convert functions to Tool objects
tools = [
    Tool.from_function(list_projects, name="list_jira_projects"),
    Tool.from_function(create_issue, name="create_jira_ticket"),
    Tool.from_function(get_issue_details, name="get_issue_details"),
    # ... add as many as you want
]

# Create server with all tools at once
mcp = FastMCP("Jira Helper", tools=tools)
```

## Simple Usage Pattern

### 1. Define Your Business Functions
```python
# business/jira_operations.py
async def list_projects(context, instance_name: str = None):
    return await context.project_service.list_projects(instance_name)

async def create_issue(context, project_key: str, summary: str, description: str):
    return await context.issue_service.create_issue(project_key, summary, description)

async def get_issue_details(context, issue_key: str, instance_name: str = None):
    return await context.issue_service.get_issue_details(issue_key, instance_name)
```

### 2. Create Tool List
```python
# mcp/server_factory.py
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool
from business.jira_operations import *

def create_jira_mcp_server(context) -> FastMCP:
    """Create Jira MCP server with bulk tool registration"""
    
    # THE ONLY PLACE YOU LIST TOOLS - just functions and names
    tool_definitions = [
        (list_projects, "list_jira_projects"),
        (create_issue, "create_jira_ticket"), 
        (get_issue_details, "get_issue_details"),
        (add_comment, "add_comment_to_jira_ticket"),
        (transition_issue, "transition_jira_issue"),
        # ... just add more here
    ]
    
    # Convert to Tool objects
    tools = [
        Tool.from_function(func, name=name, context_kwarg="context")
        for func, name in tool_definitions
    ]
    
    # Create server with all tools at once
    return FastMCP("Jira Helper", tools=tools)
```

### 3. Even Simpler - Helper Function
```python
def create_tools_from_functions(function_list, context_kwarg="context"):
    """Convert list of (function, name) tuples to Tool objects"""
    return [
        Tool.from_function(func, name=name, context_kwarg=context_kwarg)
        for func, name in function_list
    ]

def create_jira_mcp_server(context) -> FastMCP:
    # Just list your functions and names
    jira_functions = [
        (list_projects, "list_jira_projects"),
        (create_issue, "create_jira_ticket"),
        (get_issue_details, "get_issue_details"),
        # ... add more here
    ]
    
    tools = create_tools_from_functions(jira_functions)
    return FastMCP("Jira Helper", tools=tools)
```

## Benefits

### 1. Zero Decorators
- No `@mcp.tool()` decorators needed
- No wrapper functions
- Just list your functions

### 2. Single Responsibility
- One place to list all tools: the `jira_functions` list
- Add a tool = add one line to the list

### 3. Clean Separation
- Business logic: Pure functions
- Tool registration: Simple list conversion
- MCP server: Bulk registration

### 4. Flexible Organization
```python
# Group by category
project_tools = [
    (list_projects, "list_jira_projects"),
    (create_project, "create_jira_project"),
]

issue_tools = [
    (create_issue, "create_jira_ticket"),
    (get_issue_details, "get_issue_details"),
    (update_issue, "update_jira_issue"),
]

# Combine all tools
all_tools = project_tools + issue_tools
tools = create_tools_from_functions(all_tools)
mcp = FastMCP("Jira Helper", tools=tools)
```

## Advanced Usage

### Custom Tool Configuration
```python
tools = [
    Tool.from_function(
        list_projects, 
        name="list_jira_projects",
        description="List all available Jira projects",
        context_kwarg="context"
    ),
    Tool.from_function(
        create_issue,
        name="create_jira_ticket", 
        description="Create a new Jira issue/ticket",
        context_kwarg="context"
    ),
]

mcp = FastMCP("Jira Helper", tools=tools)
```

### Mixed Sources
```python
# From different modules
from business.projects import list_projects, create_project
from business.issues import create_issue, get_issue_details
from business.workflows import transition_issue

tools = [
    Tool.from_function(list_projects, name="list_jira_projects"),
    Tool.from_function(create_project, name="create_jira_project"),
    Tool.from_function(create_issue, name="create_jira_ticket"),
    Tool.from_function(get_issue_details, name="get_issue_details"),
    Tool.from_function(transition_issue, name="transition_jira_issue"),
]

mcp = FastMCP("Jira Helper", tools=tools)
```

## Context Handling

The SDK automatically handles context injection:

```python
# Your function signature
async def list_projects(context, instance_name: str = None):
    # context is automatically injected
    return await context.project_service.list_projects(instance_name)

# Tool registration
Tool.from_function(list_projects, name="list_jira_projects", context_kwarg="context")
```

The `context_kwarg="context"` tells FastMCP to automatically inject the context as the first parameter.

## Conclusion

**The MCP SDK already provides exactly what you want!** 

- ✅ **Bulk tool registration** via `FastMCP(tools=tools)`
- ✅ **Simple function conversion** via `Tool.from_function()`
- ✅ **Automatic context injection** via `context_kwarg`
- ✅ **Zero boilerplate** - just list functions and names
- ✅ **Single responsibility** - one place to define all tools

No need to build custom registration - the SDK has it built-in!
