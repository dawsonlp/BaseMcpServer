# MCP Tool Metadata Best Practices

## Critical Findings

Based on testing the MCP SDK, here are the key insights for tool metadata that will drive AI tool selection:

### Description Priority
```python
# SDK uses this priority:
description = explicit_description or function.__doc__ or ""
```

### Test Results Analysis

#### ❌ Problems with Function Docstrings Only
- **Full docstrings are verbose**: Multi-line docstrings with Args/Returns create cluttered tool descriptions
- **Empty descriptions**: Functions without docstrings get empty descriptions `""`
- **Inconsistent quality**: Some developers write good docstrings, others don't

#### ✅ Explicit Descriptions Work Better
- **Concise and focused**: "Create a new Jira ticket with project key and summary"
- **Consistent format**: All descriptions follow same pattern
- **AI-optimized**: Written specifically for AI tool selection, not human documentation

## Recommended Approach: Hybrid Strategy

### 1. Tool Definition with Explicit Descriptions
```python
# business/tool_definitions.py
from typing import Tuple, Callable
from .jira_operations import *

# Define tools with explicit AI-optimized descriptions
JIRA_TOOL_DEFINITIONS = [
    (list_projects, "list_jira_projects", 
     "List all available Jira projects, optionally filtered by instance name"),
    
    (get_issue_details, "get_issue_details",
     "Get comprehensive details about a specific Jira issue by its key"),
    
    (create_issue, "create_jira_ticket",
     "Create a new Jira issue with project key, summary, description, and optional fields"),
    
    (add_comment, "add_comment_to_jira_ticket",
     "Add a comment to an existing Jira issue, optionally visible to specific groups"),
    
    (transition_issue, "transition_jira_issue", 
     "Move a Jira issue through its workflow by applying a valid transition"),
    
    (search_issues, "search_jira_issues",
     "Execute a JQL (Jira Query Language) search to find issues matching criteria"),
    
    (validate_jql, "validate_jql_query",
     "Validate JQL syntax without executing the query, useful for testing searches"),
]
```

### 2. Smart Tool Registration Function
```python
# mcp/tool_registry.py
from mcp.server.fastmcp.tools import Tool
from typing import List, Tuple, Callable

def create_tools_with_metadata(
    tool_definitions: List[Tuple[Callable, str, str]], 
    context_kwarg: str = "context"
) -> List[Tool]:
    """
    Create Tool objects with proper metadata for AI tool selection.
    
    Args:
        tool_definitions: List of (function, name, description) tuples
        context_kwarg: Name of context parameter to inject
    
    Returns:
        List of properly configured Tool objects
    """
    tools = []
    
    for func, name, description in tool_definitions:
        tool = Tool.from_function(
            func,
            name=name,
            description=description,  # Explicit description overrides docstring
            context_kwarg=context_kwarg
        )
        tools.append(tool)
    
    return tools
```

### 3. Business Functions with Good Type Hints
```python
# business/jira_operations.py
from typing import Optional, List, Dict, Any

async def create_issue(
    context,
    project_key: str,
    summary: str, 
    description: str,
    issue_type: str = "Story",
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Jira issue with the specified details.
    
    This function creates an issue in the specified project with all the
    provided details and returns the created issue information.
    """
    return await context.create_issue_use_case.execute(
        project_key, summary, description, issue_type, 
        priority, assignee, labels, instance_name
    )
```

## Key Principles for AI-Optimized Descriptions

### 1. Be Specific and Actionable
```python
# ❌ Vague
"Get issue details"

# ✅ Specific  
"Get comprehensive details about a specific Jira issue by its key"
```

### 2. Include Key Parameters
```python
# ❌ Missing context
"Create a ticket"

# ✅ Clear parameters
"Create a new Jira issue with project key, summary, description, and optional fields"
```

### 3. Mention Important Constraints
```python
# ❌ No constraints mentioned
"Search for issues"

# ✅ Mentions JQL requirement
"Execute a JQL (Jira Query Language) search to find issues matching criteria"
```

### 4. Indicate When to Use
```python
# ❌ Unclear purpose
"Validate query"

# ✅ Clear use case
"Validate JQL syntax without executing the query, useful for testing searches"
```

## Parameter Schema Optimization

### Type Hints Drive Schema Generation
```python
# This function signature:
async def create_issue(
    context,
    project_key: str,           # Required string
    summary: str,               # Required string  
    description: str = "",      # Optional string with default
    priority: str = "Medium",   # Optional string with default
    assignee: Optional[str] = None  # Optional string, can be null
):

# Generates this schema:
{
  "properties": {
    "project_key": {"title": "Project Key", "type": "string"},
    "summary": {"title": "Summary", "type": "string"},
    "description": {"default": "", "title": "Description", "type": "string"},
    "priority": {"default": "Medium", "title": "Priority", "type": "string"},
    "assignee": {"default": null, "title": "Assignee", "type": "string"}
  },
  "required": ["project_key", "summary"],
  "type": "object"
}
```

### Best Practices for Parameters
1. **Use descriptive parameter names**: `project_key` not `key`
2. **Provide sensible defaults**: `priority: str = "Medium"`
3. **Use Optional[] for nullable**: `Optional[str] = None`
4. **Use List[] for arrays**: `labels: Optional[List[str]] = None`
5. **Use Union[] for multiple types**: `Union[str, int]` if needed

## Updated Server Factory Pattern

```python
# mcp/server_factory.py
from mcp.server.fastmcp import FastMCP
from business.tool_definitions import JIRA_TOOL_DEFINITIONS
from .tool_registry import create_tools_with_metadata

def create_jira_mcp_server(context) -> FastMCP:
    """Create Jira MCP server with optimized tool metadata"""
    
    # Convert tool definitions to Tool objects with proper metadata
    tools = create_tools_with_metadata(JIRA_TOOL_DEFINITIONS)
    
    # Create server with all tools
    return FastMCP("Jira Helper", tools=tools)
```

## Benefits of This Approach

### 1. AI-Optimized Tool Selection
- **Clear descriptions** help AI choose the right tool
- **Explicit parameters** reduce confusion about required inputs
- **Consistent format** makes tools predictable

### 2. Maintainable Metadata
- **Single source of truth** for tool descriptions
- **Easy to update** descriptions without changing business logic
- **Consistent quality** across all tools

### 3. Developer Friendly
- **Separation of concerns**: Business logic vs AI descriptions
- **Type safety**: Full type hints for IDE support
- **Easy testing**: Business functions are pure and testable

## Migration Strategy

### Phase 1: Extract Current Descriptions
```python
# Extract from current @mcp.tool() decorators
current_tools = [
    ("list_jira_projects", "List all projects available in the Jira instance"),
    ("create_jira_ticket", "Create a new Jira ticket (issue)"),
    # ... extract all current descriptions
]
```

### Phase 2: Optimize for AI
```python
# Rewrite descriptions for better AI tool selection
optimized_tools = [
    ("list_jira_projects", "List all available Jira projects, optionally filtered by instance name"),
    ("create_jira_ticket", "Create a new Jira issue with project key, summary, description, and optional priority/assignee"),
    # ... optimize all descriptions
]
```

### Phase 3: Add Missing Metadata
```python
# Add descriptions for tools that had empty docstrings
complete_tools = [
    # ... existing tools
    ("get_custom_field_mappings", "Get mappings between Jira custom field IDs and their human-readable names"),
    ("generate_project_workflow_graph", "Generate a visual workflow diagram for a specific project and issue type"),
]
```

This approach ensures that AI systems get the metadata they need to make intelligent tool selection decisions while keeping the code maintainable and the business logic clean.
