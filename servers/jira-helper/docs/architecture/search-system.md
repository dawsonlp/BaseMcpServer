# Search System Architecture

## Overview

The search system in Jira Helper implements a clean, secure, and efficient approach to Jira issue discovery. It consolidates multiple search patterns into a unified architecture that eliminates code duplication while providing both simple filtering and advanced JQL capabilities.

## Architecture Components

### 1. SearchFilters Model
A domain model for simple, structured searches.

```python
@dataclass
class SearchFilters:
    project_key: str
    status: Optional[str] = None
    issue_type: Optional[str] = None
    max_results: int = 50
    start_at: int = 0
    
    def is_valid(self) -> bool:
        """Validate filter parameters"""
        
    def to_jql(self) -> str:
        """Convert to JQL using JQLBuilder"""
```

**Purpose:**
- Type-safe filter parameters
- Built-in validation
- Easy to extend with new filter types

### 2. JQLBuilder Utility
A secure JQL query builder with fluent interface.

```python
class JQLBuilder:
    def project(self, project_key: str) -> 'JQLBuilder':
        """Add project filter with validation"""
        
    def status(self, status: str) -> 'JQLBuilder':
        """Add status filter with sanitization"""
        
    def issue_type(self, issue_type: str) -> 'JQLBuilder':
        """Add issue type filter"""
        
    def build(self) -> str:
        """Build final JQL query"""
```

**Security Features:**
- Input sanitization and validation
- JQL injection prevention
- Parameter escaping
- Whitelist-based validation

### 3. SearchService
Centralized search logic with composition-based design.

```python
class SearchService:
    def search_issues(self, query: SearchQuery, instance_name: Optional[str] = None) -> SearchResult:
        """Execute JQL search - core search method"""
        
    def search_with_filters(self, filters: SearchFilters, instance_name: Optional[str] = None) -> SearchResult:
        """Filter-based search - delegates to search_issues"""
        
    def validate_jql(self, jql: str, instance_name: Optional[str] = None) -> ValidationResult:
        """Validate JQL syntax without execution"""
```

**Design Pattern:**
- **Composition over Inheritance**: JQLBuilder as separate utility
- **Internal Delegation**: `search_with_filters()` → JQLBuilder → `search_issues()`
- **Single Responsibility**: Each method has focused purpose

## Search Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  Filter-Based   │    │   JQL-Based     │
│     Search      │    │     Search      │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       │
┌─────────────────┐              │
│  SearchFilters  │              │
│   Validation    │              │
└─────────────────┘              │
         │                       │
         ▼                       │
┌─────────────────┐              │
│   JQLBuilder    │              │
│  (Composition)  │              │
└─────────────────┘              │
         │                       │
         ▼                       ▼
┌─────────────────────────────────────┐
│         SearchService               │
│      search_issues()                │
│    (Core Implementation)            │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│      JiraApiRepository              │
│     (Infrastructure)                │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│         Jira REST API               │
└─────────────────────────────────────┘
```

## Use Case Integration

### ListProjectTicketsUseCase
Simple project-based searches with optional filters.

```python
class ListProjectTicketsUseCase(BaseQueryUseCase):
    async def execute(self, project_key: str, status: Optional[str] = None, 
                     issue_type: Optional[str] = None, max_results: int = 50,
                     instance_name: Optional[str] = None):
        
        # Create SearchFilters from parameters
        search_filters = SearchFilters(
            project_key=project_key,
            status=status,
            issue_type=issue_type,
            max_results=max_results
        )
        
        # Delegate to SearchService
        return await self.execute_query(
            lambda: self._search_service.search_with_filters(search_filters, instance_name),
            result_mapper,
            project_key=project_key,
            instance_name=instance_name
        )
```

### SearchIssuesUseCase
Advanced JQL-based searches.

```python
class SearchIssuesUseCase(BaseQueryUseCase):
    async def execute(self, jql: str, max_results: int = 50, 
                     start_at: int = 0, fields: Optional[List[str]] = None,
                     instance_name: Optional[str] = None):
        
        # Create SearchQuery from parameters
        search_query = SearchQuery(
            jql=jql,
            max_results=max_results,
            start_at=start_at,
            fields=fields
        )
        
        # Delegate to SearchService
        return await self.execute_query(
            lambda: self._search_service.search_issues(search_query, instance_name),
            result_mapper,
            jql=jql,
            instance_name=instance_name
        )
```

## Security Implementation

### 1. Input Validation
```python
def validate_project_key(project_key: str) -> bool:
    """Validate project key format"""
    if not project_key or not isinstance(project_key, str):
        return False
    
    # Project keys: alphanumeric, hyphens, underscores
    pattern = r'^[A-Z][A-Z0-9_-]*$'
    return bool(re.match(pattern, project_key.upper()))

def sanitize_jql_value(value: str) -> str:
    """Sanitize JQL field values"""
    # Escape special JQL characters
    special_chars = ['\\', '"', "'", '(', ')', '[', ']', '{', '}']
    for char in special_chars:
        value = value.replace(char, f'\\{char}')
    return value
```

### 2. JQL Injection Prevention
```python
class JQLBuilder:
    def _add_condition(self, field: str, operator: str, value: str) -> 'JQLBuilder':
        """Add condition with proper escaping"""
        # Validate field name against whitelist
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"Field '{field}' not allowed")
        
        # Sanitize value
        sanitized_value = sanitize_jql_value(value)
        
        # Build condition with proper quoting
        condition = f'{field} {operator} "{sanitized_value}"'
        self._conditions.append(condition)
        return self
