# Jira Helper MCP Server

A comprehensive MCP (Model Context Protocol) server that provides seamless integration with Jira instances. This server enables AI assistants to interact with Jira projects, issues, and workflows through a rich set of tools and resources.

## Features

- **🎯 Complete Jira Integration**: Connect to Jira Cloud or Server instances
- **📋 Issue Management**: Create, read, update, and comment on Jira issues
- **📊 Project Operations**: List projects, get project details, and manage project tickets
- **🔧 Custom Field Support**: Access and understand custom field mappings
- **🚀 Dual Transport Support**: HTTP+SSE for network use, stdio for local development
- **🐳 Docker Ready**: Fully containerized with base image support
- **⚡ FastMCP Implementation**: Built on the modern FastMCP framework
- **🔒 Secure Authentication**: API token-based authentication with Jira

## Prerequisites

- **Jira Access**: A Jira Cloud or Server instance with API access
- **Jira API Token**: Generated from your Jira account settings
- **Python 3.13+** (for local development) or **Docker** (for containerized deployment)
- **Network Access**: Ability to reach your Jira instance from where the server runs

## Quick Start

### 1. Get Jira API Token

1. Go to your Jira instance → Profile → Personal Access Tokens (Cloud) or API Tokens (Server)
2. Create a new token with appropriate permissions
3. Save the token securely - you'll need it for configuration

### 2. Local Development Setup

```bash
# Clone and navigate to the jira-helper directory
cd servers/jira-helper

# Run the setup script (creates venv and installs dependencies)
./setup.sh

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your Jira credentials (see Configuration section)

# Start the server
./run.sh sse    # For HTTP+SSE transport
# or
./run.sh stdio  # For stdio transport
```

### 3. Docker Setup

```bash
# Build the Docker image (requires base image - see Prerequisites)
./docker/build.sh jira-helper-server latest 7501 <your-docker-username>

# Run with environment variables
docker run -p 7501:7501 \
  -e JIRA_URL=https://your-domain.atlassian.net \
  -e JIRA_USER=your-email@example.com \
  -e JIRA_TOKEN=your-api-token \
  jira-helper-server:latest
```

## Installation & Setup

### Local Development Setup

The local setup uses Python virtual environments and shell scripts for easy development:

```bash
# 1. Run the setup script
./setup.sh

# This script will:
# - Create a Python 3.13+ virtual environment in .venv/
# - Install all required dependencies from requirements.txt
# - Provide setup completion instructions
```

### Docker Setup

The Docker setup builds upon the BaseMcpServer base image:

```bash
# 1. Ensure you have the base image built (from project root)
./base-mcp-docker/build.sh base-mcp-server latest 7501 <your-docker-username>

# 2. Build the Jira helper server
./servers/jira-helper/docker/build.sh jira-helper-server latest 7501 <your-docker-username>

# 3. Run the container
docker run -p 7501:7501 --env-file .env jira-helper-server:latest
```

### Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
# MCP Server identity
SERVER_NAME=jira-helper-server

# Server settings (for HTTP+SSE transport)
HOST=0.0.0.0
PORT=7501

# API key for MCP client authentication (used by Claude Desktop, Cline, etc.)
API_KEY=your_secure_api_key_here

# Jira settings (REQUIRED)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER=your-jira-email@example.com
JIRA_TOKEN=your-jira-api-token
```

**Important**: Replace the placeholder values with your actual Jira credentials.

## Available Tools

### 1. `list_jira_projects`
List all projects available in your Jira instance.

**Parameters**: None

**Returns**: 
```json
{
  "projects": [
    {
      "key": "PROJ",
      "name": "Project Name",
      "id": "12345"
    }
  ]
}
```

### 2. `get_issue_details`
Get detailed information about a specific Jira issue.

**Parameters**:
- `issue_key` (string): The Jira issue key (e.g., 'PROJ-123')

**Returns**: Issue details including summary, status, assignee, description, etc.

### 3. `get_full_issue_details`
Get comprehensive issue information with formatting options and comments.

**Parameters**:
- `issue_key` (string): The Jira issue key
- `raw_data` (boolean, optional): Return raw API data if true (default: false)
- `format` (string, optional): "formatted" or "summary" (default: "formatted")

**Returns**: Comprehensive issue data including comments, custom fields, and metadata.

### 4. `create_jira_ticket`
Create a new Jira ticket (issue).

**Parameters**:
- `project_key` (string): The project key (e.g., 'PROJ')
- `summary` (string): The ticket summary/title
- `description` (string): The ticket description
- `issue_type` (string, optional): Issue type - "Story", "Task", "Epic", "Bug" (default: "Story")
- `priority` (string, optional): Priority level (e.g., "High", "Medium", "Low")
- `assignee` (string, optional): Username to assign the ticket to
- `labels` (array, optional): List of labels to apply

**Returns**: Created issue details with key, ID, and URL.

### 5. `add_comment_to_jira_ticket`
Add a comment to an existing Jira ticket.

**Parameters**:
- `issue_key` (string): The Jira issue key
- `comment` (string): The comment text to add

**Returns**: Comment details and status confirmation.

### 6. `get_custom_field_mappings`
Get mappings between Jira custom field IDs and their human-readable names.

**Parameters**:
- `reverse` (boolean, optional): If true, map from name to ID; if false, map from ID to name (default: false)

**Returns**: Dictionary of custom field mappings with descriptions.

### 7. `list_project_tickets`
List tickets (issues) in a Jira project with optional filtering.

**Parameters**:
- `project_key` (string): The project key
- `status` (string, optional): Filter by status (e.g., "In Progress", "Done")
- `issue_type` (string, optional): Filter by issue type (e.g., "Story", "Bug")
- `max_results` (integer, optional): Maximum results to return (default: 50)

**Returns**: List of matching tickets with key details.

## Available Resources

### 1. Project Resource
**URI Template**: `resource://jira/project/{project_key}`

