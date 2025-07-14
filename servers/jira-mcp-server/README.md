# Jira MCP Server

A comprehensive, standalone MCP (Model Context Protocol) server that provides seamless integration with Jira instances. This server enables AI assistants like Claude Desktop and Cline to interact with Jira projects, issues, and workflows through a rich set of tools and resources.

## 🚀 Features

- **🎯 Complete Jira Integration**: Connect to Jira Cloud or Server instances
- **📋 Issue Management**: Create, read, update, and comment on Jira issues
- **📊 Project Operations**: List projects, get project details, and manage project tickets
- **🔧 Custom Field Support**: Access and understand custom field mappings
- **🏥 Health Monitoring**: Built-in health checks and connection testing
- **🚀 Multiple Deployment Options**: Docker, Docker Compose, or local development
- **🐳 Standalone Docker**: No external dependencies or base images required
- **⚡ FastMCP Implementation**: Built on the modern FastMCP framework
- **🔒 Secure Authentication**: API token-based authentication with Jira
- **📝 Comprehensive Logging**: Configurable logging with debug support

## 📋 Prerequisites

- **Jira Access**: A Jira Cloud or Server instance with API access
- **Jira API Token**: Generated from your Jira account settings
- **Docker** (for containerized deployment) or **Python 3.13+** (for local development)
- **Network Access**: Ability to reach your Jira instance from where the server runs

## ⚠️ Important: Updating from Previous Versions

**If you're updating the Jira MCP server or encountering 404 errors on `/health`, you MUST rebuild the Docker image:**

```bash
# Stop current container
docker-compose -f docker/docker-compose.yml down

# Rebuild with latest code and dependencies
./docker/build.sh jira-mcp-server latest 7501

# Start updated container
docker-compose -f docker/docker-compose.yml up -d

# Test health endpoint
curl http://localhost:7501/health
```

> **Why rebuild?** Docker containers are immutable snapshots. Code changes, dependency updates, and new features require rebuilding the image to be included in the running container.

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone and navigate to the directory
cd servers/jira-mcp-server

# 2. Create environment file
cp .env.example .env
# Edit .env with your Jira credentials

# 3. Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# 4. Test the server
curl http://localhost:7501/health
```

**For first-time setup or after updates:**
```bash
# Build the image first (includes latest code and dependencies)
./docker/build.sh jira-mcp-server latest 7501

# Then start with compose
docker-compose -f docker/docker-compose.yml up -d
```

### Option 2: Local Development

```bash
# 1. Navigate to the directory
cd servers/jira-mcp-server

# 2. Run setup script
./scripts/setup.sh

# 3. Configure environment
cp .env.example .env
# Edit .env with your Jira credentials

# 4. Start the server
./scripts/run.sh sse

# 5. Test the server
curl http://localhost:7501/health
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# MCP Server identity
SERVER_NAME=jira-mcp-server

# Server settings
HOST=0.0.0.0
PORT=7501

# API key for MCP client authentication
API_KEY=your_secure_api_key_here

# Jira settings (REQUIRED)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER=your-jira-email@example.com
JIRA_TOKEN=your-jira-api-token

# Logging configuration
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Getting Jira API Token

1. Go to your Jira instance → Profile → Personal Access Tokens (Cloud) or API Tokens (Server)
2. Create a new token with appropriate permissions
3. Save the token securely - you'll need it for configuration

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop
docker-compose -f docker/docker-compose.yml down
```

### Using Docker Build Scripts

```bash
# Build the image
./docker/build.sh jira-mcp-server latest 7501

# Run the container
./docker/run.sh -d
```

### Manual Docker Commands

```bash
# Build
docker build -t jira-mcp-server:latest -f docker/Dockerfile .

# Run
docker run -p 7501:7501 --env-file .env jira-mcp-server:latest
```

## 💻 Local Development

### Setup

```bash
# Run the setup script
./scripts/setup.sh

# This will:
# - Check Python version (3.13+ required)
# - Create virtual environment
# - Install dependencies
# - Create .env file from template
```

### Virtual Environment Activation

After running the setup script, you must activate the virtual environment before running any Python scripts directly:

```bash
# Navigate to the project directory
cd servers/jira-mcp-server

# Activate the virtual environment
source .venv/bin/activate

# Now you can run Python scripts directly
python3 test_health.py
```

**Important Notes:**
- The `./scripts/run.sh` script automatically handles virtual environment activation
- Direct Python script execution (like `python3 test_health.py`) requires manual activation
- You'll see `(jira-mcp-server)` in your terminal prompt when the virtual environment is active
- To deactivate the virtual environment, simply run: `deactivate`

### Running

```bash
# HTTP+SSE server (for network clients)
./scripts/run.sh sse

# Stdio server (for local development)
./scripts/run.sh stdio

