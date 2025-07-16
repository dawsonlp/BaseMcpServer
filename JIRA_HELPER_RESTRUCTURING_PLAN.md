# Jira Helper Restructuring Plan

## Executive Summary

Based on our discovery that the MCP SDK already has built-in bulk tool registration, we can dramatically simplify the jira-helper architecture by leveraging `FastMCP(tools=tools)` and `Tool.from_function()`.

## Current vs Target Architecture

### Current (Complex)
```
Multiple Entry Points:
├── src/main.py (stdio)
├── src/streamable_main.py (streamable-http) 
├── src/http_main.py (custom HTTP)
└── Complex dual adapter system

Each with:
├── Separate MCP decorators (@mcp.tool())
├── Wrapper functions for each tool
└── Duplicated registration logic
```

### Target (Simple)
```
Single Entry Point:
└── src/main.py (runtime transport selection)

With:
├── Pure business functions
├── Simple tool list
└── Bulk registration via FastMCP(tools=tools)
```

## Implementation Plan

### Phase 1: Extract Business Logic

#### 1.1 Create Pure Business Functions
**New File**: `src/business/jira_operations.py`

```python
# Pure functions - no MCP dependencies
async def list_projects(context, instance_name: str = None):
    return await context.list_projects_use_case.execute(instance_name)

async def create_issue(context, project_key: str, summary: str, description: str, **kwargs):
    return await context.create_issue_use_case.execute(project_key, summary, description, **kwargs)

async def get_issue_details(context, issue_key: str, instance_name: str = None):
    return await context.get_issue_details_use_case.execute(issue_key, instance_name)

# ... extract all other business functions
```

#### 1.2 Extract from Current MCP Decorators
- Remove MCP decorators from current `mcp_adapter.py`
- Convert each `@mcp.tool()` function to pure business function
- Move to `business/jira_operations.py`

### Phase 2: Create Server Factory

#### 2.1 New Server Factory
**New File**: `src/mcp/server_factory.py`

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool
from business.jira_operations import *

def create_tools_from_functions(function_list, context_kwarg="context"):
    """Convert function list to Tool objects"""
    return [
        Tool.from_function(func, name=name, context_kwarg=context_kwarg)
        for func, name in function_list
    ]

def create_jira_mcp_server(context) -> FastMCP:
    """Create Jira MCP server with bulk tool registration"""
    
    # THE ONLY PLACE TO LIST ALL TOOLS
    jira_tools = [
        (list_projects, "list_jira_projects"),
        (get_issue_details, "get_issue_details"),
        (get_full_issue_details, "get_full_issue_details"),
        (create_issue, "create_jira_ticket"),
        (add_comment, "add_comment_to_jira_ticket"),
        (transition_issue, "transition_jira_issue"),
        (get_issue_transitions, "get_issue_transitions"),
        (change_assignee, "change_issue_assignee"),
        (list_project_tickets, "list_project_tickets"),
        (get_custom_field_mappings, "get_custom_field_mappings"),
        (generate_workflow_graph, "generate_project_workflow_graph"),
        (list_instances, "list_jira_instances"),
        (update_issue, "update_jira_issue"),
        (search_issues, "search_jira_issues"),
        (validate_jql, "validate_jql_query"),
        # ... add all other tools here
    ]
    
    # Convert to Tool objects and create server
    tools = create_tools_from_functions(jira_tools)
    return FastMCP("Jira Helper", tools=tools)
```

#### 2.2 Lifespan Management
**New File**: `src/mcp/lifespan.py`

```python
from contextlib import asynccontextmanager
from adapters.mcp_adapter import JiraHelperContext, jira_lifespan

@asynccontextmanager
async def create_jira_context():
    """Create Jira context with all dependencies"""
    # Move existing lifespan logic here
    async with jira_lifespan(None) as context:
        yield context
```

### Phase 3: Single Entry Point

#### 3.1 Replace Multiple Entry Points
**Replace**: `main.py`, `streamable_main.py`, `http_main.py`
**With**: Single `main.py`

```python
#!/usr/bin/env python3
"""
Universal entry point for Jira Helper MCP server.
Supports all transports via runtime selection.
"""

import sys
import asyncio
from contextlib import asynccontextmanager
from mcp.server_factory import create_jira_mcp_server
from mcp.lifespan import create_jira_context

def main():
    """Main entry point with runtime transport selection"""
    
    # Parse command line arguments
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    if transport not in ["stdio", "sse", "streamable-http"]:
        print(f"Error: Unknown transport '{transport}'")
        print("Usage: python main.py [stdio|sse|streamable-http] [port]")
        sys.exit(1)
    
    # Run with lifespan context
    asyncio.run(run_with_context(transport, port))

