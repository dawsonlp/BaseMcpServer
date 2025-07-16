# Adding New Features

## Quick Start

Adding new functionality follows the hexagonal architecture pattern. Here's the step-by-step process:

## 1. Add Domain Logic (if needed)

**Location**: `src/domain/`

```python
# src/domain/models.py - Add new data models
@dataclass
class NewFeatureRequest:
    param1: str
    param2: Optional[int] = None

# src/domain/services.py - Add business logic
class NewFeatureService(BaseService):
    async def process_feature(self, request: NewFeatureRequest) -> FeatureResult:
        # Business logic here
        pass
```

## 2. Create Use Case

**Location**: `src/application/use_cases.py`

```python
class NewFeatureUseCase(BaseUseCase):
    def __init__(self, feature_service: NewFeatureService):
        self._feature_service = feature_service
    
    async def execute(self, param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
        request = NewFeatureRequest(param1=param1, param2=param2)
        result = await self._feature_service.process_feature(request)
        return self._map_result(result)
```

## 3. Register MCP Tool

**Location**: `src/adapters/mcp_tool_config.py`

```python
JIRA_TOOLS = {
    # ... existing tools ...
    'new_feature_tool': {
        'use_case_class': NewFeatureUseCase,
        'description': 'Brief description of what this tool does',
        'dependencies': ['feature_service']  # Services this tool needs
    }
}
```

## 4. Add Infrastructure (if needed)

**Location**: `src/infrastructure/`

```python
# Only if you need new external API calls
class NewFeatureRepository:
    async def fetch_external_data(self, param: str) -> ExternalData:
        # API calls, database access, etc.
        pass
```

## 5. Update Service Registration

**Location**: `src/server.py`

```python
# Add to service setup
feature_repository = NewFeatureRepository(jira_client)
feature_service = NewFeatureService(feature_repository)
new_feature_use_case = NewFeatureUseCase(feature_service)

# Add to use case registry
use_cases = {
    # ... existing use cases ...
    'new_feature_tool': new_feature_use_case
}
```

## 6. Test Your Feature

```bash
# Deploy updated server
mcp-manager install local jira-helper --source servers/jira-helper --force

# Test the new tool
new_feature_tool param1="test" param2=42
```

## Common Patterns

### Simple CRUD Operations
Most tools follow this pattern:
1. **Domain Model** - Data structure
2. **Use Case** - Orchestration logic  
3. **Service** - Business rules
4. **Repository** - External API calls

### Search/Query Tools
Use the existing search patterns:
```python
# Extend SearchFilters for new filter types
# Use JQLBuilder for secure query construction
# Follow SearchService patterns
```

### Workflow Operations
For Jira workflow operations:
```python
# Use WorkflowService patterns
# Handle state transitions properly
# Include proper error handling
```

## File Locations

```
src/
├── domain/          # Business logic, models, services
├── application/     # Use cases, orchestration
├── infrastructure/  # External APIs, repositories
└── adapters/        # MCP tools, HTTP endpoints
```

## Testing

```python
# src/tests/test_use_cases.py
async def test_new_feature_use_case():
    mock_service = Mock()
    use_case = NewFeatureUseCase(mock_service)
    
    result = await use_case.execute("test", 42)
    
    assert result['success'] is True
    mock_service.process_feature.assert_called_once()
```

## Best Practices

1. **Follow Existing Patterns** - Look at similar tools for guidance
2. **Keep It Simple** - Start with minimal implementation
3. **Test Early** - Deploy and test frequently
4. **Security First** - Validate all inputs
5. **Error Handling** - Use consistent error patterns

## Need Help?

- Check existing tools in `mcp_tool_config.py` for examples
- Review the [Architecture Guide](../architecture/hexagonal-design.md)
- Look at similar use cases in `use_cases.py`

---

**Most features can be added in under 30 minutes following this pattern.**
