# Jira Helper MCP Server Enhancements

This document summarizes the enhancements made to the Jira Helper MCP server to support multiple instances, workflow transitions, and assignee management.

## Summary of Changes

### 1. Multiple Jira Instance Support

**Configuration Changes:**
- Added `JiraInstance` class to represent individual Jira configurations
- Enhanced `Settings` class with `get_jira_instances()` and `get_default_instance_name()` methods
- Added support for `JIRA_INSTANCES` JSON environment variable
- Maintained backward compatibility with legacy single-instance configuration

**Implementation:**
- Updated `create_jira_client()` function to accept `instance_name` parameter
- All tools now support optional `instance_name` parameter
- Automatic fallback to default instance when none specified

### 2. New Workflow Management Tools

**transition_jira_issue:**
- Move issues through their workflow states
- Support for optional comments during transitions
- Validation of available transitions before execution
- Returns old status, new status, and transition details

**get_issue_transitions:**
- List all available workflow transitions for an issue
- Shows transition names and target statuses
- Helps users understand what transitions are possible

### 3. Assignee Management

**change_issue_assignee:**
- Assign issues to specific users
- Unassign issues (set assignee to None)
- Verification of assignment changes
- Support for username or email as assignee identifier

### 4. Enhanced Instance Management

**list_jira_instances:**
- List all configured Jira instances
- Show which instance is the default
- Display instance URLs, users, and descriptions

**Updated Resources:**
- Enhanced `resource://jira/instances` to show all configured instances
- Added proper error handling and instance information

### 5. Workflow Visualization

**generate_project_workflow_graph:**
- Generate visual workflow graphs for projects and issue types
- Support multiple output formats: SVG, PNG, DOT, and JSON
- Automatic workflow discovery from Jira project configuration
- Fallback mechanisms for different Jira configurations
- Color-coded status categories (To Do, In Progress, Done)
- Base64-encoded output for easy integration

### 5. Improved Tool Signatures

**Updated Existing Tools:**
All existing tools now support the `instance_name` parameter:
- `list_jira_projects`
- `get_issue_details`
- `list_project_tickets`

**Enhanced Return Values:**
- All tools now include `instance` field in responses
- Consistent error handling across all tools
- Proper URL generation for different instances

## Configuration Examples

### Single Instance (Legacy)
```bash
JIRA_URL=https://company.atlassian.net
JIRA_USER=user@company.com
JIRA_TOKEN=your-api-token
```

### Multiple Instances
```bash
JIRA_INSTANCES='[
  {
    "name": "production",
    "url": "https://company.atlassian.net",
    "user": "user@company.com",
    "token": "prod-token",
    "description": "Production Jira"
  },
  {
    "name": "staging",
    "url": "https://staging.atlassian.net",
    "user": "user@company.com",
    "token": "staging-token",
    "description": "Staging Jira"
  }
]'
```

## New Tool Usage Examples

### Workflow Transitions
```python
# Check available transitions
transitions = await session.call_tool("get_issue_transitions", {
    "issue_key": "PROJ-123",
    "instance_name": "production"
})

# Transition issue with comment
result = await session.call_tool("transition_jira_issue", {
    "issue_key": "PROJ-123",
    "transition_name": "Start Progress",
    "comment": "Beginning work on this issue",
    "instance_name": "production"
})
```

### Assignee Management
```python
# Assign to user
result = await session.call_tool("change_issue_assignee", {
    "issue_key": "PROJ-123",
    "assignee": "john.doe@company.com",
    "instance_name": "production"
})

# Unassign issue
result = await session.call_tool("change_issue_assignee", {
    "issue_key": "PROJ-123",
    "assignee": "",  # Empty to unassign
    "instance_name": "production"
})
```

### Multi-Instance Operations
```python
# List instances
instances = await session.call_tool("list_jira_instances")

# Work with specific instance
projects = await session.call_tool("list_jira_projects", {
    "instance_name": "staging"
})
```

### Workflow Visualization
```python
# Generate SVG workflow graph
graph = await session.call_tool("generate_project_workflow_graph", {
    "project_key": "PROJ",
    "issue_type": "Story",
    "format": "svg",
    "instance_name": "production"
})
# Returns base64-encoded SVG data

# Generate JSON workflow structure
workflow_data = await session.call_tool("generate_project_workflow_graph", {
    "project_key": "PROJ",
    "issue_type": "Bug",
    "format": "json"
})
# Returns structured workflow data with nodes and edges

# Generate DOT format for custom processing
dot_graph = await session.call_tool("generate_project_workflow_graph", {
    "project_key": "PROJ",
    "format": "dot"
})
# Returns DOT language representation
```

## Backward Compatibility

All changes maintain full backward compatibility:
- Existing single-instance configurations continue to work
- All existing tools work without specifying `instance_name`
- Legacy environment variables are still supported
- Default instance behavior ensures seamless operation

## Error Handling

Enhanced error handling includes:
- Clear error messages when instances are not found
- Validation of transition availability before execution
- Proper handling of authentication failures
- Informative error responses with available options

## Security Considerations

- Multiple API tokens are handled securely
- No tokens are exposed in error messages or logs
- Instance configurations support individual authentication
- Backward compatibility doesn't compromise security

## Testing Recommendations

1. **Single Instance Testing:**
   - Verify legacy configuration still works
   - Test all existing tools without instance_name parameter

2. **Multi-Instance Testing:**
   - Configure multiple instances
   - Test instance selection and fallback behavior
   - Verify instance-specific operations

3. **New Feature Testing:**
   - Test workflow transitions with valid and invalid transition names
   - Test assignee changes with valid users and unassignment
   - Test error conditions and edge cases

4. **Integration Testing:**
   - Test with real Jira instances
   - Verify permissions and authentication
   - Test cross-instance operations

## Future Enhancements

Potential future improvements:
1. **Bulk Operations:** Support for bulk issue updates across instances
2. **Advanced Filtering:** More sophisticated JQL query building
3. **Webhook Support:** Real-time notifications from Jira instances
4. **Custom Field Management:** Enhanced custom field manipulation
5. **Project Templates:** Support for creating projects from templates
6. **Advanced Workflow:** Support for complex workflow operations
7. **Reporting:** Built-in reporting and analytics tools

## Migration Guide

For users upgrading from the previous version:

1. **No Action Required:** Existing configurations will continue to work
2. **Optional Migration:** To use multiple instances, add `JIRA_INSTANCES` environment variable
3. **New Features:** Start using new tools for workflow and assignee management
4. **Testing:** Verify existing integrations continue to work as expected

The enhanced Jira Helper MCP server provides significantly more functionality while maintaining complete backward compatibility, making it a powerful tool for managing Jira instances in complex environments.
