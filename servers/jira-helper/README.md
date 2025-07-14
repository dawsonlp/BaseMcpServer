# Jira Helper MCP Server

A comprehensive MCP server for interacting with Jira instances. This server provides tools for managing Jira issues, including support for multiple Jira instances, workflow transitions, and assignee management.

## Features

- **Multiple Jira Instance Support**: Connect to and manage multiple Jira instances simultaneously
- **Issue Management**: Create, read, update, and comment on Jira issues
- **Workflow Transitions**: Move issues through their workflow states
- **Assignee Management**: Change issue assignees or unassign issues
- **Project Management**: List projects and tickets with filtering options
- **Custom Field Support**: Access and understand custom fields in your Jira instances
- **Fully Dockerized**: Easy to build and deploy
- **Based on MCP Python SDK**: Uses the official Model Context Protocol SDK

## Project Structure

```
jira-helper/
├── src/                     # Application code
│   ├── __init__.py
│   ├── config.py            # Configuration handling with multi-instance support
│   ├── main.py              # Entry point for the server
│   └── server.py            # MCP server implementation with Jira tools and resources
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Dockerfile to build the image
│   └── build.sh             # Build script for Docker image
├── .env.example             # Example environment variables
├── README.md                # This file
├── requirements.txt         # Python dependencies
├── run.sh                   # Local development runner
└── setup.sh                 # Setup script
```

## Prerequisites

- Docker installed and configured (for containerized deployment)
- Python 3.13+ (for local development)
- Jira API tokens for the instances you want to connect to

## Configuration

### Single Jira Instance (Legacy)

For backward compatibility, you can configure a single Jira instance using individual environment variables:

```bash
cp .env.example .env
# Edit .env with your Jira details:
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER=your-jira-email@example.com
JIRA_TOKEN=your-jira-api-token
```

### Multiple Jira Instances

To configure multiple Jira instances, use the `JIRA_INSTANCES` environment variable with JSON format. You can use either single-line or multi-line format:

**Multi-line format (recommended for readability):**
```bash
JIRA_INSTANCES='[
  {
    "name": "production",
    "url": "https://company.atlassian.net",
    "user": "user@company.com",
    "token": "your-production-token",
    "description": "Production Jira instance"
  },
  {
    "name": "staging",
    "url": "https://staging.atlassian.net",
    "user": "user@company.com",
    "token": "your-staging-token",
    "description": "Staging Jira instance"
  }
]'
```

**Single-line format:**
```bash
JIRA_INSTANCES='[{"name": "production", "url": "https://company.atlassian.net", "user": "user@company.com", "token": "your-production-token", "description": "Production Jira"}, {"name": "staging", "url": "https://staging.atlassian.net", "user": "user@company.com", "token": "your-staging-token", "description": "Staging Jira"}]'
```

**Important:** When using multi-line format, wrap the entire JSON in single quotes to preserve the formatting.

### Getting Jira API Tokens

1. Go to your Jira instance
2. Navigate to Account Settings → Security → API tokens
3. Create a new API token
4. Use your email address as the username and the token as the password

## Building and Running

### Docker Deployment

```bash
# Build the Docker image
./docker/build.sh jira-helper-server latest 7501 <your-docker-username>

# Run the container
docker run -p 7501:7501 --env-file .env jira-helper-server:latest
```

### Local Development

```bash
# Set up the project-specific virtual environment
./setup.sh

# Run the server (automatically activates venv)
./run.sh
```

**Note:** The project uses a server-specific virtual environment (`.venv/`) that inherits from the base project requirements and adds Jira-specific dependencies. The setup script will:

1. Create a Python 3.13+ virtual environment in `.venv/`
2. Install base MCP dependencies from `../../requirements-base.txt`
3. Install server-specific dependencies (Jira API, graph visualization)

**Manual Setup (if needed):**
```bash
# Create and activate virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r ../../requirements-base.txt
pip install -r requirements.txt
```

## Available Tools

### Core Issue Management

1. **list_jira_projects** - List all projects in a Jira instance
   - Parameters:
     - `instance_name` (optional): Name of the Jira instance to use

2. **get_issue_details** - Get detailed information about a specific issue
   - Parameters:
     - `issue_key`: The Jira issue key (e.g., 'PROJECT-123')
     - `instance_name` (optional): Name of the Jira instance to use

3. **get_full_issue_details** - Get comprehensive issue information with formatting options
   - Parameters:
     - `issue_key`: The Jira issue key
     - `raw_data` (optional): Return raw API data if true
     - `format` (optional): "formatted" or "summary"

4. **create_jira_ticket** - Create a new Jira issue
   - Parameters:
     - `project_key`: Project key (e.g., 'PROJ')
     - `summary`: Issue title
     - `description`: Issue description
     - `issue_type` (optional): Story, Task, Epic, Bug (default: Story)
     - `priority` (optional): High, Medium, Low
     - `assignee` (optional): Username to assign to
     - `labels` (optional): List of labels

