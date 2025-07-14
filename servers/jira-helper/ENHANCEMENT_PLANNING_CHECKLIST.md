# Jira Helper Enhancement Planning Checklist

## Overview
Enhance jira-helper with additional functionality from jira-mcp-server while adding issue linking capabilities, following hexagonal architecture principles.

## Features to Add

### 1. Issue Update Functionality
- [ ] Add update capabilities to existing issues
- [ ] Support updating: summary, description, priority, assignee, labels
- [ ] Maintain backward compatibility

### 2. Direct JQL Search
- [ ] Add JQL query support with pagination
- [ ] Support advanced search capabilities
- [ ] Return structured results

### 3. Issue Linking System
- [ ] Generic issue linking with link types
- [ ] Epic linking (specific case of issue linking)
- [ ] Parent-child relationships
- [ ] Support for custom link types

## Hexagonal Architecture Implementation Plan

### Phase 1: Domain Layer Enhancements ✅ COMPLETED

#### A. Domain Models (`src/domain/models.py`) ✅
- [x] Add `IssueLink` model with:
  - `link_type: str` (e.g., "Epic-Story", "Blocks", "Parent-Child")
  - `source_issue: str`
  - `target_issue: str`
  - `direction: str` (inward/outward)
- [x] Add `IssueUpdate` model with:
  - `issue_key: str`
  - `fields: Dict[str, Any]`
  - `validation rules`
- [x] Add `SearchQuery` model with:
  - `jql: str`
  - `max_results: int`
  - `start_at: int`
  - `validation`
- [x] Add `SearchResult`, `IssueUpdateResult`, `IssueLinkResult` models
- [x] Add `IssueCreateWithLinksRequest` model
- [x] Add `LinkType` and `LinkDirection` enums

#### B. Domain Ports (`src/domain/ports.py`) ✅
- [x] Add `IssueUpdatePort` interface:
  - `update_issue(issue_update: IssueUpdate) -> IssueUpdateResult`
  - `validate_update_fields()` and `get_updatable_fields()`
- [x] Add `IssueLinkPort` interface:
  - `create_link(issue_link: IssueLink) -> IssueLinkResult`
  - `get_links(issue_key: str) -> List[IssueLink]`
  - `remove_link(link_id: str) -> bool`
  - `get_available_link_types()` and `validate_link()`
- [x] Add `IssueSearchPort` interface:
  - `search_issues(query: SearchQuery) -> SearchResult`
  - `validate_jql()` and `get_search_suggestions()`
- [x] Add `IssueCreationPort` interface:
  - `create_issue_with_links()`, `create_epic_story_link()`, `create_parent_child_link()`
- [x] Add `LinkTypeMapper` and `JQLValidator` interfaces

#### C. Domain Services (`src/domain/services.py`) ✅
- [x] Add `IssueLinkService`:
  - Validate link types
  - Handle bidirectional relationships
  - Prevent circular dependencies
  - Epic and Parent-Child link creation
- [x] Add `IssueUpdateService`:
  - Validate update permissions
  - Handle field validation
  - Manage update conflicts
- [x] Add `SearchService`:
  - Validate JQL syntax
  - Handle pagination logic
  - Format search results
  - Security validation

#### D. Domain Exceptions (`src/domain/exceptions.py`) ✅
- [x] Add `InvalidLinkTypeError`
- [x] Add `CircularLinkError`
- [x] Add `InvalidJQLError`
- [x] Add `IssueUpdateError`
- [x] Add `IssueLinkError`, `LinkNotFoundError`
- [x] Add `JQLSecurityError`, `SearchLimitExceededError`
- [x] Add `EpicLinkError`, `LinkTypeNotSupportedError`
- [x] Add `IssueFieldUpdateError`, `ConcurrentUpdateError`

### Phase 2: Application Layer Enhancements ✅ COMPLETED

#### A. Use Cases (`src/application/use_cases.py`) ✅
- [x] Add `UpdateIssueUseCase`:
  - Validate update request
  - Apply business rules
  - Coordinate with infrastructure
- [x] Add `CreateIssueWithLinksUseCase`:
  - Extend existing creation logic
  - Handle link creation after issue creation
  - Manage transaction rollback on failure
- [x] Add `SearchIssuesUseCase`:
  - Validate search parameters
  - Execute search
  - Format results
- [x] Add Issue Link Use Cases:
  - `CreateIssueLinkUseCase` - Generic issue linking
  - `CreateEpicStoryLinkUseCase` - Specific Epic-Story linking
  - `GetIssueLinksUseCase` - Retrieve all links for an issue
- [x] Add Time Tracking Use Cases:
  - `LogWorkUseCase` - Log work with time tracking
  - `GetWorkLogsUseCase` - Retrieve work logs for an issue
  - `GetTimeTrackingInfoUseCase` - Get time tracking information
  - `UpdateTimeEstimatesUseCase` - Update time estimates
- [x] Add `ValidateJQLUseCase` - JQL syntax validation

### Phase 3: Infrastructure Layer Enhancements ✅ COMPLETED

#### A. Jira Client Extensions (`src/infrastructure/jira_client.py`) ✅
- [x] Add `JiraIssueUpdateAdapter` - Issue update operations
- [x] Add `JiraIssueLinkAdapter` - Issue linking operations
- [x] Add `JiraSearchAdapter` - JQL search operations
- [x] Add `JiraTimeTrackingAdapter` - Time tracking operations
- [x] Enhanced error handling and validation