# Using custom environment file
./scripts/run.sh --env /path/to/custom.env sse
./scripts/run.sh --env .env.prod stdio

# Show help
./scripts/run.sh help
```

**New `--env` Option:**
- Specify a custom environment file path
- Server validates all required variables are present
- Will "halt and catch fire" 🔥 if any required variables are missing
- Supports both relative and absolute paths

## 🔌 MCP Client Integration

### Cline (VS Code)

1. Start the server:
   ```bash
   ./scripts/run.sh sse
   # or
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. Edit Cline MCP settings file:
   ```json
   {
     "mcpServers": {
       "jira-mcp-server": {
         "url": "http://localhost:7501/sse",
         "apiKey": "your_secure_api_key_here",
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```

### Claude Desktop

Claude Desktop requires the `command`/`args` format and cannot connect directly to HTTP servers. It will launch its own stdio instance of the server.

1. Ensure the server code is available locally (no need to run the Docker container for Claude Desktop)

2. Add to Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
   ```json
   {
     "mcpServers": {
       "jira-mcp-server": {
         "command": "/path/to/your/BaseMcpServer/servers/jira-mcp-server/scripts/run.sh",
         "args": [
           "--env",
           "/path/to/your/BaseMcpServer/servers/jira-mcp-server/.env",
           "stdio"
         ]
       }
     }
   }
   ```

   **Important Notes:**
   - Replace `/path/to/your/BaseMcpServer` with the actual path to your project
   - The `--env` argument specifies the path to your environment file
   - All environment variables are read from the `.env` file
   - The server will "halt and catch fire" 🔥 if required variables are missing
   - Claude Desktop launches its own stdio instance, separate from any Docker containers

3. **Required Environment Variables** (must be in your `.env` file):
   - `JIRA_URL` - Your Jira instance URL
   - `JIRA_USER` - Your Jira username/email
   - `JIRA_TOKEN` - Your Jira API token
   - `SERVER_NAME` - MCP server name
   - `API_KEY` - Authentication key for MCP clients

4. Restart Claude Desktop to apply the configuration

## 🛠️ Available Tools

### Core Jira Operations

#### 1. `jira_get_issue` / `get_issue_details`
Get details of a specific Jira issue.

**Parameters**:
- `issue_key` (string): The Jira issue key (e.g., 'PROJ-123')

**Returns**: Issue details including summary, status, assignee, description, etc.

#### 2. `jira_search`
Search issues using JQL (Jira Query Language).

**Parameters**:
- `jql` (string): The JQL query string (e.g., "project = PROJ AND status = 'In Progress'")
- `max_results` (integer, optional): Maximum number of results to return (default: 50)
- `start_at` (integer, optional): Starting index for pagination (default: 0)

**Returns**: Search results with issue list and metadata.

#### 3. `jira_create_issue` / `create_jira_ticket`
Create a new Jira issue.

**Parameters**:
- `project_key` (string): The project key (e.g., 'PROJ')
- `summary` (string): The issue summary/title
- `description` (string): The issue description
- `issue_type` (string, optional): Issue type - "Story", "Task", "Epic", "Bug" (default: "Story")
- `priority` (string, optional): Priority level (e.g., "High", "Medium", "Low")
- `assignee` (string, optional): Username to assign the issue to
- `labels` (array, optional): List of labels to apply

**Returns**: Created issue details with key, ID, and URL.

#### 4. `jira_update_issue`
Update an existing Jira issue.

**Parameters**:
- `issue_key` (string): The Jira issue key (e.g., 'PROJ-123')
- `summary` (string, optional): New summary/title
- `description` (string, optional): New description
- `priority` (string, optional): New priority (e.g., "High", "Medium", "Low")
- `assignee` (string, optional): New assignee username
- `labels` (array, optional): New list of labels (replaces existing labels)

**Returns**: Update status and list of updated fields.

#### 5. `jira_transition_issue`
Transition an issue to a new status.

**Parameters**:
- `issue_key` (string): The Jira issue key (e.g., 'PROJ-123')
- `transition_name` (string): The name of the transition (e.g., "In Progress", "Done", "Close Issue")
- `comment` (string, optional): Optional comment to add during the transition

**Returns**: Transition status with before/after status confirmation.

#### 6. `jira_add_comment` / `add_comment_to_jira_ticket`
Add a comment to a Jira issue.

**Parameters**:
- `issue_key` (string): The Jira issue key (e.g., 'PROJ-123')
- `comment` (string): The comment text to add

**Returns**: Comment details and status confirmation.

### Additional Tools

#### 7. `health_check`
Check the health of the Jira MCP server and its connection to Jira.

**Parameters**: None

**Returns**: Server status, Jira connection status, and configuration info.

#### 8. `list_jira_projects`
List all projects available in your Jira instance.

