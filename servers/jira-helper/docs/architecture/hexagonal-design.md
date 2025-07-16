# Hexagonal Architecture Design

## Overview

The Jira Helper MCP Server implements a clean hexagonal architecture (also known as Ports and Adapters) that provides excellent separation of concerns, testability, and maintainability.

## Architecture Layers

### Core Domain (Center)
The business logic and domain models, completely independent of external concerns.

```
src/domain/
├── models.py          # Domain entities and value objects
├── services.py        # Domain services and business logic
├── base.py           # Base domain types and interfaces
├── base_service.py   # Abstract service patterns
└── jql_builder.py    # Domain-specific utilities
```

**Key Components:**
- **Domain Models**: Issue, Project, SearchResult, SearchFilters
- **Domain Services**: SearchService, IssueService, WorkflowService
- **Business Rules**: JQL validation, search filtering, security policies

### Application Layer
Orchestrates domain objects to fulfill use cases, contains no business logic.

```
src/application/
├── use_cases.py      # Application use cases
├── services.py       # Application services
└── base_use_case.py  # Base patterns for use cases
```

**Key Components:**
- **Use Cases**: ListProjectsUseCase, SearchIssuesUseCase, CreateIssueUseCase
- **Application Services**: Coordinate between domain and infrastructure
- **Result Mapping**: Transform domain objects to API responses

### Infrastructure Layer (Outer Ring)
Handles external concerns like databases, APIs, and frameworks.

```
src/infrastructure/
├── jira_api_repository.py      # Jira API integration
├── jira_client_factory.py      # HTTP client management
├── jira_time_tracking_adapter.py # Time tracking specifics
└── base_adapter.py             # Common adapter patterns
```

**Key Components:**
- **Repositories**: Data access and persistence
- **External APIs**: Jira REST API integration
- **Adapters**: Convert between external formats and domain models

### Adapters Layer
Translates between the application and external interfaces.

```
src/adapters/
├── mcp_adapter.py           # MCP protocol adapter
├── http_adapter.py          # HTTP/REST adapter
├── mcp_tool_config.py       # Tool configuration
├── mcp_bulk_registration.py # Bulk tool registration
└── mcp_result_adapter.py    # Result transformation
```

**Key Components:**
- **MCP Adapter**: Implements Model Context Protocol
- **HTTP Adapter**: RESTful API interface
- **Tool Configuration**: Metadata-driven tool registration

## Dependency Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   HTTP Client   │    │  Other Clients  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Adapters Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ MCP Adapter │  │HTTP Adapter │  │   Other Adapters        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Use Cases  │  │  Services   │  │   Result Mappers        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Domain Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Models    │  │  Services   │  │    Business Rules       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │Repositories │  │   Clients   │  │    External APIs        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Dependency Inversion
- High-level modules don't depend on low-level modules
- Both depend on abstractions (interfaces)
- Infrastructure depends on domain, not vice versa

### 2. Single Responsibility
- Each layer has one reason to change
- Domain: Business rules change
- Application: Use case requirements change
- Infrastructure: External system changes

### 3. Interface Segregation
- Small, focused interfaces
- Clients depend only on methods they use
- Easy to mock and test

### 4. Open/Closed Principle
- Open for extension, closed for modification
- New adapters can be added without changing core logic
- New use cases extend existing patterns

## Benefits Achieved

### 1. Testability
```python
# Domain logic can be tested in isolation
def test_search_filters_validation():
    filters = SearchFilters(project_key="PROJ", status="Invalid")
    assert not filters.is_valid()

# Use cases can be tested with mocked dependencies
def test_search_use_case():
    mock_service = Mock()
    use_case = SearchIssuesUseCase(search_service=mock_service)
    # Test without external dependencies
```

### 2. Flexibility
- Multiple adapters can coexist (MCP, HTTP, CLI)
- Easy to swap infrastructure components
- Business logic remains stable across changes

### 3. Maintainability
- Clear separation of concerns
- Easy to locate and modify specific functionality
- Reduced coupling between components

### 4. Security
- Input validation at adapter boundaries
- Business rules enforced in domain layer
- JQL injection prevention built into domain

## Implementation Patterns

### 1. Repository Pattern
```python
class JiraApiRepository:
    """Infrastructure layer - handles external API calls"""
    
    async def get_issue(self, issue_key: str) -> Issue:
        # External API integration
        pass

class IssueService:
    """Domain layer - business logic"""
    
    def __init__(self, repository: JiraApiRepository):
        self._repository = repository
    
    async def get_issue_with_validation(self, issue_key: str) -> Issue:
        # Business logic and validation
        pass
```

### 2. Use Case Pattern
```python
class GetIssueDetailsUseCase:
    """Application layer - orchestrates domain objects"""
    
    def __init__(self, issue_service: IssueService):
        self._issue_service = issue_service
    
    async def execute(self, issue_key: str) -> Dict[str, Any]:
        # Orchestrate domain services
        # Map results for presentation
        pass
```

### 3. Adapter Pattern
```python
class MCPAdapter:
    """Adapter layer - translates between MCP and application"""
    
    def __init__(self, use_cases: Dict[str, Any]):
        self._use_cases = use_cases
    
    async def handle_tool_call(self, name: str, args: Dict) -> Any:
        # Translate MCP calls to use case execution
        pass
```

## Configuration and Dependency Injection

### Service Registration
```python
# Infrastructure services
jira_client = JiraClientFactory.create(config)
jira_repository = JiraApiRepository(jira_client)

# Domain services
search_service = SearchService(jira_repository)
issue_service = IssueService(jira_repository)

# Application use cases
search_use_case = SearchIssuesUseCase(search_service)
issue_use_case = GetIssueDetailsUseCase(issue_service)

# Adapter configuration
mcp_adapter = MCPAdapter({
    'search_jira_issues': search_use_case,
    'get_issue_details': issue_use_case
})
```

### Tool Configuration
```python
# Metadata-driven tool registration
JIRA_TOOLS = {
    'search_jira_issues': {
        'use_case_class': SearchIssuesUseCase,
        'dependencies': ['search_service'],
        'description': 'Execute JQL search queries'
    }
}
```

## Error Handling Strategy

### 1. Domain Errors
- Business rule violations
- Validation failures
- Domain-specific exceptions

### 2. Application Errors
- Use case execution failures
- Orchestration errors
- Result mapping issues

### 3. Infrastructure Errors
- Network failures
- API rate limiting
- Authentication issues

### 4. Adapter Errors
- Protocol translation failures
- Input/output format errors
- Client communication issues

## Performance Considerations

### 1. Lazy Loading
- Services instantiated on demand
- Repository connections pooled
- Results cached appropriately

### 2. Async Operations
- Non-blocking I/O throughout
- Concurrent request handling
- Efficient resource utilization

### 3. Resource Management
- Connection pooling
- Request batching where possible
- Memory-efficient result streaming

## Testing Strategy

### 1. Unit Tests
- Domain logic in isolation
- Pure functions and business rules
- Fast, reliable, independent

### 2. Integration Tests
- Use cases with real dependencies
- Repository implementations
- End-to-end workflows

### 3. Contract Tests
- Adapter interfaces
- External API contracts
- Protocol compliance

## Future Extensions

### 1. New Adapters
- GraphQL adapter
- gRPC adapter
- WebSocket adapter

### 2. New Domains
- Confluence integration
- Bitbucket integration
- Generic Atlassian services

### 3. Enhanced Features
- Caching layer
- Event sourcing
- Audit logging

---

This hexagonal architecture provides a solid foundation for maintainable, testable, and extensible Jira integration while keeping business logic independent of external concerns.
