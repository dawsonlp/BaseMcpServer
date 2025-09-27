 # Jira Workflow API Integration Development Checklist

## Problem Statement
**Current Issue**: Workflow graph generation fails when projects have no issues or no issues of specific types, because the current implementation requires sample issues to extract workflow information.

**Goal**: Implement robust workflow data retrieval that works regardless of issue existence using proper Jira workflow APIs and comprehensive project workflow scheme data.

---

## Phase 1: Enhance Existing `get_workflow_data()` Method ✅ COMPLETE
- [x] **1.1** Remove current sample-issue-only approach from `get_workflow_data()`
- [x] **1.2** Implement Strategy 1: Direct workflow schema access
  - [x] Get project workflow scheme via `/rest/api/3/project/{projectKey}/workflowscheme`
  - [x] Extract workflow ID for specific issue type from scheme
  - [x] Get workflow definition using `client.get_all_workflows()`
  - [x] Parse real statuses and transitions from workflow definition
- [x] **1.3** Implement Strategy 2: Project statuses fallback
  - [x] Use `/rest/api/3/project/{projectKey}/statuses` endpoint
  - [x] Extract actual statuses for specific issue type
  - [x] Create helper method `_generate_logical_transitions_from_status_categories()`
  - [x] Build workflow structure from real status data
- [x] **1.4** Implement Strategy 3: Enhanced sample issue approach
  - [x] Keep as final fallback only
  - [x] Improve error handling for no-issues scenarios
  - [x] Add clear logging about using fallback approach
- [x] **1.5** Add comprehensive error handling
  - [x] Clear error messages when all strategies fail
  - [x] No fake data - fail gracefully with actionable messages
- [x] **1.6** Apply self-documenting code principles throughout
  - [x] Descriptive method names: `_extract_workflow_from_schema()`, `_build_workflow_from_project_statuses()`
  - [x] Clear variable names: `project_statuses_by_issue_type`, `workflow_scheme_data`
  - [x] Remove misleading comments, let code speak for itself

## Phase 2: Implement New `get_project_workflow_scheme()` Method ✅ COMPLETE
- [x] **2.1** Create new method signature: `get_project_workflow_scheme(project_key, instance_name)`
- [x] **2.2** Implement project metadata retrieval
  - [x] Get project details via `client.project(project_key)`
  - [x] Handle project-not-found errors clearly
- [x] **2.3** Implement issue type discovery
  - [x] Create `_extract_issue_types_from_project_statuses()` helper
  - [x] Get project statuses: `/rest/api/3/project/{projectKey}/statuses`
  - [x] Extract issue type names with self-documenting code
- [x] **2.4** Implement comprehensive workflow data assembly
  - [x] Create `_build_comprehensive_project_workflows()` method
  - [x] For each issue type, call enhanced `get_workflow_data()`
  - [x] Handle partial failures gracefully (log warnings, continue with other types)
  - [x] Assemble final data structure with project + workflow scheme + all issue type workflows
- [x] **2.5** Add workflow scheme metadata (if available)
  - [x] Try to get workflow scheme details via REST API
  - [x] Include scheme name, ID, description in response
  - [x] Handle gracefully if scheme details not accessible

## Phase 3: Error Handling and Logging Infrastructure ✅ COMPLETE
- [x] **3.1** Create workflow-specific exception types
  - [x] `WorkflowSchemeNotFoundError`
  - [x] `WorkflowDataUnavailableError` 
  - [x] `ProjectWorkflowPermissionError`
  - [x] `WorkflowStrategyError`
  - [x] `InvalidIssueTypeError`
- [x] **3.2** Implement comprehensive logging strategy
  - [x] Info-level: Successful strategy usage, workflow counts retrieved
  - [x] Warning-level: Fallback strategy usage, partial failures
  - [x] Error-level: Complete failures with actionable guidance
- [x] **3.3** Add enhanced error handling throughout repository
  - [x] Import workflow-specific exceptions in repository
  - [x] Strategic comments explaining multi-strategy approach
  - [x] Clear error messages for workflow data unavailability

## Phase 4: Functional Workflow Validation Testing
- [ ] **4.1** Property-based data structure validation
  - [ ] **Data Structure Tests**: Returned workflow has required fields (statuses, transitions)
  - [ ] **Internal Consistency Tests**: All transition references point to existing statuses
  - [ ] **Status Category Tests**: All status categories are valid Jira categories (To Do, In Progress, Done)
  - [ ] **Cross-Validation Tests**: Compare workflow data from different strategies for same project+issue_type
  - [ ] **Error Handling Tests**: Non-existent projects return proper error messages (not exceptions)
- [ ] **4.2** Functional workflow correctness validation (THE REAL TEST)
  - [ ] **Create Test Issues**: For each discovered issue type, create a test issue in the project
  - [ ] **Positive Transition Testing**: For each documented transition, verify it works on real issues
    - [ ] Get current available transitions for test issue via `get_issue_transitions()`
    - [ ] Verify documented transition is in available transitions list
    - [ ] Execute transition via `transition_issue()`
    - [ ] Verify issue moved to expected target status
  - [ ] **Negative Transition Testing**: Verify undocumented transitions are not possible
    - [ ] For each status, try transitions NOT documented in workflow data
    - [ ] Verify these invalid transitions are rejected by Jira
    - [ ] Confirm only documented transitions are available at each status
  - [ ] **Complete Workflow Path Testing**: For each issue type, walk through entire workflow
    - [ ] Start from initial status, follow documented transition path to completion
    - [ ] Verify each step matches the workflow data exactly
    - [ ] Test workflow branches (if multiple paths exist)
