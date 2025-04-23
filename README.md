# BaseMcpServer

A minimal containerized base for MCP servers using the MCP Python SDK.

## Overview

BaseMcpServer provides a standardized Docker base image for building Model Context Protocol (MCP) servers. It is:

- **Simple**: Designed as a minimal implementation using the MCP Python SDK
- **Containerized**: Built specifically for Docker deployment
- **Protocol-specific**: Uses both HTTP+SSE and stdio protocols
- **Reusable**: Serves as a foundation for derived MCP server implementations

This image provides all the common dependencies and configuration needed for MCP servers, so that derived projects can focus solely on implementing their specific tools and resources.

## Local Development

For local development without Docker, each MCP server includes setup scripts to create and manage Python virtual environments with the necessary dependencies.

### Prerequisites

- Python 3.13+ installed (recommended)
- Git (to clone this repository)

### Using Setup and Run Scripts

Each MCP server includes two shell scripts for easy setup and execution:

#### 1. Setup Script

The `setup.sh` script creates a virtual environment and installs all dependencies:

```bash
# Navigate to the desired MCP server directory
cd example/

# Run the setup script
./setup.sh
```

This will:
- Create a `.venv` directory with a Python virtual environment
- Install all required dependencies from `requirements.txt`
- Configure the environment for local development

#### 2. Run Script

The `run.sh` script activates the virtual environment and runs the MCP server:

```bash
# Start with SSE protocol (for Claude/Cline integration)
./run.sh sse

# Or start with stdio protocol (for direct stdin/stdout communication)
./run.sh stdio
```

### Manual Setup (If Scripts Don't Work)

If the scripts don't work on your system, you can manually set up the environment:

```bash
# Navigate to the desired MCP server directory
cd example/

# Create a virtual environment
python3.13 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH and run the server
export PYTHONPATH="$PWD/src:$PYTHONPATH"  # On Windows: set PYTHONPATH=%CD%\src;%PYTHONPATH%
cd src
python main.py sse  # Or: python main.py stdio
```

### Virtual Environment Structure

The virtual environment approach:
- Creates an isolated Python environment for each MCP server
- Installs only the dependencies needed for that specific server
- Allows for easy activation/deactivation
- Sets the correct PYTHONPATH automatically
- Provides a consistent environment across different systems

## Best Practices for Custom MCP Servers

When creating custom MCP servers based on this template, follow these best practices to avoid common issues:

### Port Configuration

1. **Use the Correct Ports**: The base image exposes port `7501`. Always align your configuration with this port:
   - In the `.env` file, set `PORT=7501`
   - When running the container, map the external port to 7501: `docker run -p EXTERNAL_PORT:7501`
   - In the VSCode/Claude settings, use the external port with the SSE suffix: `"url": "http://localhost:EXTERNAL_PORT/sse"`

2. **Consistent Port Usage**: Be consistent with your port numbering. If you choose external port 7777:
   - Docker command: `docker run -p 7777:7501`
   - VSCode/Claude settings: `"url": "http://localhost:7777/sse"`

3. **Port Conflicts**: If you get connection errors, check for port conflicts with `lsof -i :PORT_NUMBER`

### Environment Variables

1. **Mounting vs. Copying**: For development, you can copy the `.env` file into the container:
   ```dockerfile
   COPY ./.env ./.env
   ```
   For production, mount it at runtime:
   ```bash
   docker run -p 7777:7501 --env-file .env your-image
   ```

2. **Robust Config Loading**: Implement robust environment variable loading with logging and fallbacks:
   ```python
   # Add logging of loaded configuration values
   logger.info(f"JIRA_URL: {settings.JIRA_URL}")
   logger.info(f"Using port: {settings.port}")
   ```

3. **Verify Environment**: Use explicit validation of required environment variables with clear error messages

### Connecting to Claude/Cline

To connect your MCP server to Claude Desktop or Cline in VS Code:

1. First make sure your MCP server is running with the sse transport:
   ```bash
   ./run.sh sse  # For local development
   ```
   or
   ```bash
   docker run -p 7501:7501 your-image  # For Docker
   ```