```

### 3. Parameter Validation
```python
def validate_search_parameters(filters: SearchFilters) -> List[str]:
    """Validate all search parameters"""
    errors = []
    
    if not validate_project_key(filters.project_key):
        errors.append("Invalid project key format")
    
    if filters.status and filters.status not in VALID_STATUSES:
        errors.append(f"Invalid status: {filters.status}")
    
    if filters.max_results < 1 or filters.max_results > 1000:
        errors.append("max_results must be between 1 and 1000")
    
    return errors
```

## Performance Optimizations

### 1. Efficient JQL Generation
```python
class JQLBuilder:
    def build(self) -> str:
        """Build optimized JQL query"""
        if not self._conditions:
            return ""
        
        # Combine conditions efficiently
        jql = " AND ".join(self._conditions)
        
        # Add ORDER BY for consistent results
        if self._order_by:
            jql += f" ORDER BY {self._order_by}"
        
        return jql
```

### 2. Result Pagination
```python
class SearchResult:
    def has_more_results(self) -> bool:
        """Check if more results are available"""
        return self.start_at + len(self.issues) < self.total_results
    
    def next_page_start(self) -> int:
        """Calculate next page starting index"""
        return self.start_at + self.max_results
```

### 3. Field Selection
```python
def build_field_list(fields: Optional[List[str]] = None) -> str:
    """Build efficient field selection"""
    if not fields:
        # Default essential fields only
        fields = ['key', 'summary', 'status', 'assignee', 'updated']
    
    return ','.join(fields)
```

## Error Handling

### 1. Validation Errors
```python
class SearchValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error in {field}: {message}")
```

### 2. JQL Syntax Errors
```python
class JQLSyntaxError(Exception):
    def __init__(self, jql: str, error_details: str):
        self.jql = jql
        self.error_details = error_details
        super().__init__(f"JQL syntax error: {error_details}")
```

### 3. Search Execution Errors
```python
class SearchExecutionError(Exception):
    def __init__(self, query: str, cause: Exception):
        self.query = query
        self.cause = cause
        super().__init__(f"Search execution failed: {cause}")
```

## Testing Strategy

### 1. Unit Tests
```python
def test_search_filters_validation():
    """Test SearchFilters validation logic"""
    valid_filters = SearchFilters(project_key="PROJ", status="Open")
    assert valid_filters.is_valid()
    
    invalid_filters = SearchFilters(project_key="", status="Invalid")
    assert not invalid_filters.is_valid()

def test_jql_builder_security():
    """Test JQL injection prevention"""
    builder = JQLBuilder()
    malicious_input = "'; DROP TABLE issues; --"
    
    jql = builder.project("PROJ").status(malicious_input).build()
    assert "DROP TABLE" not in jql
    assert malicious_input in jql  # But properly escaped
```

### 2. Integration Tests
```python
async def test_search_service_integration():
    """Test SearchService with real dependencies"""
    search_service = SearchService(mock_repository)
    
    filters = SearchFilters(project_key="TEST", status="Open")
    result = await search_service.search_with_filters(filters)
    
    assert result.total_results >= 0
    assert all(issue.project_key == "TEST" for issue in result.issues)
```

### 3. Security Tests
```python
def test_jql_injection_prevention():
    """Test various JQL injection attempts"""
    injection_attempts = [
        "'; DROP TABLE issues; --",
        "' OR 1=1 --",
        "'; UNION SELECT * FROM users; --"
    ]
    
    for attempt in injection_attempts:
        builder = JQLBuilder()
        jql = builder.project("PROJ").status(attempt).build()
        
        # Verify injection is neutralized
        assert "DROP" not in jql.upper()
        assert "UNION" not in jql.upper()
        assert attempt not in jql  # Original not present
```

## Refactoring Benefits

### Before: Duplicate Code
- `IssueService.search_issues()` - 45 lines
- `SearchService.search_issues()` - Similar implementation
- Manual JQL construction in multiple places
- Inconsistent validation and error handling

### After: Consolidated Architecture
- Single `SearchService.search_issues()` implementation
- Reusable `JQLBuilder` utility
- Consistent `SearchFilters` validation
- Unified error handling and security

### Metrics
- **Code Reduction**: 45 lines eliminated
- **Security**: Centralized JQL injection prevention
- **Maintainability**: Single source of truth for search logic
- **Extensibility**: Easy to add new filter types

## Future Enhancements

### 1. Advanced Filtering
```python
class SearchFilters:
    assignee: Optional[str] = None
    priority: Optional[str] = None
    labels: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    updated_within: Optional[timedelta] = None
```

### 2. Search Result Caching
```python
class CachedSearchService:
    def __init__(self, search_service: SearchService, cache: Cache):
        self._search_service = search_service
        self._cache = cache
    
    async def search_issues(self, query: SearchQuery, instance_name: Optional[str] = None) -> SearchResult:
        cache_key = self._build_cache_key(query, instance_name)
        
        if cached_result := await self._cache.get(cache_key):
            return cached_result
        
        result = await self._search_service.search_issues(query, instance_name)
        await self._cache.set(cache_key, result, ttl=300)  # 5 minutes
        
        return result
```

### 3. Search Analytics
```python
class SearchAnalytics:
    def track_search(self, query: str, result_count: int, execution_time: float):
        """Track search performance and usage"""
        
    def get_popular_searches(self) -> List[str]:
        """Get most common search patterns"""
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get search performance statistics"""
```

---

This search system architecture provides a solid foundation for efficient, secure, and maintainable Jira issue discovery while eliminating code duplication and providing excellent extensibility.