Get detailed information about a specific Jira project.

**Example**: `resource://jira/project/MYPROJ`

### 2. Jira Instances Resource
**URI**: `resource://jira/instances`

Get information about configured Jira instances.

## Usage Examples

### Basic Issue Operations

```python
# List all projects
projects = await session.call_tool("list_jira_projects", {})

# Get issue details
issue = await session.call_tool("get_issue_details", {
    "issue_key": "PROJ-123"
})

# Create a new ticket
new_ticket = await session.call_tool("create_jira_ticket", {
    "project_key": "PROJ",
    "summary": "Fix login bug",
    "description": "Users cannot log in with special characters in password",
    "issue_type": "Bug",
    "priority": "High",
    "labels": ["urgent", "security"]
})

# Add a comment
comment = await session.call_tool("add_comment_to_jira_ticket", {
    "issue_key": "PROJ-123",
    "comment": "Investigation shows this is related to password validation regex"
})
```

### Project Management

```python
# List tickets in a project
tickets = await session.call_tool("list_project_tickets", {
    "project_key": "PROJ",
    "status": "In Progress",
    "max_results": 20
})

# Get project information via resource
project_info = await session.access_resource("resource://jira/project/PROJ")
```

### Custom Fields

```python
# Get custom field mappings
field_mappings = await session.call_tool("get_custom_field_mappings", {})

# Get comprehensive issue details with custom fields
full_details = await session.call_tool("get_full_issue_details", {
    "issue_key": "PROJ-123",
    "format": "formatted"
})
```

## MCP Client Integration

### Claude Desktop Integration

1. Start the server with SSE transport:
   ```bash
   ./run.sh sse
   ```

2. Add to Claude Desktop settings:
   ```json
   {
     "mcpServers": {
       "jira-helper": {
         "url": "http://localhost:7501",
         "apiKey": "your_api_key_here"
       }
     }
   }
   ```

### Cline (VS Code) Integration

1. Start the server:
   ```bash
   ./run.sh sse
   ```

2. Edit Cline MCP settings file:
   ```json
   {
     "mcpServers": {
       "jira-helper-server": {
         "url": "http://localhost:7501/sse",
         "apiKey": "your_api_key_here",
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVER_NAME` | MCP server identifier | `jira-helper-server` | No |
| `HOST` | Server host address | `0.0.0.0` | No |
| `PORT` | Server port | `7501` | No |
| `API_KEY` | MCP client authentication key (for Claude Desktop, Cline, etc.) | `example_key` | No |
| `JIRA_URL` | Jira instance URL | - | **Yes** |
| `JIRA_USER` | Jira username/email | - | **Yes** |
| `JIRA_TOKEN` | Jira API token | - | **Yes** |

### Jira URL Formats

- **Jira Cloud**: `https://your-domain.atlassian.net`
- **Jira Server**: `https://jira.your-company.com`
- **Jira Data Center**: `https://jira.your-company.com`

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: Failed to create JIRA client: HTTP 401
```
- Verify your `JIRA_USER` and `JIRA_TOKEN` are correct
- Ensure the API token has appropriate permissions
- Check if your Jira instance requires additional authentication

**2. Connection Errors**
```
Error: Failed to create JIRA client: Connection timeout
```
- Verify `JIRA_URL` is correct and accessible
- Check network connectivity to Jira instance
- Ensure firewall/proxy settings allow the connection

**3. Permission Errors**
```
Error: You do not have permission to view this issue
```
- Verify your Jira user has appropriate project permissions
- Check if the issue exists and is accessible to your user

**4. Custom Field Issues**
- Use `get_custom_field_mappings` to understand available custom fields
- Custom field access depends on your Jira configuration and permissions

### Debug Mode

Enable debug logging by setting environment variables:
```bash
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
```

## Development & Customization

### Adding New Tools

To add a new Jira tool, edit `src/server.py` within the `register_tools_and_resources` function:

```python
@srv.tool()
def my_custom_jira_tool(issue_key: str, custom_param: str) -> Dict[str, Any]:
    """
    Description of your custom tool.
    
    Args:
        issue_key: The Jira issue key
        custom_param: Description of custom parameter
        
    Returns:
        Dictionary with results
    """
    try:
        jira = create_jira_client()
        # Your custom logic here
        return {"result": "success"}
    except Exception as e:
        return {"error": str(e)}
```

### Adding New Resources

```python
@srv.resource("resource://jira/custom/{param}")
def custom_resource(param: str) -> Dict[str, Any]:
    """Custom resource description"""
    jira = create_jira_client()
    # Fetch and return resource data
    return {"data": "resource_data"}
```

### Project Structure

```
servers/jira-helper/
├── src/                     # Application source code
│   ├── __init__.py
│   ├── config.py            # Configuration and environment handling
│   ├── main.py              # Entry point and server setup
│   └── server.py            # MCP tools and resources implementation
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Container definition
│   └── build.sh             # Docker build script
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── setup.sh                 # Local development setup script
├── run.sh                   # Server execution script
└── README.md                # This file
```

## Security Considerations

- **API Token Security**: Store Jira API tokens securely, never commit them to version control
- **Network Security**: Use HTTPS for Jira connections in production
- **Access Control**: Ensure the Jira user has minimal required permissions
- **MCP Authentication**: Set a strong `API_KEY` for MCP client authentication (this is what Claude Desktop, Cline, and other MCP clients use to authenticate with your server)
- **Container Security**: The Docker container runs as a non-root user

## License

[MIT License](LICENSE)

---

For more information about the Model Context Protocol, visit: https://modelcontextprotocol.io
