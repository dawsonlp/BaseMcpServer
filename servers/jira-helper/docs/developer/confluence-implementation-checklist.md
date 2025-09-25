# Confluence Implementation Checklist

A step-by-step checklist for extending jira-helper with Confluence functionality using the established hexagonal architecture.

## Prerequisites
- [ ] Review `adding-use-cases.md` for general patterns
- [ ] Understand existing jira-helper architecture
- [ ] Have Confluence API documentation available
- [ ] Confluence instance access credentials configured

## Implementation Plan

### Basic Confluence Operations to Implement
- [ ] **List pages in a Confluence space**
- [ ] **Retrieve specific Confluence page content**
- [ ] **Search Confluence pages**
- [ ] **Get Confluence space information**
- [ ] **Create new Confluence page** (optional)
- [ ] **Update existing Confluence page** (optional)

---

## Step 1: Domain Models
**File: `src/domain/models.py`**

- [ ] Create `ConfluencePage` dataclass with fields:
  - [ ] `id: str`
  - [ ] `title: str` 
  - [ ] `space_key: str`
  - [ ] `content: Optional[str]`
  - [ ] `version: int`
  - [ ] `created_date: str`
  - [ ] `modified_date: str`
  - [ ] `author: str`
  - [ ] `url: str`

- [ ] Create `ConfluenceSpace` dataclass with fields:
  - [ ] `key: str`
  - [ ] `name: str`
  - [ ] `description: Optional[str]`
  - [ ] `homepage_id: str`
  - [ ] `type: str` (personal, global, etc.)

- [ ] Create `ConfluenceSearchResult` dataclass with fields:
  - [ ] `pages: List[ConfluencePage]`
  - [ ] `total_results: int`
  - [ ] `limit: int`
  - [ ] `start: int`

- [ ] Add `@validate_required_fields` decorators where appropriate
- [ ] Add any business logic methods needed

---

## Step 2: Domain Services
**File: `src/domain/services.py`**

- [ ] Create `ConfluenceService` class or add methods to existing service:
  - [ ] `validate_space_key(space_key: str) -> bool`
  - [ ] `validate_page_id(page_id: str) -> bool`
  - [ ] `format_page_content(raw_content: str) -> str`
  - [ ] `sanitize_search_query(query: str) -> str`

- [ ] Add business rule validation methods:
  - [ ] Check valid space access permissions
  - [ ] Validate page creation constraints
  - [ ] Handle content formatting rules

---

## Step 3: Infrastructure Layer
**File: `src/infrastructure/atlassian_confluence_adapter.py` (new file)**

- [ ] Create `ConfluenceRepository` class
- [ ] Implement HTTP client methods:
  - [ ] `get_spaces(instance_name: str) -> List[ConfluenceSpace]`
  - [ ] `get_space_pages(space_key: str, instance_name: str, limit: int = 50) -> List[ConfluencePage]`
  - [ ] `get_page_by_id(page_id: str, instance_name: str, expand: str = "body.storage") -> ConfluencePage`
  - [ ] `search_pages(query: str, space_key: Optional[str], instance_name: str) -> ConfluenceSearchResult`
  - [ ] `create_page(space_key: str, title: str, content: str, instance_name: str) -> ConfluencePage` (optional)
  - [ ] `update_page(page_id: str, title: str, content: str, version: int, instance_name: str) -> ConfluencePage` (optional)

- [ ] Add proper error handling for:
  - [ ] Invalid space keys
  - [ ] Page not found (404)
  - [ ] Permission denied (403)
  - [ ] API rate limiting
  - [ ] Network connectivity issues

- [ ] Map Confluence API responses to domain models
- [ ] Handle pagination for large result sets
- [ ] Add logging for debugging

---

## Step 4: Use Cases
**File: `src/application/use_cases.py`**

### Query Use Cases (Read Operations)
- [ ] **ListConfluenceSpacesUseCase** (extends `BaseQueryUseCase`):
  - [ ] Validate `instance_name` parameter
  - [ ] Call `confluence_repository.get_spaces()`
  - [ ] Map results using `map_spaces_result()`

