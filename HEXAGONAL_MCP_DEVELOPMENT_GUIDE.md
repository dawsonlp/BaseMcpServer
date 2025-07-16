# Hexagonal Architecture MCP Development Guide

## Executive Summary

After analyzing the current jira-helper implementation, I've discovered it already has an **excellent hexagonal architecture**. The issue isn't the architecture - it's that the MCP adapter layer has unnecessary complexity with decorators and duplicate tool registration. This guide shows how to simplify the MCP adapter while preserving the clean hexagonal separation.

## Current Architecture Analysis

### ✅ Excellent Hexagonal Structure (Keep This!)
```
servers/jira-helper/src/
├── domain/          # Pure business logic (entities, services, ports)
├── application/     # Use cases (orchestration layer)
├── infrastructure/  # External concerns (Jira API, config, graph generation)
└── adapters/        # Interface adapters (MCP, HTTP)
```

### ✅ Clean Separation Already Exists
- **Domain**: Pure business entities and rules (`models.py`, `services.py`, `ports.py`)
- **Application**: Use cases that orchestrate domain logic (`use_cases.py`)
- **Infrastructure**: Jira API clients, configuration, external services
- **Adapters**: MCP adapter, HTTP adapter (interface to external world)

### ❌ The Only Problem: MCP Adapter Complexity
The current MCP adapter has:
- **Repetitive decorators**: Each tool needs a `@mcp.tool()` decorator
- **Boilerplate wrapper functions**: Each decorator just calls `create_mcp_tools()`
- **Duplicate tool definitions**: Tools defined in both `mcp_adapter.py` and `mcp_tools.py`

## The Solution: Simplify MCP Adapter with Bulk Registration

### Keep Hexagonal Architecture, Simplify MCP Layer

#### Current Flow (Complex)
```
MCP Client Request
    ↓
@mcp.tool() decorator (15+ decorators)
    ↓
create_mcp_tools() wrapper
    ↓
Application Use Cases
    ↓
Domain Services
    ↓
Infrastructure (Jira API)
```

#### Target Flow (Simple)
```
MCP Client Request
    ↓
MCP Adapter (thin translation, bulk registered)
    ↓
Application Use Cases (unchanged)
    ↓
Domain Services (unchanged)
    ↓
Infrastructure (unchanged)
```

## Implementation Plan

### Phase 1: Create MCP Adapter Class (Thin Translation Layer)

#### 1.1 Create Simplified MCP Adapter
**File**: `servers/jira-helper/src/adapters/mcp_adapter_simplified.py`

```python
"""
Simplified MCP adapter that preserves hexagonal architecture.
This adapter is a thin translation layer between MCP protocol and application use cases.
"""

from typing import Any, Dict, Optional, List
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool

from application.use_cases import (
    ListProjectsUseCase, GetIssueDetailsUseCase, CreateIssueUseCase,
    # ... all other use cases
)
# ... other imports remain the same


class JiraMCPAdapter:
    """
    Thin MCP adapter that translates MCP tool calls to application use cases.
    This preserves hexagonal architecture by keeping the adapter as a pure translation layer.
    """
    
    def __init__(self, context: JiraHelperContext):
        self.context = context
    
    # MCP tool methods - these are just thin wrappers around use cases
    async def list_jira_projects(self, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """List all available Jira projects, optionally filtered by instance name."""
        result = await self.context.list_projects_use_case.execute(instance_name)
        return result.data if result.success else {
            "success": False, "error": result.error, "details": result.details
        }
    
    async def create_jira_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Story",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new Jira issue with project key, summary, description, and optional priority/assignee/labels."""
        result = await self.context.create_issue_use_case.execute(
            project_key, summary, description, issue_type, priority, assignee, labels, instance_name
        )
        return result.data if result.success else {
            "success": False, "error": result.error, "details": result.details
        }
    
    # ... all other tool methods follow the same pattern


# Tool definitions with AI-optimized metadata
JIRA_TOOL_DEFINITIONS = [
    (
        "list_jira_projects",
        "List all available Jira projects, optionally filtered by instance name"
    ),
    (
        "create_jira_ticket", 
        "Create a new Jira issue with project key, summary, description, and optional priority/assignee/labels"
    ),
    (
        "get_issue_details",
        "Get comprehensive details about a specific Jira issue by its key"
    ),
    # ... all other tools with AI-optimized descriptions
]


def create_jira_mcp_server_with_bulk_registration(context: JiraHelperContext) -> FastMCP:
    """
    Create Jira MCP server using bulk tool registration.
    This eliminates decorator boilerplate while preserving hexagonal architecture.
    """
    
    # Create adapter instance
    adapter = JiraMCPAdapter(context)
    
    # Create tools using bulk registration
    tools = []
    for tool_name, description in JIRA_TOOL_DEFINITIONS:
        # Get the adapter method
        adapter_method = getattr(adapter, tool_name)
        
        # Create Tool object with proper metadata
        tool = Tool.from_function(
            adapter_method,
            name=tool_name,
            description=description,
            context_kwarg=None  # Adapter already has context
        )
        tools.append(tool)
    
    # Create FastMCP server with all tools at once
    return FastMCP("Jira Helper", tools=tools, lifespan=jira_lifespan)


# Keep existing lifespan management (unchanged)
@asynccontextmanager
async def jira_lifespan(server: FastMCP) -> AsyncIterator[JiraHelperContext]:
    # ... existing lifespan code remains exactly the same
    pass
```

