# Available Tools Reference

## Overview

The Jira Helper MCP Server provides 16 comprehensive tools for Jira integration. All tools support multiple Jira instances and include built-in error handling and validation.

## Search and Discovery Tools

### `list_jira_projects`
List all projects available in the Jira instance.

**Parameters:**
- `instance_name` (optional): Specific Jira instance to query

**Example:**
```bash
list_jira_projects
list_jira_projects instance_name="staging"
```

**Returns:**
- Project list with keys, names, IDs, leads, and URLs
- Total project count
- Instance information

### `list_project_tickets`
List tickets (issues) in a Jira project with optional filtering.

**Parameters:**
- `project_key` (required): Project identifier (e.g., "PROJ")
- `status` (optional): Filter by issue status
- `issue_type` (optional): Filter by issue type
- `max_results` (optional): Maximum results to return (default: 50)
- `instance_name` (optional): Specific Jira instance

**Examples:**
```bash
list_project_tickets project_key="PROJ"
list_project_tickets project_key="PROJ" status="In Progress" max_results=20
list_project_tickets project_key="PROJ" issue_type="Story" status="To Do"
```

**Returns:**
- Filtered issue list with pagination metadata
- Total results count and "has more" indicator
- Issue details: key, summary, status, type, priority, assignee, dates

### `search_jira_issues`
Execute a JQL search query to find Jira issues.

**Parameters:**
- `jql` (required): JQL query string
- `max_results` (optional): Maximum results (default: 50)
- `start_at` (optional): Starting index for pagination (default: 0)
- `fields` (optional): Specific fields to retrieve
- `instance_name` (optional): Specific Jira instance

**Examples:**
```bash
search_jira_issues jql="project = PROJ AND assignee = currentUser()"
search_jira_issues jql="status = 'In Progress' ORDER BY updated DESC" max_results=10
search_jira_issues jql="project = PROJ AND priority = High" start_at=20
```

**Returns:**
- Search results with pagination
- Issue details and metadata
- Total count and pagination info

### `validate_jql_query`
Validate JQL syntax without executing the query.

**Parameters:**
- `jql` (required): JQL query to validate
- `instance_name` (optional): Specific Jira instance

**Example:**
```bash
validate_jql_query jql="project = PROJ AND status = 'Invalid Status'"
```

**Returns:**
- Validation status (valid/invalid)
- Error messages and warnings
- Syntax suggestions

## Issue Management Tools

### `get_issue_details`
Get detailed information about a specific Jira issue.

**Parameters:**
- `issue_key` (required): Issue identifier (e.g., "PROJ-123")
- `instance_name` (optional): Specific Jira instance

**Example:**
```bash
get_issue_details issue_key="PROJ-123"
```

**Returns:**
- Complete issue information
- Fields: summary, description, status, type, priority, assignee, reporter
- Timestamps, components, labels, and URL

### `get_full_issue_details`
Get comprehensive information about a specific Jira issue with formatting options.

**Parameters:**
- `issue_key` (required): Issue identifier
- `raw_data` (optional): Return raw data format (default: false)
- `format` (optional): Output format - "formatted", "summary" (default: "formatted")
- `instance_name` (optional): Specific Jira instance

**Examples:**
```bash
get_full_issue_details issue_key="PROJ-123"
get_full_issue_details issue_key="PROJ-123" format="summary"
get_full_issue_details issue_key="PROJ-123" raw_data=true
```

**Returns:**
- Detailed issue information with comments
- Custom fields and extended metadata
- Comment history with authors and timestamps

### `create_jira_ticket`
Create a new Jira ticket (issue).

**Parameters:**
- `project_key` (required): Target project
- `summary` (required): Issue title
- `description` (required): Issue description
- `issue_type` (optional): Issue type (default: "Story")
- `priority` (optional): Issue priority
- `assignee` (optional): Assignee username
- `labels` (optional): List of labels
- `instance_name` (optional): Specific Jira instance

**Examples:**
```bash
create_jira_ticket project_key="PROJ" summary="New feature" description="Detailed description"
create_jira_ticket project_key="PROJ" summary="Bug fix" description="Fix description" issue_type="Bug" priority="High"
```

**Returns:**
- Created issue details
- Issue key, ID, and URL
- Creation confirmation

### `update_jira_issue`
Update an existing Jira issue with new field values.

**Parameters:**
- `issue_key` (required): Issue to update
- `summary` (optional): New summary
- `description` (optional): New description
- `priority` (optional): New priority
- `assignee` (optional): New assignee
- `labels` (optional): New labels list
- `instance_name` (optional): Specific Jira instance

