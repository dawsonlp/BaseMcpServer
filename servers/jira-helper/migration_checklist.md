# Jira Helper Migration Checklist

## Phase 1: Stabilize the Core Interface

-   [x] **Update `JiraRepository` Port:**
    -   [x] Modify all method signatures in `servers/jira-helper/src/domain/ports.py` to make `instance_name` a required parameter.
-   [x] **Update `JiraApiRepository`:**
    -   [x] Update the method signatures in `servers/jira-helper/src/infrastructure/jira_client.py` to match the new `JiraRepository` interface.
-   [x] **Update `AtlassianApiRepository`:**
    -   [x] Update the method signatures in `servers/jira-helper/src/infrastructure/atlassian_api_adapter.py` to match the new `JiraRepository` interface.

## Phase 2: Update the Application Layer

-   [x] **Identify and Update Use Cases:**
    -   [x] Analyze the `servers/jira-helper/src/application/use_cases.py` file to identify all methods that call the `JiraRepository`.
    -   [x] Update the method signatures in the use cases to accept and pass the `instance_name`.
-   [x] **Update MCP Tool Definitions:**
    -   [x] Analyze the `servers/jira-helper/src/adapters/mcp_tool_config.py` file.
    -   [x] Update the tool definitions to require `instance_name` and pass it to the use cases.

## Phase 3: Implement Live Integration Testing

-   [x] **Rewrite `test_atlassian_api_adapter.py`:**
    -   [x] Remove all `unittest.mock` patches.
    -   [x] Update the `atlassian_api_repository` fixture to connect to the live Jira instance.
    -   [x] Rewrite `test_create_and_get_issue` to create and clean up a real issue in the "ATP" project.
    -   [x] Rewrite `test_get_projects` to verify that the "ATP" project is present.
    -   [x] Rewrite `test_add_and_get_comment` to add and clean up a real comment on a test issue.

## Phase 4: Finalize the Migration

-   [ ] **Run Full Test Suite:**
    -   [ ] Execute all tests to ensure the entire application is working as expected.
-   [ ] **Swap Adapters:**
    -   [ ] Update the application's entry point to use `AtlassianApiRepository` instead of `JiraApiRepository`.
-   [ ] **Cleanup:**
    -   [ ] Delete the old `jira_client.py` and its associated tests.
    -   [ ] Delete the `migration_checklist.md` file.