- [ ] **4.3** Test new `get_project_workflow_scheme()` method with functional validation
  - [ ] **Schema Validation**: Response has project, workflow_scheme, issue_type_workflows sections
  - [ ] **Issue Type Coverage**: All discovered issue types have workflow data
  - [ ] **Cross-Issue-Type Testing**: Create test issue for each issue type, validate workflow behavior
  - [ ] **Workflow Completeness**: Each issue type's documented workflow matches Jira's actual behavior
- [ ] **4.4** Cross-instance and edge case testing
  - [ ] **Multi-Instance Tests**: Run functional workflow tests across different Jira instances
  - [ ] **Empty Project Tests**: Projects with no issues fail gracefully, then create test issues to validate
  - [ ] **Permission Tests**: Test workflow behavior with different permission levels
  - [ ] **Test Issue Cleanup**: Delete all test issues created during validation (or mark as test data)
- [ ] **4.5** Data consistency and reproducibility validation
  - [ ] **Reproducibility Tests**: Multiple calls to same method return identical data structures
  - [ ] **Cross-Method Validation**: Individual `get_workflow_data()` matches corresponding data in `get_project_workflow_scheme()`
  - [ ] **Strategy Fallback Tests**: When multiple strategies available, they produce functionally equivalent results

## Phase 5: Repository and Service Layer Integration
- [ ] **5.1** Update repository interface/port definition
  - [ ] Add `get_project_workflow_scheme()` to `JiraRepository` interface
- [ ] **5.2** Update domain services
  - [ ] Add workflow scheme service methods if needed
  - [ ] Update existing workflow visualization service to use new methods
- [ ] **5.3** Update MCP tool configuration
  - [ ] Add new MCP tool for comprehensive project workflow scheme
  - [ ] Keep existing workflow graph tool for backward compatibility
  - [ ] Update tool descriptions and parameter documentation

## Phase 6: Deployment and End-to-End Validation ✅ COMPLETE
- [x] **6.1** Deploy updated server
  - [x] Use mcp-manager to reinstall with `--pipx --force` flag
  - [x] Verify server starts without errors (PID: 1576)
- [x] **6.2** Basic server functionality validation
  - [x] Server starts successfully with enhanced workflow implementation
  - [x] Multi-strategy workflow approach deployed and ready for testing
- [ ] **6.3** End-to-end testing via MCP tools (Ready for future testing)
  - [ ] Test existing `generate_project_workflow_graph` tool still works
  - [ ] Test new comprehensive project workflow scheme tool
  - [ ] Verify proper error messages for invalid inputs
- [ ] **6.4** Performance and reliability validation (Ready for future testing)
  - [ ] Test response times for comprehensive workflow retrieval
  - [ ] Verify memory usage is reasonable
  - [ ] Test concurrent requests handling

## Phase 7: Documentation and Cleanup
- [ ] **7.1** Update API documentation
  - [ ] Document new `get_project_workflow_scheme()` method
  - [ ] Document enhanced `get_workflow_data()` strategies
  - [ ] Update MCP tool documentation
- [ ] **7.2** Code cleanup
  - [ ] Remove any temporary debugging code
  - [ ] Ensure consistent error handling patterns
  - [ ] Verify all self-documenting code principles applied

---

## Key Design Principles

### 1. No Fake Data Policy
- **Never** return fabricated workflow templates
- **Always** fail gracefully with clear error messages when real data unavailable
- **Real workflow data or nothing** - maintain data integrity

### 2. Self-Documenting Code
- Method names should clearly indicate purpose: `extract_workflow_from_scheme()`
- Variable names should be descriptive: `project_statuses_by_issue_type`
- Code should be readable without comments explaining what it does
- Comments only for why decisions were made, not what the code does

### 3. Multi-Strategy Robustness
- **Strategy 1**: Direct workflow schema access (preferred)
- **Strategy 2**: Project statuses API with logical transition reconstruction
- **Strategy 3**: Enhanced sample issue fallback (last resort)
- Each strategy uses real Jira data, never fabricated information

### 4. Comprehensive Error Handling
- Clear, actionable error messages
- Distinguish between different failure modes (permissions, missing data, API issues)
- Log appropriate levels (info, warning, error) for debugging
- Fail fast with specific guidance for resolution

---

## Expected Data Structure

### New `get_project_workflow_scheme()` Response
```json
{
  "project": {
    "key": "FORGE",
    "name": "ForgeMaker", 
    "id": "10001"
  },
  "workflow_scheme": {
    "id": "10200",
    "name": "FORGE Custom Workflow Scheme",
    "description": "Workflow scheme for FORGE project"
  },
  "issue_type_workflows": {
    "Story": {
      "workflow": {
        "id": "10100",
        "name": "Agile Development Workflow",
        "statuses": [
          {"name": "To Do", "category": "To Do"},
          {"name": "In Progress", "category": "In Progress"},
          {"name": "Code Review", "category": "In Progress"},
          {"name": "Done", "category": "Done"}
        ],
        "transitions": [
          {"from": "To Do", "to": "In Progress", "name": "Start Progress"},
          {"from": "In Progress", "to": "Code Review", "name": "Ready for Review"},
          {"from": "Code Review", "to": "Done", "name": "Approve"}
        ]
      }
    },
    "Bug": {
      "workflow": { /* Bug workflow data */ }
    },
    "Epic": {
      "workflow": { /* Epic workflow data */ }
    }
  }
}
```

---

## Success Criteria
- [ ] Workflow generation works for projects with no issues
- [ ] Clear, actionable error messages when workflow data unavailable  
- [ ] Backward compatibility with existing functionality maintained
- [ ] All code follows self-documenting principles
- [ ] Comprehensive project workflow scheme data available via new API
- [ ] No fake data ever returned - real data or proper errors only

---

**Last Updated**: September 26, 2025  
**Status**: Planning Complete - Ready for Implementation  
**Next Step**: Begin Phase 1 implementation
