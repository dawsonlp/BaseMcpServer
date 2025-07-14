# Jira Helper Hexagonal Architecture Refactoring Checklist

## Overview
Refactoring the monolithic jira-helper server.py (1000+ lines) into clean hexagonal architecture to enable independent testing of Jira functionality separate from the MCP framework.

## Current Architecture Problems
- [x] **Identified**: Monolithic server.py with all business logic tightly coupled to MCP framework
- [x] **Identified**: Direct Jira API calls embedded in MCP tool functions
- [x] **Identified**: No separation of concerns between domain logic and infrastructure
- [x] **Identified**: Cannot test Jira functionality independently of MCP framework
- [x] **Identified**: Configuration directly accessed throughout codebase

## Phase 1: Domain Layer (Core Business Logic)
### Domain Models
- [x] Create `domain/models.py` with core entities:
  - [x] `JiraIssue` - Core issue entity with all properties
  - [x] `JiraProject` - Project entity
  - [x] `WorkflowTransition` - Transition entity
  - [x] `JiraComment` - Comment entity
  - [x] `WorkflowGraph` - Workflow visualization entity
  - [x] `JiraInstance` - Instance configuration entity

### Domain Ports (Interfaces)
- [x] Create `domain/ports.py` with interfaces:
  - [x] `JiraRepository` - Interface for Jira data operations
  - [x] `WorkflowService` - Interface for workflow operations
  - [x] `GraphGenerator` - Interface for graph generation
  - [x] `ConfigurationProvider` - Interface for configuration access

### Domain Services
- [x] Create `domain/services.py` with business logic:
  - [x] `IssueService` - Core issue management logic
  - [x] `ProjectService` - Project management logic
  - [x] `WorkflowService` - Workflow transition logic
  - [x] `VisualizationService` - Graph generation logic

### Domain Exceptions
- [x] Create `domain/exceptions.py` with domain-specific exceptions

## Phase 2: Application Layer (Use Cases)
### Use Cases
- [x] Create `application/use_cases.py` with:
  - [x] `ListProjectsUseCase`
  - [x] `GetIssueDetailsUseCase`
  - [x] `GetFullIssueDetailsUseCase`
  - [x] `CreateIssueUseCase`
  - [x] `AddCommentUseCase`
  - [x] `TransitionIssueUseCase`
  - [x] `GetIssueTransitionsUseCase`
  - [x] `ChangeAssigneeUseCase`
  - [x] `ListProjectTicketsUseCase`
  - [x] `GetCustomFieldMappingsUseCase`
  - [x] `GenerateWorkflowGraphUseCase`
  - [x] `ListInstancesUseCase`

### Application Services
- [ ] Create `application/services.py` with:
  - [ ] `JiraApplicationService` - Orchestrates use cases
  - [ ] `ValidationService` - Input validation logic

## Phase 3: Infrastructure Layer (External Dependencies)
### Repository Implementations
- [x] Create `infrastructure/jira_client.py` with:
  - [x] `JiraApiRepository` - Implements JiraRepository using Jira API
  - [x] `JiraClientFactory` - Creates and manages Jira clients

### Configuration Implementation
- [x] Create `infrastructure/config_adapter.py` with:
  - [x] `ConfigurationAdapter` - Implements ConfigurationProvider

### Graph Generation Implementation
- [x] Create `infrastructure/graph_generator.py` with:
  - [x] `GraphvizGenerator` - Implements GraphGenerator
  - [x] `WorkflowAnalyzerImpl` - Graph processing utilities

## Phase 4: Adapters Layer (Framework Integration)
### MCP Adapter
- [x] Create `adapters/mcp_adapter.py` with:
  - [x] `McpJiraAdapter` - Translates between MCP tools and use cases
  - [x] Keep all MCP-specific code isolated here
  - [x] All 12 MCP tools implemented with proper error handling
  - [x] Dependency injection and lifecycle management
  - [x] FastMCP integration with lifespan context

