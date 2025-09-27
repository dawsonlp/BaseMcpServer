# MCP Result Adapter Architecture

## Overview

The MCP Result Adapter is a critical infrastructure component in the jira-helper server that solves a massive boilerplate problem. This single ~100-line file (`src/adapters/mcp_result_adapter.py`) **replaces over 500 lines of repetitive wrapper functions**, making it one of the highest-impact pieces of code in the system.

## The Problem

Without the MCP Result Adapter, every single use case would need an individual wrapper function to make it compatible with the MCP (Model Context Protocol) SDK. Here's what that would look like:

```python
# WITHOUT ADAPTER - You'd need this pattern for EVERY use case

async def list_projects_mcp_wrapper(instance_name: str):
    result = await list_projects_use_case.execute(instance_name)
    if result.success:
        return result.data
    else:
        return {"error": result.error, "details": result.details}

async def get_issue_details_mcp_wrapper(issue_key: str, instance_name: str):
    result = await get_issue_use_case.execute(issue_key, instance_name)
    if result.success:
        return result.data
    else:
        return {"error": result.error, "details": result.details}

async def create_issue_mcp_wrapper(project_key: str, summary: str, description: str, 
                                   issue_type: str, priority: str, assignee: str, 
                                   labels: list, custom_fields: dict, instance_name: str):
    result = await create_issue_use_case.execute(project_key, summary, description, 
                                                issue_type, priority, assignee, 
                                                labels, custom_fields, instance_name)
    if result.success:
        return result.data
    else:
        return {"error": result.error, "details": result.details}

# ... repeat this pattern for 20+ use cases = 500+ lines of boilerplate
```

**Problems with this approach:**
- **Massive code duplication**: Same transformation logic repeated dozens of times
- **Error-prone**: Easy to forget edge cases in individual wrappers
- **Maintenance nightmare**: Changes to error handling need to be applied everywhere
- **Inconsistent behavior**: Different wrappers might handle errors slightly differently

## The Solution

The `create_mcp_adapter()` function is a **higher-order function** that takes any use case method and returns an MCP-compatible version:

```python
def create_mcp_adapter(use_case_method: Callable) -> Callable:
    """
    Create an MCP-compatible adapter for a use case method.
    
    This SINGLE function replaces 500+ lines of boilerplate wrapper functions.
    """
```

### Usage Example

Instead of writing 20+ wrapper functions, you do this:

```python
# Create use case
list_projects_use_case = ListProjectsUseCase(project_service)

# Adapt it for MCP (one line!)
adapted_method = create_mcp_adapter(list_projects_use_case.execute)

# Register with MCP SDK
tool = Tool.from_function(adapted_method, name="list_projects")
```

## Technical Implementation

### 1. Function Signature Preservation

```python
sig = inspect.signature(use_case_method)
# ... later ...
mcp_adapted_method.__signature__ = sig
mcp_adapted_method.__name__ = use_case_method.__name__
mcp_adapted_method.__doc__ = use_case_method.__doc__
```

The adapter preserves the original method's signature so the MCP SDK knows exactly what parameters to expect. This enables proper type checking and parameter validation.

### 2. Result Transformation

```python
if isinstance(result, UseCaseResult):
    if result.success:
        return result.data  # MCP gets clean data directly
    else:
        return {
            "success": False,
            "error": result.error,
            "details": result.details
        }
```

The adapter automatically transforms `UseCaseResult` objects:
- **Success case**: Returns `result.data` directly (clean, typed data)
- **Failure case**: Returns standardized error format with context

### 3. Comprehensive Error Handling

```python
except Exception as e:
    logger.error(f"Error in MCP adapter for {use_case_method.__name__}: {str(e)}")
    return {
        "success": False,
        "error": f"Unexpected error: {str(e)}",
        "details": {"method": use_case_method.__name__, "kwargs": kwargs}
    }
```

All unexpected exceptions are caught and transformed into consistent error responses with debugging context.

### 4. Metadata Preservation

The adapter preserves function metadata required by the MCP SDK:
- Function name
- Documentation strings  
- Type annotations
- Parameter signatures