- [ ] **ListConfluencePagesUseCase** (extends `BaseQueryUseCase`):
  - [ ] Validate `space_key` and `instance_name` parameters  
  - [ ] Optional `limit` parameter
  - [ ] Call `confluence_repository.get_space_pages()`
  - [ ] Map results using `map_pages_result()`

- [ ] **GetConfluencePageUseCase** (extends `BaseQueryUseCase`):
  - [ ] Validate `page_id` and `instance_name` parameters
  - [ ] Optional `expand` parameter for content inclusion
  - [ ] Call `confluence_repository.get_page_by_id()`
  - [ ] Map result using `map_page_result()`

- [ ] **SearchConfluencePagesUseCase** (extends `BaseQueryUseCase`):
  - [ ] Validate `query` and `instance_name` parameters
  - [ ] Optional `space_key` for space-limited search
  - [ ] Call `confluence_repository.search_pages()`
  - [ ] Map results using `map_search_result()`

### Command Use Cases (Write Operations) - Optional
- [ ] **CreateConfluencePageUseCase** (extends `BaseCommandUseCase`):
  - [ ] Validate `space_key`, `title`, `content`, `instance_name`
  - [ ] Business rule validation via domain service
  - [ ] Call `confluence_repository.create_page()`
  - [ ] Map result using `map_create_result()`

- [ ] **UpdateConfluencePageUseCase** (extends `BaseCommandUseCase`):
  - [ ] Validate `page_id`, `title`, `content`, `version`, `instance_name`
  - [ ] Version conflict handling
  - [ ] Call `confluence_repository.update_page()`
  - [ ] Map result using `map_update_result()`

### Result Mapper Functions
- [ ] Create mapper functions for each use case:
  - [ ] `map_spaces_result(spaces: List[ConfluenceSpace]) -> dict`
  - [ ] `map_pages_result(pages: List[ConfluencePage]) -> dict`
  - [ ] `map_page_result(page: ConfluencePage) -> dict`
  - [ ] `map_search_result(search_result: ConfluenceSearchResult) -> dict`

---

## Step 5: Tool Configuration  
**File: `src/adapters/mcp_tool_config.py`**

- [ ] Add entries to `JIRA_TOOLS` dictionary:

```python
"list_confluence_spaces": {
    "use_case_class": ListConfluenceSpacesUseCase,
    "description": "List all Confluence spaces available in the instance",
    "dependencies": ["confluence_repository"]
},
"list_confluence_pages": {
    "use_case_class": ListConfluencePagesUseCase, 
    "description": "List pages in a specific Confluence space",
    "dependencies": ["confluence_repository"]
},
"get_confluence_page": {
    "use_case_class": GetConfluencePageUseCase,
    "description": "Get detailed information about a specific Confluence page",
    "dependencies": ["confluence_repository"]  
},
"search_confluence_pages": {
    "use_case_class": SearchConfluencePagesUseCase,
    "description": "Search for Confluence pages using text query",
    "dependencies": ["confluence_repository"]
}
```

- [ ] Add optional command tools if implementing create/update:
  - [ ] `create_confluence_page`
  - [ ] `update_confluence_page`

---

## Step 6: Context Initialization
**File: `src/adapters/mcp_adapter.py`**

- [ ] Import new classes:
  - [ ] `from infrastructure.atlassian_confluence_adapter import ConfluenceRepository`
  - [ ] Import all new use case classes

- [ ] Update `JiraHelperContext` constructor:
  - [ ] Add `confluence_repository: ConfluenceRepository` parameter
  - [ ] Store as instance variable

- [ ] Update `jira_lifespan()` function:
  - [ ] Initialize `confluence_repository = ConfluenceRepository(http_client)`
  - [ ] Add confluence_repository to context initialization
  - [ ] Initialize all Confluence use cases with proper dependencies

**Example context update:**
```python
context = JiraHelperContext(
    # existing dependencies...
    confluence_repository=confluence_repository,
    # Confluence use cases
    list_confluence_spaces=ListConfluenceSpacesUseCase(confluence_repository),
    list_confluence_pages=ListConfluencePagesUseCase(confluence_repository),
    get_confluence_page=GetConfluencePageUseCase(confluence_repository),
    search_confluence_pages=SearchConfluencePagesUseCase(confluence_repository),
)
```