async def run_with_context(transport: str, port: int):
    """Run server with proper context management"""
    
    async with create_jira_context() as context:
        # Create MCP server with all tools
        mcp = create_jira_mcp_server(context)
        
        # Configure transport-specific settings
        if transport in ["sse", "streamable-http"]:
            mcp.settings.port = port
        
        # Run with selected transport
        mcp.run(transport=transport)

if __name__ == "__main__":
    main()
```

#### 3.2 Usage Examples
```bash
# Local development
python main.py stdio

# Cline integration
python main.py sse 8000

# Other MCP clients (when fixed)
python main.py streamable-http 8000
```

### Phase 4: Simplify Deployment

#### 4.1 Remove Unnecessary Files
**Delete**:
- `src/streamable_main.py`
- `src/http_main.py`
- `src/adapters/http_adapter.py`
- `docker-compose.http.yml`
- `Dockerfile.http`

#### 4.2 Update Docker Configuration
**New**: `Dockerfile`
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config.yaml.example ./config.yaml

# Default to SSE transport for Cline compatibility
CMD ["python", "src/main.py", "sse", "8000"]
```

**New**: `docker-compose.yml`
```yaml
services:
  jira-helper:
    build: .
    ports:
      - "8000:8000"
    environment:
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
    volumes:
      - ./config.yaml:/app/config.yaml
```

#### 4.3 Deployment Scripts
**New**: `deploy/stdio.sh`
```bash
#!/bin/bash
python src/main.py stdio
```

**New**: `deploy/sse.sh`
```bash
#!/bin/bash
python src/main.py sse ${PORT:-8000}
```

### Phase 5: Update Documentation

#### 5.1 Update README.md
```markdown
# Jira Helper MCP Server

## Quick Start

### Local Development (STDIO)
```bash
python src/main.py stdio
```

### Cline Integration (SSE)
```bash
python src/main.py sse 8000
```

### Docker Deployment
```bash
docker compose up
```

## Transport Options
- `stdio`: Local development, traditional MCP clients
- `sse`: Cline integration, remote HTTP (recommended)
- `streamable-http`: Other MCP clients (currently broken in Cline)
```

#### 5.2 Migration Guide
**New**: `MIGRATION_GUIDE.md`
- Document changes from old architecture
- Provide upgrade instructions
- List breaking changes (if any)

## Benefits of This Restructuring

### Code Reduction
- **90% fewer lines** in MCP adapter layer
- **Single entry point** instead of 3
- **No duplicate tool registration**
- **No custom HTTP adapter complexity**

### Maintainability
- **One place to add tools**: Just add to the list in `server_factory.py`
- **Pure business logic**: Easy to test independently
- **Clear separation**: Business logic vs MCP protocol vs transport

### Flexibility
- **Runtime transport selection**: Same code, different deployment
- **Easy testing**: Test business logic without MCP overhead
- **Future-proof**: Easy to add new transports when available

## Implementation Timeline

### Week 1: Business Logic Extraction
- [ ] Create `business/jira_operations.py`
- [ ] Extract all functions from current MCP decorators
- [ ] Test business logic independently

### Week 2: Server Factory
- [ ] Create `mcp/server_factory.py`
- [ ] Implement bulk tool registration
- [ ] Test with all transports

### Week 3: Single Entry Point
- [ ] Create new `main.py`
- [ ] Test transport selection
- [ ] Verify Cline compatibility

### Week 4: Cleanup and Documentation
- [ ] Remove old files
- [ ] Update Docker configuration
- [ ] Update documentation
- [ ] Create migration guide

## Risk Mitigation

### Backward Compatibility
- Keep old entry points during transition
- Gradual migration with feature flags
- Comprehensive testing

### Testing Strategy
- Unit tests for business logic
- Integration tests for MCP tools
- End-to-end tests with all transports
- Cline compatibility verification

## Success Metrics

### Code Quality
- [ ] Reduce MCP adapter from 500+ lines to <100 lines
- [ ] Single entry point for all transports
- [ ] 100% business logic test coverage

### Functionality
- [ ] All existing tools work with new architecture
- [ ] All three transports work correctly
- [ ] Cline integration works with SSE transport

### Maintainability
- [ ] Adding new tool requires only 1 line change
- [ ] Clear separation of concerns
- [ ] Simplified deployment process

This restructuring will transform the jira-helper from a complex multi-adapter system into a clean, maintainable MCP server that follows SDK best practices and dramatically reduces complexity.