### Phase 2: Update Entry Points for Transport Selection

#### 2.1 Create Universal Entry Point
**File**: `servers/jira-helper/src/main_universal.py`

```python
"""
Universal entry point for Jira Helper MCP server.
Supports all transports via runtime selection while preserving hexagonal architecture.
"""

import sys
import asyncio
from adapters.mcp_adapter_simplified import create_jira_mcp_server_with_bulk_registration

def main():
    """Main entry point with runtime transport selection."""
    
    # Parse command line arguments
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    if transport not in ["stdio", "sse", "streamable-http"]:
        print(f"Error: Unknown transport '{transport}'")
        print("Usage: python main_universal.py [stdio|sse|streamable-http] [port]")
        sys.exit(1)
    
    # Run with lifespan context
    asyncio.run(run_with_context(transport, port))

async def run_with_context(transport: str, port: int):
    """Run server with proper context management."""
    
    # Create MCP server (lifespan handles context creation)
    mcp = create_jira_mcp_server_with_bulk_registration(None)  # Context created in lifespan
    
    # Configure transport-specific settings
    if transport in ["sse", "streamable-http"]:
        mcp.settings.port = port
    
    print(f"🚀 Starting Jira Helper MCP server with {transport} transport on port {port}")
    
    # Run with selected transport
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()
```

### Phase 3: Preserve Existing Architecture

#### 3.1 Keep All Existing Layers Unchanged
- ✅ **Domain layer**: No changes needed - already perfect
- ✅ **Application layer**: No changes needed - use cases are clean
- ✅ **Infrastructure layer**: No changes needed - external concerns handled well
- ✅ **Lifespan management**: Keep existing dependency injection

#### 3.2 Only Change: Simplify MCP Adapter
- ❌ **Remove**: Repetitive `@mcp.tool()` decorators
- ❌ **Remove**: Boilerplate wrapper functions
- ✅ **Add**: Bulk tool registration with proper metadata
- ✅ **Keep**: Thin translation layer pattern

## Benefits of This Approach

### 1. Preserves Hexagonal Architecture
- **Domain** remains pure business logic
- **Application** keeps use case orchestration
- **Infrastructure** handles external concerns
- **Adapters** become simpler translation layers

### 2. Eliminates MCP Complexity
- **90% reduction** in MCP adapter boilerplate
- **Single place** to define tool metadata
- **Bulk registration** eliminates decorator repetition
- **AI-optimized descriptions** for better tool selection

### 3. Maintains Clean Separation
```
MCP Protocol Concerns (Adapter)
    ↓
Business Orchestration (Application)
    ↓
Business Logic (Domain)
    ↓
External Systems (Infrastructure)
```

### 4. Runtime Transport Selection
```bash
# Same code, different transports
python main_universal.py stdio          # Development
python main_universal.py sse 8000       # Cline integration
python main_universal.py streamable-http 8000  # Other clients
```

## Implementation Checklist