2. For Cline in VS Code, edit the settings file:
   
   Path: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   
   Example configuration:
   ```json
   {
     "mcpServers": {
       "example-mcp-server": {
         "url": "http://localhost:7501/sse",
         "apiKey": "example_key",
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```
   
   Notes:
   - Use the correct server name from config.py (server_name setting)
   - Ensure the port matches your configuration (default is 7501)
   - Include "/sse" at the end of the URL
   - The apiKey should match the one in your .env file
   
3. For Claude Desktop, go to:
   Settings → Advanced → MCP Servers → Add MCP Server
   
   Enter:
   - Name: example-mcp-server (or your custom server name)
   - URL: http://localhost:7501
   - API Key: example_key (or your custom API key)

4. Restart Claude/VS Code to apply the changes

### VS Code Integration

1. **Restart VS Code When Needed**: If you encounter connection issues with Claude trying to access your MCP server, try:
   - Restarting VS Code completely
   - Checking the Claude MCP settings file for proper configuration
   - Ensuring the server is running and accessible via the correct port

2. **Clear Connection Errors**: When you see "Not connected" errors from Claude, it usually indicates:
   - Port configuration mismatch
   - The server isn't running
   - VS Code needs to be restarted to refresh the connection

3. **Check Claude's MCP Settings**: Ensure Claude's MCP settings file (`~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`) has the correct entry for your server

### Debugging Techniques

1. **Add Detailed Logging**: Enhance logging, especially for configuration and initialization:
   ```python
   logger.info(f"Starting MCP server on {settings.host}:{settings.port}")
   logger.info(f"Using API key: {'Yes' if settings.api_key else 'No'}")
   ```

2. **Check Server Logs**: Always check the Docker container logs with `docker logs CONTAINER_ID`

3. **Verify Docker Container**: Use `docker ps` to ensure your container is running and the port mapping is correct

### Testing Approach

1. **Incremental Development**: Start with a known working example (like the example server)
2. **Make Small Changes**: Make one change at a time and test after each change
3. **Test Core Functionality**: Test with simple tools like the calculator before adding complex integrations
4. **Examine Error Messages**: Pay close attention to error messages in both the server logs and Claude's responses

For more detailed debugging notes, see `debugging_notes.md` in the project root.

## Key Features

- Python 3.13 environment with all MCP SDK dependencies pre-installed
- Multi-stage Docker build for optimized image size
- Non-root user for improved security
- HTTP+SSE protocol support via Starlette and Uvicorn
- Environment variable configuration via pydantic-settings
- Local development support with virtual environments
- Dual transport support (HTTP+SSE and stdio)

## Usage

### Building the Base Image

```bash
./build.sh base-mcp-server latest 7501 <your-docker-username>
```

Parameters:
- `base-mcp-server`: Image name (default)
- `latest`: Tag (default)
- `7501`: Port to expose (default)
- `<your-docker-username>`: **Required** - Your Docker Hub username

This will:
1. Build the base image
2. Tag it for Docker Hub
3. Push it to Docker Hub if you're logged in

### Using the Base Image in Derived Projects

In your Dockerfile:

```dockerfile
# Define build argument for Docker Hub username
ARG DOCKER_USERNAME

# Use the base MCP server image from Docker Hub
FROM docker.io/${DOCKER_USERNAME}/base-mcp-server:latest

# Copy your application code
COPY ./src ./src

# Set PYTHONPATH to include src as a sources root
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Set working directory to src
WORKDIR /app/src

# Command to run your MCP server with sse transport
CMD ["python", "main", "sse"]
```

## Technical Details

### Protocol Support

BaseMcpServer now supports both HTTP+SSE and stdio protocols:

- **HTTP+SSE**: Ideal for containerized deployments and network-based integrations
- **stdio**: Useful for local development and direct integration with command-line tools

#### What is HTTP+SSE in MCP?

HTTP+SSE (Server-Sent Events) is one of the standard transports supported by the MCP protocol:

- **HTTP**: Used for client-to-server communication (requests)
- **SSE**: Used for server-to-client communication (responses and events)

HTTP+SSE is designed for networked environments, making it ideal for:

- Web-based LLM integrations
- Service-to-service MCP communication
- Containerized deployments (like this one)
- Cloud environments