**Example:**
```bash
update_jira_issue issue_key="PROJ-123" summary="Updated title" priority="High"
```

**Returns:**
- Updated issue information
- Changed fields confirmation
- Issue URL

## Workflow and Status Tools

### `get_issue_transitions`
Get available workflow transitions for a Jira issue.

**Parameters:**
- `issue_key` (required): Issue identifier
- `instance_name` (optional): Specific Jira instance

**Example:**
```bash
get_issue_transitions issue_key="PROJ-123"
```

**Returns:**
- Available transitions list
- Transition IDs, names, and target statuses
- Current issue status

### `transition_jira_issue`
Transition a Jira issue through its workflow.

**Parameters:**
- `issue_key` (required): Issue to transition
- `transition_name` (required): Transition to execute
- `comment` (optional): Comment to add during transition
- `instance_name` (optional): Specific Jira instance

**Examples:**
```bash
transition_jira_issue issue_key="PROJ-123" transition_name="In Progress"
transition_jira_issue issue_key="PROJ-123" transition_name="Done" comment="Completed successfully"
```

**Returns:**
- Transition success confirmation
- New issue status
- Comment addition confirmation

### `change_issue_assignee`
Change the assignee of a Jira issue.

**Parameters:**
- `issue_key` (required): Issue to reassign
- `assignee` (optional): New assignee username (null to unassign)
- `instance_name` (optional): Specific Jira instance

**Examples:**
```bash
change_issue_assignee issue_key="PROJ-123" assignee="john.doe"
change_issue_assignee issue_key="PROJ-123"  # Unassign
```

**Returns:**
- Assignment change confirmation
- New assignee information
- Issue URL

## Collaboration Tools

### `add_comment_to_jira_ticket`
Add a comment to an existing Jira ticket.

**Parameters:**
- `issue_key` (required): Target issue
- `comment` (required): Comment text
- `instance_name` (optional): Specific Jira instance

**Example:**
```bash
add_comment_to_jira_ticket issue_key="PROJ-123" comment="Status update: work in progress"
```

**Returns:**
- Comment addition confirmation
- Comment ID and author
- Comment body and timestamp

## Configuration and Metadata Tools

### `list_jira_instances`
List all configured Jira instances.

**Parameters:** None

**Example:**
```bash
list_jira_instances
```

**Returns:**
- All configured instances
- Instance details: name, URL, user, description
- Default instance indicator

### `get_custom_field_mappings`
Get mappings between Jira custom field IDs and their names/descriptions.

**Parameters:**
- `reverse` (optional): Reverse mapping direction (default: false)
- `instance_name` (optional): Specific Jira instance

**Examples:**
```bash
get_custom_field_mappings
get_custom_field_mappings reverse=true instance_name="staging"
```

**Returns:**
- Field ID to name mappings
- Field descriptions and types
- Total field count

### `generate_project_workflow_graph`
Generate a visual workflow graph for a specific project and issue type.

**Parameters:**
- `project_key` (required): Target project
- `issue_type` (optional): Issue type (default: "Story")
- `format` (optional): Output format (default: "svg")
- `instance_name` (optional): Specific Jira instance

**Example:**
```bash
generate_project_workflow_graph project_key="PROJ" issue_type="Bug" format="svg"
```

**Returns:**
- Workflow graph data
- Visual representation of transitions
- Project and issue type information

## Common Parameters

### Instance Selection
All tools support the `instance_name` parameter to target specific Jira instances:
- Omit for default instance
- Use configured instance name for specific instance
- Check `list_jira_instances` for available instances

### Pagination
Search tools support pagination:
- `max_results`: Limit result count (default varies by tool)
- `start_at`: Starting index for pagination
- Response includes `has_more` indicator

### Error Handling
All tools include:
- Input validation and sanitization
- Comprehensive error messages
- Graceful failure handling
- Security validation (JQL injection prevention)

## Usage Tips

### Efficient Searching
1. Use specific filters to reduce result sets
2. Leverage JQL for complex queries
3. Use pagination for large result sets
4. Validate JQL before executing searches

### Workflow Management
1. Check available transitions before attempting transitions
2. Use comments during transitions for audit trails
3. Verify assignee exists before assignment
4. Monitor workflow state changes

### Performance Optimization
1. Limit `max_results` for faster responses
2. Use specific field selection when available
3. Filter at the source rather than post-processing
4. Cache frequently accessed data

---

**Need Help?** Check the [Getting Started Guide](getting-started.md) for setup instructions or [Troubleshooting](troubleshooting.md) for common issues.
