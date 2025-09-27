# Jira Helper MCP-Commons Migration Plan

## Current State Analysis

### WorldContext (Target Pattern)
- **Simple main.py**: Uses `run_mcp_server()` and `create_mcp_app()` from mcp-commons
- **Clean tool_config.py**: Dictionary of functions with descriptions
- **Minimal dependencies**: mcp, mcp-commons, httpx, pydantic
- **Direct function calls**: No complex use case classes or dependency injection
- **Straightforward architecture**: Tools → Functions → Business Logic

### Jira Helper (Current Complex Implementation)  
- **Complex main.py**: Custom FastMCP server with lifespan management
- **Heavy architecture**: Hexagonal with domain/application/infrastructure layers
- **Complex tool registration**: Bulk registration with use case classes and dependencies
- **Many dependencies**: atlassian-python-api, graphviz, networkx, testing frameworks
- **Dependency injection**: Complex context object with many services

## Migration Strategy

**Goal**: Migrate jira-helper to use the same clean pattern as worldcontext while preserving all Jira functionality and the hexagonal architecture.

### Phase 1: Create Unified Tool Configuration
1. **Create new `tool_config.py`** following worldcontext pattern
2. **Expose all Jira functionality** through simple function interfaces
3. **Keep hexagonal architecture** but hide complexity behind function facades
4. **Maintain all existing features** (33+ Jira tools)

### Phase 2: Simplify Main Entry Point  
1. **Refactor main.py** to use `run_mcp_server()` from mcp-commons
2. **Remove complex FastMCP server** and lifespan management
3. **Use simple transport selection** like worldcontext
4. **Add help functionality** using `print_mcp_help()`

### Phase 3: Create Function Adapters
1. **Wrap existing use cases** in simple functions
2. **Initialize services once** at module level
3. **Expose clean interfaces** for MCP tool registration
4. **Maintain error handling** and logging

### Phase 4: Testing & Validation
1. **Ensure all tools work** with new architecture
2. **Validate error handling** remains robust
3. **Test both stdio and sse transports**
4. **Verify configuration management** still works

## Implementation Details

### New Architecture Pattern
```
main.py (simple)
├── run_mcp_server(tools_config=get_tools_config())
└── tool_config.py
    ├── JIRA_TOOLS = {...}  # Simple dictionary
    ├── get_tools_config() → returns JIRA_TOOLS
    └── Helper functions that wrap use cases
        ├── list_jira_projects(instance_name) 
        ├── get_issue_details(issue_key, instance_name)
        ├── create_jira_ticket(...)
        └── ... (33+ functions)
```

### Service Initialization
- Initialize all services **once at module level** in tool_config.py
- Services remain the same (hexagonal architecture preserved)
- Functions act as thin wrappers around use cases

### Benefits
1. **Consistency**: Same pattern as worldcontext
2. **Simplicity**: Easier to understand and maintain
3. **Functionality**: All existing features preserved
4. **Architecture**: Hexagonal design remains intact
5. **Standards**: Follows mcp-commons best practices

## Migration Steps

1. **Create new tool_config.py** with function wrappers
2. **Initialize services at module level** 
3. **Implement wrapper functions** for all 33+ tools
4. **Simplify main.py** to match worldcontext pattern
5. **Remove complex mcp_adapter.py** and bulk registration
6. **Test all functionality** works as before
7. **Update documentation** to reflect simpler architecture

## Compatibility
- **Config files**: No changes needed
- **Tool interfaces**: Remain exactly the same
- **Dependencies**: Keep existing (atlassian-python-api, graphviz, etc.)
- **Functionality**: 100% preserved
- **Performance**: Should improve (less complexity)

This migration will result in a much cleaner, more maintainable codebase while preserving all the sophisticated Jira functionality.