#### What is stdio in MCP?

The stdio transport uses standard input/output streams for communication:

- **stdin**: Used for receiving client requests
- **stdout**: Used for sending server responses

This transport is primarily used for:

- Local development
- Direct integration with command-line tools
- Desktop applications that can spawn processes

#### Implementation Details

This base image uses:
- **Starlette**: A lightweight ASGI framework that handles the HTTP+SSE protocol
- **Uvicorn**: An ASGI server that serves the Starlette application
- **Native Python I/O**: For stdio transport mode

The implementation is provided by the MCP Python SDK through:
- The `.sse_app()` method for HTTP+SSE
- Direct `run("stdio")` support for stdio mode

#### Mounting the MCP Server

When extending this base image, your MCP server is automatically served via HTTP+SSE. For more advanced scenarios where you need to integrate with existing web services, you can mount the MCP server to an existing ASGI application:

```python
from starlette.applications import Starlette
from starlette.routing import Mount, Host
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")

# Mount the MCP server to an existing ASGI application
app = Starlette(
    routes=[
        Mount('/mcp', app=mcp.sse_app()),
    ]
)

# Or mount it as a subdomain
app.router.routes.append(Host('mcp.example.com', app=mcp.sse_app()))
```

#### Security Considerations

When using HTTP+SSE in production:
- Always use HTTPS in production environments
- Consider implementing authentication for the HTTP endpoints
- If exposing your MCP server publicly, use API keys or other authentication mechanisms
- Implement rate limiting for public-facing servers

### Python SDK Implementation

The image directly uses the MCP Python SDK with minimal abstraction:

- FastMCP for ergonomic tool definitions
- Built-in schema generation based on Python type hints
- Automatic validation of input/output formats
- Support for both HTTP+SSE and stdio transport modes

### Environment Variables and Configuration

The base image supports configuration through environment variables, which can be passed to derived images in several ways:

#### Available Environment Variables

- `HOST`: Interface to bind to (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 7501)
- `API_KEY`: Required for authentication (must be provided)
- `SERVER_NAME`: Unique identifier for your MCP server
- Any additional environment variables required by your specific implementation

#### Configuration Methods for Derived Images

##### 1. Using Command Line Environment Variables

```bash
docker run -p 7501:7501 \
  -e API_KEY=your_api_key \
  -e SERVER_NAME=your-mcp-server \
  yourdockerusername/your-mcp-server:latest
```

##### 2. Using an Environment File

Create a `.env` file with your configuration:

```
API_KEY=your_api_key
SERVER_NAME=your-mcp-server
HOST=0.0.0.0
PORT=7501
```

Then run with:

```bash
docker run -p 7501:7501 --env-file .env yourdockerusername/your-mcp-server:latest
```

##### 3. Using Docker Secrets (for Docker Swarm)

For production deployments using Docker Swarm:

```bash
echo "your_api_key" | docker secret create api_key -
echo "your_server_name" | docker secret create server_name -

docker service create \
  --name your-mcp-server \
  --secret api_key \
  --secret server_name \
  --publish 7501:7501 \
  yourdockerusername/your-mcp-server:latest
```

##### 4. Building Configuration into Derived Images

For development or testing purposes, you can build configuration directly into derived images:

```dockerfile
FROM docker.io/yourusername/base-mcp-server:latest

# Configure environment variables (non-sensitive only!)
ENV HOST=0.0.0.0
ENV PORT=7501
ENV SERVER_NAME=example-mcp-server

# Copy application code
COPY ./src ./src

CMD ["python", "main", "sse"]
```

#### Security Best Practices

- Never include sensitive API keys or secrets in Dockerfiles or images
- Use environment variables or mounted secrets for sensitive values
- Consider using Docker secrets or a vault service for production
- The container runs as a non-root user for improved security
- Rotate API keys and secrets regularly

## Development

This repository contains:

- `docker/Dockerfile`: Multi-stage Dockerfile for the base image
- `build.sh`: Build script with Docker Hub integration
- `requirements-base.txt`: Base Python dependencies
- Server-specific implementation directories (example/, jira-clone/)
- Local development scripts (setup.sh, run.sh)

## License

[MIT License](LICENSE)