### Future Adapters (Prepared Structure)
- [ ] Prepare structure for:
  - [ ] `CliAdapter` - For potential CLI interface
  - [ ] `RestAdapter` - For potential REST API interface

## Phase 5: Directory Structure Creation
- [ ] Create new directory structure:
  ```
  servers/jira-helper/src/
  ├── domain/
  │   ├── __init__.py
  │   ├── models.py
  │   ├── ports.py
  │   ├── services.py
  │   └── exceptions.py
  ├── application/
  │   ├── __init__.py
  │   ├── use_cases.py
  │   └── services.py
  ├── infrastructure/
  │   ├── __init__.py
  │   ├── jira_client.py
  │   ├── config_adapter.py
  │   └── graph_generator.py
  ├── adapters/
  │   ├── __init__.py
  │   └── mcp_adapter.py
  └── tests/
      ├── __init__.py
      ├── test_domain.py
      ├── test_use_cases.py
      └── test_integration.py
  ```

## Phase 6: Testing Strategy Implementation
### Unit Tests for Domain Layer
- [ ] Create `tests/test_domain.py`:
  - [ ] Test pure business logic without external dependencies
  - [ ] Mock all ports/interfaces
  - [ ] Property-based testing for complex logic

### Integration Tests
- [ ] Create `tests/test_integration.py`:
  - [ ] Test Jira API integration with real/mock services
  - [ ] Test configuration loading
  - [ ] Test graph generation

### Use Case Tests
- [ ] Create `tests/test_use_cases.py`:
  - [ ] Test complete workflows
  - [ ] Test error handling
  - [ ] Test multi-instance scenarios

## Phase 7: Migration Strategy (Incremental)
### Tool-by-Tool Migration
- [ ] **Tool 1**: `list_jira_projects`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 2**: `get_issue_details`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 3**: `get_full_issue_details`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 4**: `create_jira_ticket`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 5**: `add_comment_to_jira_ticket`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 6**: `transition_jira_issue`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 7**: `get_issue_transitions`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 8**: `change_issue_assignee`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 9**: `list_project_tickets`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 10**: `get_custom_field_mappings`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 11**: `generate_project_workflow_graph`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

- [ ] **Tool 12**: `list_jira_instances`
  - [ ] Extract domain model and use case
  - [ ] Create infrastructure adapter
  - [ ] Update MCP adapter
  - [ ] Test thoroughly

### Backward Compatibility
- [ ] Maintain existing MCP tool signatures
- [ ] Ensure all current functionality works
- [ ] No breaking changes to external interface

## Phase 8: Final Integration and Testing
### Complete Integration
- [ ] Update `server.py` to use new architecture
- [ ] Update `main.py` if needed
- [ ] Ensure all tools work through new architecture

### Comprehensive Testing
- [ ] Run all existing functionality tests
- [ ] Test multi-instance scenarios
- [ ] Test error handling
- [ ] Performance testing

### Documentation Updates
- [ ] Update README.md with new architecture
- [ ] Document testing approach
- [ ] Document extension points for future adapters

## Phase 9: Benefits Validation
### Independent Testing Capability
- [ ] Verify domain logic testable without MCP framework
- [ ] Verify use cases testable with mocked repositories
- [ ] Verify clear separation of concerns

### Future Extensibility
- [ ] Verify easy to add new adapters (CLI, REST API)
- [ ] Verify easy to swap Jira API implementation
- [ ] Verify easy to add new Jira functionality

## Success Criteria
- [ ] All existing MCP tools continue to work exactly as before
- [ ] Domain logic can be tested independently of MCP framework
- [ ] Clear separation between business logic and infrastructure
- [ ] Easy to extend with new adapters or Jira functionality
- [ ] Improved code maintainability and readability
- [ ] Comprehensive test coverage at all layers

## Notes
- Start with Phase 1 and work incrementally
- Test each phase thoroughly before proceeding
- Maintain backward compatibility throughout
- Focus on one tool at a time during migration phase