## Architectural Benefits

### 1. **DRY Principle Applied**
- **One definitive place** for MCP result transformation logic
- **500+ lines eliminated** from repetitive wrapper functions
- **Single source of truth** for error handling patterns

### 2. **Consistency Guaranteed**
- **All use cases** get identical MCP adaptation behavior
- **Standardized error responses** across all tools
- **Uniform logging** and debugging information

### 3. **Maintainability Enhanced**
- **Changes to MCP format** only need to be made in one place
- **Error handling improvements** apply to all tools automatically
- **Easier to test** comprehensive behavior with focused unit tests

### 4. **Type Safety Preserved**
- **Original signatures maintained** for proper MCP SDK integration
- **Parameter validation** works as expected
- **IDE support** remains fully functional

## Design Pattern: Higher-Order Function

This is a perfect example of the **higher-order function pattern**:

```python
# Input: Any use case execute method
use_case_method: Callable

# Output: MCP-compatible version of that method  
mcp_compatible_method: Callable

# The adapter is a function that takes a function and returns a function
adapter = create_mcp_adapter(original_function)
```

This pattern is especially powerful for:
- **Cross-cutting concerns** (like MCP compatibility)
- **Infrastructure-level transformations** 
- **Maintaining clean separation** between business logic and protocol adapters

## Testing Strategy

The MCP Result Adapter is **critical infrastructure** that affects every single MCP tool. This makes it essential to test thoroughly:

### Why Mocks Are Essential Here

```python
# From test_mcp_result_adapter.py
mock_use_case = AsyncMock(return_value=mock_result)
adapted_method = create_mcp_adapter(mock_use_case)
```

**Justification for mocking:**
1. **High Impact**: A bug here breaks every MCP tool
2. **Complex Logic**: Signature preservation, result transformation, error handling
3. **Infrastructure Testing**: Need to test adapter behavior, not business logic
4. **Edge Case Coverage**: Must test various UseCaseResult scenarios

### Test Coverage Areas

- ✅ **Successful result transformation**
- ✅ **Failed result transformation**  
- ✅ **Exception handling**
- ✅ **Metadata preservation**
- ✅ **Signature preservation**
- ✅ **Non-UseCaseResult handling**

## Integration with Clean Architecture

The MCP Result Adapter sits at the **infrastructure boundary** of the hexagonal architecture:

```
Domain Layer (Pure Business Logic)
    ↓
Application Layer (Use Cases) 
    ↓ 
MCP Result Adapter (Infrastructure Bridge)
    ↓
MCP SDK (External Framework)
```

**Key architectural role:**
- **Bridges** the application layer to MCP infrastructure
- **Preserves** clean separation between business logic and protocol
- **Enables** use cases to remain framework-agnostic
- **Provides** consistent external interface

## Performance Impact

### Before Adapter
- **500+ lines** of wrapper function code
- **Repeated compilation** of similar functions
- **Inconsistent error handling** performance

### With Adapter  
- **~100 lines** total for all MCP compatibility
- **Single function** handles all transformations
- **Consistent performance** characteristics across all tools

## Future Considerations

### Extending the Adapter

If MCP protocol changes require new transformation logic:

```python
# All changes happen in ONE place
def create_mcp_adapter(use_case_method: Callable) -> Callable:
    # Add new transformation logic here
    # Benefits ALL tools automatically
```

### Alternative Protocols

The same pattern could be applied to other protocols:

```python
graphql_adapter = create_graphql_adapter(use_case.execute)
rest_adapter = create_rest_adapter(use_case.execute)
grpc_adapter = create_grpc_adapter(use_case.execute)
```

## Summary

The MCP Result Adapter demonstrates **infrastructure code done right**:

- **Massive code reduction**: 500+ lines eliminated
- **Perfect DRY application**: One function, many beneficiaries  
- **Clean architecture preservation**: Business logic stays pure
- **Comprehensive testing**: Critical infrastructure must be reliable
- **Future-proof design**: Easy to extend and modify

This single file is a cornerstone of the jira-helper server's maintainability and represents excellent software engineering practices in action.