5. **add_comment_to_jira_ticket** - Add a comment to an existing issue
   - Parameters:
     - `issue_key`: The Jira issue key
     - `comment`: Comment text to add

6. **list_project_tickets** - List issues in a project with filtering
   - Parameters:
     - `project_key`: Project key
     - `status` (optional): Filter by status
     - `issue_type` (optional): Filter by issue type
     - `max_results` (optional): Maximum results (default: 50)
     - `instance_name` (optional): Name of the Jira instance to use

### Workflow Management

7. **transition_jira_issue** - Move an issue through its workflow
   - Parameters:
     - `issue_key`: The Jira issue key
     - `transition_name`: Name of the transition (e.g., "Start Progress", "Done")
     - `comment` (optional): Comment to add during transition
     - `instance_name` (optional): Name of the Jira instance to use

8. **get_issue_transitions** - Get available workflow transitions for an issue
   - Parameters:
     - `issue_key`: The Jira issue key
     - `instance_name` (optional): Name of the Jira instance to use

### Assignee Management

9. **change_issue_assignee** - Change the assignee of an issue
   - Parameters:
     - `issue_key`: The Jira issue key
     - `assignee` (optional): Username/email of new assignee (empty to unassign)
     - `instance_name` (optional): Name of the Jira instance to use

### Instance and Field Management

10. **list_jira_instances** - List all configured Jira instances
    - No parameters required

11. **get_custom_field_mappings** - Get mappings between custom field IDs and names
    - Parameters:
      - `reverse` (optional): If true, map from name to ID instead of ID to name

### Workflow Visualization

12. **generate_project_workflow_graph** - Generate visual workflow graph for a project
    - Parameters:
      - `project_key`: Project key (e.g., 'PROJ')
      - `issue_type` (optional): Issue type to analyze (default: "Story")
      - `format` (optional): Output format - "svg", "png", "dot", or "json" (default: "svg")
      - `instance_name` (optional): Name of the Jira instance to use

## Available Resources

1. **resource://jira/instances** - Information about all configured Jira instances

2. **resource://jira/project/{project_key}** - Information about a specific project
   - Parameters:
     - `project_key`: The project key to get information for

## Example Usage

### Basic Issue Management

```python
# List all projects
projects = await session.call_tool("list_jira_projects")

# Get issue details
issue = await session.call_tool("get_issue_details", {
    "issue_key": "PROJ-123"
})

# Create a new issue
new_issue = await session.call_tool("create_jira_ticket", {
    "project_key": "PROJ",
    "summary": "New feature request",
    "description": "Detailed description of the feature",
    "issue_type": "Story",
    "priority": "High",
    "assignee": "john.doe"
})
```

### Workflow Management

```python
# Check available transitions
transitions = await session.call_tool("get_issue_transitions", {
    "issue_key": "PROJ-123"
})

# Move issue to "In Progress"
result = await session.call_tool("transition_jira_issue", {
    "issue_key": "PROJ-123",
    "transition_name": "Start Progress",
    "comment": "Starting work on this issue"
})
```

### Multi-Instance Usage

```python
# List projects from a specific instance
projects = await session.call_tool("list_jira_projects", {
    "instance_name": "production"
})

# Get issue from staging instance
issue = await session.call_tool("get_issue_details", {
    "issue_key": "STAGE-456",
    "instance_name": "staging"
})
```

### Assignee Management

```python
# Assign issue to a user
result = await session.call_tool("change_issue_assignee", {
    "issue_key": "PROJ-123",
    "assignee": "jane.smith"
})

# Unassign issue
result = await session.call_tool("change_issue_assignee", {
    "issue_key": "PROJ-123",
    "assignee": ""  # Empty string to unassign
})
```

### Workflow Visualization

```python
# Generate SVG workflow graph
graph = await session.call_tool("generate_project_workflow_graph", {
    "project_key": "PROJ",
    "issue_type": "Story",
    "format": "svg"
})
# Returns base64-encoded SVG data

# Generate JSON workflow data
workflow_data = await session.call_tool("generate_project_workflow_graph", {
    "project_key": "PROJ",
    "issue_type": "Bug",
    "format": "json",
    "instance_name": "production"
})
# Returns structured workflow data with nodes and edges

# Generate DOT format for custom processing
dot_graph = await session.call_tool("generate_project_workflow_graph", {
    "project_key": "PROJ",
    "format": "dot"
})
# Returns DOT language representation
```

## Security Considerations

- Store Jira API tokens securely and never commit them to version control
- Use environment variables or secure secret management for production deployments
- Consider using HTTPS in production environments
- The container runs as a non-root user for improved security
- Regularly rotate API tokens

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your Jira URL, username, and API token
2. **Permission Errors**: Ensure your Jira user has appropriate permissions for the operations you're trying to perform
3. **Instance Not Found**: Check that the instance name matches exactly what's configured in `JIRA_INSTANCES`
4. **Transition Errors**: Use `get_issue_transitions` to see available transitions for an issue

### Debug Mode

Enable debug logging by setting:
```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## License

[MIT License](LICENSE)