---

## Step 7: Testing
**File: `src/tests/test_confluence_use_cases.py` (new file)**

### Test Setup
- [ ] Create pytest fixtures:
  - [ ] `mock_confluence_repository`
  - [ ] `sample_confluence_space`
  - [ ] `sample_confluence_page`
  - [ ] `sample_confluence_search_result`

### Test Coverage for Each Use Case
- [ ] **ListConfluenceSpacesUseCase tests:**
  - [ ] Test successful space retrieval
  - [ ] Test empty space list
  - [ ] Test API error handling
  - [ ] Test invalid instance_name

- [ ] **ListConfluencePagesUseCase tests:**
  - [ ] Test successful page list retrieval
  - [ ] Test invalid space_key
  - [ ] Test empty page list
  - [ ] Test limit parameter handling

- [ ] **GetConfluencePageUseCase tests:**
  - [ ] Test successful page retrieval
  - [ ] Test page not found (404)
  - [ ] Test invalid page_id format
  - [ ] Test expand parameter handling

- [ ] **SearchConfluencePagesUseCase tests:**
  - [ ] Test successful search with results
  - [ ] Test search with no results
  - [ ] Test search with space filter
  - [ ] Test malformed query handling

### Integration Tests (Optional)
- [ ] Create `test_confluence_integration.py`:
  - [ ] Test actual Confluence API calls with real data
  - [ ] Test authentication and authorization
  - [ ] Test pagination handling

---

## Step 8: Code Review Checklist

### DRY (Don't Repeat Yourself)
- [ ] No duplicated validation logic between use cases
- [ ] Shared result mapping patterns follow existing conventions
- [ ] Common error handling consolidated in base classes
- [ ] HTTP client configuration reused from existing patterns

### KISS (Keep It Simple, Stupid)  
- [ ] Use case methods are single-purpose and focused
- [ ] Domain models contain only necessary fields
- [ ] API calls use straightforward HTTP patterns
- [ ] Error messages are clear and actionable

### Consistency
- [ ] Naming conventions match existing jira-helper patterns
- [ ] File structure follows established organization
- [ ] Test patterns match existing test files  
- [ ] Documentation follows project standards

### Architecture Compliance
- [ ] Domain logic separated from infrastructure concerns
- [ ] Use cases properly extend BaseQueryUseCase/BaseCommandUseCase
- [ ] Dependencies injected through constructor
- [ ] MCP tools automatically registered via metadata

### Functional Requirements
- [ ] All basic operations work as specified
- [ ] Error handling covers common failure scenarios
- [ ] Results format matches MCP tool expectations
- [ ] Performance acceptable for typical use cases

---

## Verification Steps

### Manual Testing
- [ ] Deploy updated jira-helper server
- [ ] Test each Confluence tool via MCP interface
- [ ] Verify error handling with invalid inputs
- [ ] Test with different Confluence instances

### Automated Testing  
- [ ] All unit tests pass: `python run_tests.py`
- [ ] Test coverage meets project standards
- [ ] Integration tests pass (if implemented)
- [ ] No regression in existing JIRA functionality

### Documentation
- [ ] Update `docs/user/available-tools.md` with new Confluence tools
- [ ] Add any special configuration requirements
- [ ] Document any limitations or known issues

---

## Success Criteria

Upon completion, the jira-helper should provide:
- ✅ **List Confluence spaces** - Users can see available spaces
- ✅ **Browse pages in spaces** - Users can list pages within a space  
- ✅ **Retrieve page content** - Users can get full page details and content
- ✅ **Search across Confluence** - Users can search for pages by text query
- ✅ **Error handling** - Clear error messages for common failure cases
- ✅ **Consistent patterns** - All tools follow established jira-helper conventions

## Estimated Implementation Time
- **Core functionality (Steps 1-6):** 4-6 hours
- **Testing (Step 7):** 2-3 hours  
- **Code review and refinement (Step 8):** 1-2 hours
- **Total:** 7-11 hours

This checklist ensures Confluence functionality integrates seamlessly with the existing jira-helper architecture while maintaining code quality and consistency.
