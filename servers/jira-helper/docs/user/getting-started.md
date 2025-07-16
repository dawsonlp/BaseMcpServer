# Getting Started with Jira Helper MCP Server

## Overview

The Jira Helper MCP Server provides seamless integration with Jira through the Model Context Protocol (MCP). This guide will help you get up and running quickly.

## Prerequisites

- **mcp-manager**: For server installation and management
- **Jira Access**: Valid Jira instance with API access
- **MCP Client**: Any MCP-compatible client (like Cline)

## Installation

### 1. Install the Server

```bash
mcp-manager install local jira-helper --source servers/jira-helper --force
```

### 2. Configure Jira Connection

Create a configuration file:

```bash
cd servers/jira-helper
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your Jira details:

```yaml
jira_instances:
  default:
    url: "https://your-company.atlassian.net"
    user: "your-email@company.com"
    token: "your-api-token"
    description: "Main Jira instance"
    is_default: true
```

### 3. Get Your Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "MCP Server")
4. Copy the token to your config file

## Basic Usage

### Search for Issues

```bash
# List issues in a project
list_project_tickets project_key="PROJ" max_results=10

# Search with filters
list_project_tickets project_key="PROJ" status="In Progress" issue_type="Story"

# Advanced JQL search
search_jira_issues jql="project = PROJ AND assignee = currentUser()" max_results=20
```

### Issue Management

```bash
# Get issue details
get_issue_details issue_key="PROJ-123"

# Create a new issue
create_jira_ticket project_key="PROJ" summary="New feature" description="Detailed description" issue_type="Story"

# Add a comment
add_comment_to_jira_ticket issue_key="PROJ-123" comment="Status update"

# Transition an issue
transition_jira_issue issue_key="PROJ-123" transition_name="In Progress"
```

### Time Tracking

```bash
# Log work
log_work issue_key="PROJ-123" time_spent="2h" comment="Development work"

# Get work logs
get_work_logs issue_key="PROJ-123"

# Update time estimates
update_time_estimates issue_key="PROJ-123" original_estimate="8h" remaining_estimate="4h"
```

## Common Workflows

### Daily Standup Preparation

```bash
# Get your current work
search_jira_issues jql="assignee = currentUser() AND status = 'In Progress'" max_results=10

# Check recent updates
search_jira_issues jql="assignee = currentUser() AND updated >= -1d" max_results=20
```

### Project Status Review

```bash
# Get project overview
list_project_tickets project_key="PROJ" max_results=50

# Check blocked issues
search_jira_issues jql="project = PROJ AND status = 'Blocked'" max_results=20

# Review recent completions
search_jira_issues jql="project = PROJ AND status = 'Done' AND resolved >= -7d" max_results=30
```

### Issue Triage

```bash
# Get unassigned issues
search_jira_issues jql="project = PROJ AND assignee is EMPTY AND status = 'To Do'" max_results=20

# Check high priority items
list_project_tickets project_key="PROJ" status="To Do" max_results=20
```

## Configuration Options

### Multiple Jira Instances

```yaml
jira_instances:
  production:
    url: "https://company.atlassian.net"
    user: "user@company.com"
    token: "prod-token"
    description: "Production Jira"
    is_default: true
    
  staging:
    url: "https://staging.atlassian.net"
    user: "user@company.com"
    token: "staging-token"
    description: "Staging Environment"
    is_default: false
```

Use specific instances:

```bash
get_issue_details issue_key="PROJ-123" instance_name="staging"
```

### Performance Tuning

```yaml
# In config.yaml
performance:
  max_results_default: 50
  timeout_seconds: 30
  retry_attempts: 3
```

## Security Best Practices

1. **API Tokens**: Use dedicated API tokens, not passwords
2. **Permissions**: Grant minimal required permissions
3. **Rotation**: Regularly rotate API tokens
4. **Environment**: Store sensitive config in environment variables

```bash
# Using environment variables
export JIRA_TOKEN="your-token-here"
export JIRA_URL="https://company.atlassian.net"
```

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify URL format (include https://)
- Check API token validity
- Confirm user permissions

**No Results Found**
- Check project key spelling
- Verify user has access to project
- Try simpler search criteria

**Slow Performance**
- Reduce max_results parameter
- Use more specific search filters
- Check Jira instance performance

### Getting Help

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review [Available Tools](available-tools.md) for syntax
3. Examine server logs: `mcp-manager run jira-helper`

## Next Steps

- Explore [Available Tools](available-tools.md) for complete functionality
- Learn about [Configuration](configuration.md) options
- Check out advanced usage in the [Developer Guide](../developer/development-setup.md)

---

**Need Help?** Check the troubleshooting guide or review the tool documentation for detailed parameter information.