**Parameters**: None

**Returns**: Array of projects with key, name, and ID.

#### 9. `get_full_issue_details`
Get comprehensive issue information with formatting options and comments.

**Parameters**:
- `issue_key` (string): The Jira issue key
- `raw_data` (boolean, optional): Return raw API data if true (default: false)
- `format` (string, optional): "formatted" or "summary" (default: "formatted")

**Returns**: Comprehensive issue data including comments, custom fields, and metadata.

#### 10. `get_custom_field_mappings`
Get mappings between Jira custom field IDs and their human-readable names.

**Parameters**:
- `reverse` (boolean, optional): If true, map from name to ID; if false, map from ID to name (default: false)

**Returns**: Dictionary of custom field mappings with descriptions.

#### 11. `list_project_tickets`
List tickets (issues) in a Jira project with optional filtering.

**Parameters**:
- `project_key` (string): The project key
- `status` (string, optional): Filter by status (e.g., "In Progress", "Done")
- `issue_type` (string, optional): Filter by issue type (e.g., "Story", "Bug")
- `max_results` (integer, optional): Maximum results to return (default: 50)

**Returns**: List of matching tickets with key details.

## 📚 Available Resources

### 1. Project Resource
**URI Template**: `resource://jira/project/{project_key}`

Get detailed information about a specific Jira project.

**Example**: `resource://jira/project/MYPROJ`

### 2. Jira Instances Resource
**URI**: `resource://jira/instances`

Get information about configured Jira instances.

## 📖 Usage Examples

### Basic Issue Operations

```python
# List all projects
projects = await session.call_tool("list_jira_projects", {})

# Get issue details
issue = await session.call_tool("jira_get_issue", {
    "issue_key": "PROJ-123"
})

# Search for issues using JQL
search_results = await session.call_tool("jira_search", {
    "jql": "project = PROJ AND status = 'In Progress'",
    "max_results": 20
})

# Create a new issue
new_issue = await session.call_tool("jira_create_issue", {
    "project_key": "PROJ",
    "summary": "Fix login bug",
    "description": "Users cannot log in with special characters in password",
    "issue_type": "Bug",
    "priority": "High",
    "labels": ["urgent", "security"]
})

# Update an existing issue
update_result = await session.call_tool("jira_update_issue", {
    "issue_key": "PROJ-123",
    "summary": "Updated: Fix login bug with special characters",
    "priority": "Critical",
    "assignee": "john.doe"
})

# Transition an issue to a new status
transition_result = await session.call_tool("jira_transition_issue", {
    "issue_key": "PROJ-123",
    "transition_name": "In Progress",
    "comment": "Starting work on this issue"
})

# Add a comment
comment = await session.call_tool("jira_add_comment", {
    "issue_key": "PROJ-123",
    "comment": "Investigation shows this is related to password validation regex"
})
```

### Health Monitoring

```python
# Check server health
health = await session.call_tool("health_check", {})
print(f"Server status: {health['server_status']}")
print(f"Jira connected: {health['jira_connection']['connected']}")
```

## 🏥 Health Monitoring

The Jira MCP server includes comprehensive health monitoring capabilities:

### Health Endpoint

The server exposes a `/health` endpoint that provides detailed status information:

```bash
# Test the health endpoint
curl http://localhost:7501/health

# Or use the provided test script (requires virtual environment activation)
source .venv/bin/activate
python3 test_health.py
```

### Health Response Format

**Healthy Response (HTTP 200)**:
```json
{
  "status": "healthy",
  "server_name": "jira-mcp-server",
  "jira_connection": {
    "connected": true,
    "server_title": "Your Jira Instance",
    "version": "9.x.x",
    "build_number": "xxxxx",
    "base_url": "https://your-domain.atlassian.net",
    "timestamp": "2025-07-07T15:20:00.000Z"
  },
  "timestamp": "2025-07-07T15:20:00.000Z"
}
```

**Unhealthy Response (HTTP 503)**:
```json
{
  "status": "unhealthy",
  "server_name": "jira-mcp-server",
  "jira_connection": {
    "connected": false,
    "error": "Connection error details",
    "configured_url": "https://your-domain.atlassian.net",
    "configured_user": "your-email@example.com",
    "timestamp": "2025-07-07T15:20:00.000Z"
  },
  "error": "Error details"
}
```

### Docker Health Checks

The Docker container includes automatic health checks:
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts before marking unhealthy
- **Start Period**: 10 seconds initial grace period

Check container health status:
```bash
# View container health status
docker ps

# View health check logs
docker inspect jira-mcp-server | grep -A 10 Health
```

## 🔍 Troubleshooting

### Common Issues

**1. Health Check Failures**
```
INFO: 127.0.0.1:35246 - "GET /health HTTP/1.1" 404 Not Found
```
- This was fixed in the latest version - rebuild your Docker image
- Run `./docker/build.sh` to get the updated version with health endpoint