### Phase 1: Create Simplified Adapter
- [ ] **Create** `adapters/mcp_adapter_simplified.py`
- [ ] **Implement** `JiraMCPAdapter` class with thin wrapper methods
- [ ] **Define** `JIRA_TOOL_DEFINITIONS` with AI-optimized descriptions
- [ ] **Implement** `create_jira_mcp_server_with_bulk_registration()`
- [ ] **Test** adapter methods call use cases correctly

### Phase 2: Universal Entry Point
- [ ] **Create** `main_universal.py` with transport selection
- [ ] **Test** all three transports work correctly
- [ ] **Verify** Cline compatibility with SSE transport
- [ ] **Update** Docker configuration for universal entry point

### Phase 3: Migration and Cleanup
- [ ] **Backup** existing `mcp_adapter.py`
- [ ] **Replace** with simplified version
- [ ] **Remove** old entry points (`streamable_main.py`, `http_main.py`)
- [ ] **Update** documentation and deployment scripts
- [ ] **Test** all existing functionality works

### Phase 4: Validation
- [ ] **Verify** hexagonal architecture preserved
- [ ] **Test** all use cases work through new adapter
- [ ] **Confirm** AI tool selection improved with better metadata
- [ ] **Validate** transport selection works correctly

## Tool Metadata Optimization

### AI-Optimized Descriptions
Following [MCP_TOOL_METADATA_BEST_PRACTICES.md](./MCP_TOOL_METADATA_BEST_PRACTICES.md):

```python
JIRA_TOOL_DEFINITIONS = [
    # ✅ Specific and actionable
    ("list_jira_projects", "List all available Jira projects, optionally filtered by instance name"),
    
    # ✅ Includes key parameters
    ("create_jira_ticket", "Create a new Jira issue with project key, summary, description, and optional priority/assignee/labels"),
    
    # ✅ Mentions important constraints
    ("search_jira_issues", "Execute a JQL (Jira Query Language) search to find issues matching criteria with pagination"),
    
    # ✅ Indicates when to use
    ("validate_jql_query", "Validate JQL syntax without executing the query, useful for testing searches"),
]
```

### Parameter Schema Generation
The adapter methods preserve type hints for automatic schema generation:

```python
async def create_jira_ticket(
    self,
    project_key: str,           # Required
    summary: str,               # Required
    description: str,           # Required
    issue_type: str = "Story",  # Optional with default
    priority: Optional[str] = None,  # Optional, nullable
    assignee: Optional[str] = None,  # Optional, nullable
    labels: Optional[List[str]] = None,  # Optional list
    instance_name: Optional[str] = None  # Optional, nullable
) -> Dict[str, Any]:
```

## Comparison: Before vs After

### Before (Complex)
```python
# 15+ repetitive decorators
@mcp.tool()
async def list_jira_projects(instance_name: Optional[str] = None):
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["list_jira_projects"](instance_name)

@mcp.tool()
async def create_jira_ticket(project_key: str, summary: str, ...):
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["create_jira_ticket"](project_key, summary, ...)

# ... 13+ more identical patterns
```

### After (Simple)
```python
# Single adapter class with bulk registration
class JiraMCPAdapter:
    def __init__(self, context):
        self.context = context
    
    async def list_jira_projects(self, instance_name: Optional[str] = None):
        result = await self.context.list_projects_use_case.execute(instance_name)
        return result.data if result.success else {"success": False, "error": result.error}
    
    async def create_jira_ticket(self, project_key: str, summary: str, ...):
        result = await self.context.create_issue_use_case.execute(project_key, summary, ...)
        return result.data if result.success else {"success": False, "error": result.error}

# Bulk registration eliminates all decorators
tools = [Tool.from_function(getattr(adapter, name), name=name, description=desc) 
         for name, desc in JIRA_TOOL_DEFINITIONS]
mcp = FastMCP("Jira Helper", tools=tools)
```

## Conclusion

The jira-helper already has **excellent hexagonal architecture** - we just need to simplify the MCP adapter layer. This approach:

- ✅ **Preserves** the clean domain/application/infrastructure separation
- ✅ **Simplifies** the MCP adapter to a thin translation layer
- ✅ **Eliminates** decorator boilerplate and duplication
- ✅ **Improves** AI tool selection with optimized metadata
- ✅ **Enables** runtime transport selection
- ✅ **Maintains** all existing functionality

The key insight is that **hexagonal architecture is about keeping business logic pure**, and the MCP adapter should be just another interface adapter - thin, focused, and separate from business concerns.