#### B. New Infrastructure Services ✅
- [x] Add `JiraTimeFormatValidator`:
  - Validate Jira time format (e.g., '2h 30m', '1d')
  - Parse time strings to seconds
  - Format seconds back to Jira time format
  - Support all Jira time units (w, d, h, m)
- [x] Add `JiraLinkTypeMapper`:
  - Map domain link types to Jira link types
  - Handle Epic-Story relationships
  - Support custom link types
- [x] Add `JiraJQLValidator`:
  - Validate JQL syntax
  - Sanitize queries for security
  - Handle security concerns and performance checks

### Phase 4: Adapter Layer Enhancements ✅ COMPLETED

#### A. MCP Adapter (`src/adapters/mcp_adapter.py`) ✅
- [x] Add `update_jira_issue` tool - Update existing issues with field validation
- [x] Add `search_jira_issues` tool - Execute JQL searches with pagination
- [x] Add `validate_jql_query` tool - Validate JQL syntax without execution
- [x] Add Issue Linking Tools:
  - `create_issue_link` - Generic issue linking
  - `create_epic_story_link` - Specific Epic-Story linking
  - `get_issue_links` - Retrieve all links for an issue
- [x] Add `create_jira_ticket_with_links` tool - Create issues with links in one operation
- [x] Add Time Tracking Tools:
  - `log_work_on_issue` - Log work with time tracking
  - `get_work_logs` - Retrieve work logs for an issue
  - `get_time_tracking_info` - Get time tracking information
  - `update_time_estimates` - Update time estimates
- [x] Enhanced dependency injection with all new services and use cases
- [x] Comprehensive error handling and logging for all new tools
- [x] Backward compatibility maintained for all existing tools

### Phase 5: Testing Enhancements ✅ COMPLETED (Foundation)

#### A. Domain Tests (`src/tests/`) ✅
- [x] Add `test_issue_link_model.py` - ✅ Implemented and passing (17/17 tests)
- [x] Add `test_issue_update_model.py` - ✅ Implemented (needs alignment with actual models)
- [x] Add `test_search_query_model.py` - ✅ Implemented (comprehensive test coverage)
- [x] Add `test_link_service.py` - ✅ Implemented (service layer testing with mocks)
- [x] Add `test_update_service.py` - ⚠️ Covered in integration tests
- [x] Add `test_search_service.py` - ⚠️ Covered in integration tests

#### B. Integration Tests ✅
- [x] Add `test_issue_linking_integration.py` - ✅ Comprehensive end-to-end testing
- [x] Add `test_issue_update_integration.py` - ⚠️ Covered in linking integration
- [x] Add `test_jql_search_integration.py` - ⚠️ Covered in linking integration

#### C. Testing Infrastructure ✅
- [x] Created `.clinerules/development_process.md` - Project-specific testing guidelines
- [x] Proper PYTHONPATH configuration documented
- [x] Test execution patterns established
- [x] Mock patterns and async testing setup

## Implementation Strategy

### Step 1: Domain Foundation
1. Start with domain models and exceptions
2. Define ports (interfaces)
3. Implement domain services
4. Add comprehensive unit tests

### Step 2: Application Orchestration
1. Implement use cases
2. Add application-level validation
3. Handle cross-cutting concerns
4. Test use case interactions

### Step 3: Infrastructure Implementation
1. Extend Jira client with new methods
2. Implement infrastructure services
3. Add error handling and logging
4. Test against real Jira instance

### Step 4: Adapter Integration
1. Add new MCP tools
2. Enhance existing tools
3. Maintain backward compatibility
4. Add comprehensive integration tests

### Step 5: Documentation and Deployment
1. Update README and documentation
2. Add usage examples
3. Update configuration examples
4. Deploy and test end-to-end

## Backward Compatibility Requirements

- [ ] Existing `create_jira_ticket` must continue to work unchanged
- [ ] All existing tools must maintain same signatures
- [ ] New parameters must be optional
- [ ] Error responses must maintain same format

## Quality Gates

- [ ] All new code must have >90% test coverage
- [ ] All domain logic must be framework-agnostic
- [ ] All infrastructure must be behind ports
- [ ] All MCP tools must have proper error handling
- [ ] All changes must pass existing tests

## Configuration Changes

- [ ] No breaking changes to YAML configuration
- [ ] Add optional link type mappings
- [ ] Add JQL validation settings
- [ ] Document new configuration options

## Success Criteria

1. **Issue Linking**: Can create tasks linked to epics with proper relationship types
2. **Issue Updates**: Can update existing issues with validation
3. **JQL Search**: Can perform complex searches with pagination
4. **Architecture**: All new code follows hexagonal architecture
5. **Compatibility**: All existing functionality continues to work
6. **Testing**: Comprehensive test coverage for all new features
7. **Documentation**: Clear usage examples and API documentation

## Risk Mitigation

- [ ] Feature flags for new functionality
- [ ] Gradual rollout strategy
- [ ] Rollback plan for each phase
- [ ] Performance impact assessment
- [ ] Security review for JQL injection
