# Adding New Use Cases to Jira Helper

A concise guide for extending the jira-helper MCP server with new functionality.

## Quick Overview

The jira-helper uses hexagonal architecture with these layers:
- **Domain**: Business logic (`models.py`, `services.py`)
- **Application**: Use cases (`use_cases.py`) 
- **Infrastructure**: External APIs (`atlassian_*_adapter.py`)
- **Adapters**: MCP integration (`mcp_tool_config.py`, `mcp_adapter.py`)

## 8-Step Process

### 1. Domain Model (if needed)
Add to `src/domain/models.py`:
- Create dataclass with `@validate_required_fields` decorator
- Add business logic methods
- Create request/response models

### 2. Domain Service (if needed) 
Add to `src/domain/services.py`:
- Add method to appropriate service class
- Validate business rules
- Delegate to infrastructure

### 3. Infrastructure (if needed)
Add to `src/infrastructure/atlassian_repository.py`:
- Implement API calls
- Handle HTTP client logic
- Map API responses to domain models

### 4. Use Case
Add to `src/application/use_cases.py`:
- Extend `BaseQueryUseCase` (read) or `BaseCommandUseCase` (write)
- Use `self._validate_required_params()` for validation
- Use `execute_query()` or `execute_command()` patterns
- Create result mapper function

### 5. Tool Configuration
Add entry to `JIRA_TOOLS` in `src/adapters/mcp_tool_config.py`:
- Specify use case class, description, and dependencies
- Tool automatically becomes available via MCP

### 6. Context Initialization
Update `src/adapters/mcp_adapter.py`:
- Initialize use case with dependencies in `jira_lifespan()`
- Add to `JiraHelperContext` constructor

### 7. Tests
Create `src/tests/test_{feature}_use_cases.py`:
- Mock dependencies with `pytest.fixture`
- Test success and failure cases
- Use `@pytest.mark.asyncio` for async tests

### 8. Code Review
Review your implementation against core principles:
- **DRY**: No duplicated logic across layers or similar use cases
- **KISS**: Simple, readable code following established patterns
- **Consistency**: Matches existing naming and structure conventions
- **Single Responsibility**: Each class/method has one clear purpose

## Key Patterns

**Query Use Case** (read operations):
```python
class ListSomethingUseCase(BaseQueryUseCase):
    async def execute(self, param: str, instance_name: str):
        self._validate_required_params(param=param)
        return await self.execute_query(
            lambda: self._service.get_something(param, instance_name),
            result_mapper
        )
```

**Command Use Case** (write operations):
```python
class CreateSomethingUseCase(BaseCommandUseCase):
    async def execute(self, name: str, instance_name: str):
        self._validate_required_params(name=name)
        return await self.execute_command(
            create_operation,
            success_mapper
        )
```

## Files to Modify

Every new use case typically requires changes to:
1. `src/application/use_cases.py` (always)
2. `src/adapters/mcp_tool_config.py` (always)
3. `src/adapters/mcp_adapter.py` (always)
4. `src/domain/models.py` (if new entities needed)
5. `src/domain/services.py` (if new business logic needed)
6. `src/infrastructure/atlassian_repository.py` (if new API calls needed)
7. `src/tests/test_{feature}_use_cases.py` (always)

## Architecture Benefits

This approach achieves:
- **72% code reduction** through BaseUseCase patterns
- **300+ lines eliminated** via bulk MCP registration
- **Clean separation** of business logic from framework concerns
- **Easy testing** with dependency injection
- **Consistent patterns** across all features

## Learning from Examples

Study existing use cases for patterns:
- `ListProjectsUseCase` - Simple query
- `CreateIssueUseCase` - Command with validation  
- `SearchIssuesUseCase` - Complex query
- `TransitionIssueUseCase` - Business rule enforcement

The hexagonal architecture ensures new features follow the same reliable patterns while maintaining clean, testable code.