**2. Authentication Errors**
```
Error: Failed to create JIRA client: HTTP 401
```
- Verify your `JIRA_USER` and `JIRA_TOKEN` are correct
- Ensure the API token has appropriate permissions
- Check if your Jira instance requires additional authentication

**3. Connection Errors**
```
Error: Failed to create JIRA client: Connection timeout
```
- Verify `JIRA_URL` is correct and accessible
- Check network connectivity to Jira instance
- Ensure firewall/proxy settings allow the connection

**4. Docker Build Issues**
```
Error: Docker image not found
```
- Run `./docker/build.sh` to build the image first
- Check Docker is running and accessible

**5. Permission Errors**
```
Error: You do not have permission to view this issue
```
- Verify your Jira user has appropriate project permissions
- Check if the issue exists and is accessible to your user

**6. ModuleNotFoundError (requests, etc.)**
```
Error: ModuleNotFoundError: No module named 'requests'
```
- You need to activate the virtual environment first: `source .venv/bin/activate`
- Or use the run script which handles this automatically: `./scripts/run.sh sse`
- Ensure dependencies are installed: `pip install -r requirements.txt`
- Verify you're in the correct directory: `cd servers/jira-mcp-server`

### Debug Mode

Enable debug logging:
```bash
# In .env file
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### Health Check Testing

Test server connectivity and health:
```bash
# Quick health check
curl http://localhost:7501/health

# Detailed health test with retry logic
python3 test_health.py

# Docker container health check
docker exec jira-mcp-server curl http://localhost:7501/health

# View container health status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Rebuilding After Updates

If you encounter health check issues, rebuild the container:
```bash
# Stop current container
docker-compose -f docker/docker-compose.yml down

# Rebuild with latest fixes
./docker/build.sh jira-mcp-server latest 7501

# Start updated container
docker-compose -f docker/docker-compose.yml up -d

# Test health endpoint
python3 test_health.py
```

## 🔄 Updating the Server

### When to Rebuild

You **MUST** rebuild the Docker image when:
- ✅ Updating to a newer version of the server
- ✅ Code changes have been made to source files
- ✅ Dependencies have been updated in `requirements.txt`
- ✅ You're getting 404 errors on `/health` endpoint
- ✅ New features or bug fixes have been added

### Update Workflow

```bash
# 1. Stop current container
cd servers/jira-mcp-server
docker-compose -f docker/docker-compose.yml down

# 2. Pull latest changes (if using git)
git pull origin main

# 3. Rebuild Docker image with latest code
./docker/build.sh jira-mcp-server latest 7501

# 4. Start updated container
docker-compose -f docker/docker-compose.yml up -d

# 5. Verify health endpoint works
curl http://localhost:7501/health
python3 test_health.py

# 6. Check container logs for any issues
docker-compose -f docker/docker-compose.yml logs -f
```

### Why Rebuilding is Required

Docker containers are **immutable snapshots**:
- Running containers use the image that was built at a specific point in time
- Code changes on your filesystem don't automatically appear in running containers
- New dependencies or fixes require rebuilding the image to be included
- `docker-compose up` reuses existing images unless you rebuild

### Quick Rebuild Command

For convenience, you can use this one-liner to rebuild and restart:
```bash
docker-compose -f docker/docker-compose.yml down && ./docker/build.sh jira-mcp-server latest 7501 && docker-compose -f docker/docker-compose.yml up -d
```

## 🏗️ Development & Customization

### Project Structure

```
servers/jira-mcp-server/
├── src/                     # Application source code
│   ├── __init__.py
│   ├── config.py            # Configuration and environment handling
│   ├── main.py              # Entry point and server setup
│   └── server.py            # MCP tools and resources implementation
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Standalone container definition
│   ├── build.sh             # Docker build script
│   ├── run.sh               # Docker run script
│   └── docker-compose.yml   # Compose configuration
├── scripts/                 # Local development scripts
│   ├── setup.sh             # Development environment setup
│   └── run.sh               # Local server execution
├── .env.example             # Environment variables template
├── .dockerignore            # Docker ignore file
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── LICENSE                  # License file
```

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

## 🔒 Security Considerations

- **API Token Security**: Store Jira API tokens securely, never commit them to version control
- **Network Security**: Use HTTPS for Jira connections in production
- **Access Control**: Ensure the Jira user has minimal required permissions
- **MCP Authentication**: Set a strong `API_KEY` for MCP client authentication
- **Container Security**: The Docker container runs as a non-root user
- **Resource Limits**: Docker Compose includes memory and CPU limits

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review the MCP documentation: https://modelcontextprotocol.io
- Open an issue in the repository

---

**Built with ❤️ for the MCP Community**
