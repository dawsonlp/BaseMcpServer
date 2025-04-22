# BaseMcpServer

A minimal containerized base for MCP servers using the MCP Python SDK.

## Overview

BaseMcpServer provides a standardized Docker base image for building Model Context Protocol (MCP) servers. It is:

- **Simple**: Designed as a minimal implementation using the MCP Python SDK
- **Containerized**: Built specifically for Docker deployment
- **Protocol-specific**: Uses only the HTTP+SSE protocol (not stdio)
- **Reusable**: Serves as a foundation for derived MCP server implementations

This image provides all the common dependencies and configuration needed for MCP servers, so that derived projects can focus solely on implementing their specific tools and resources.

## Best Practices for Custom MCP Servers

When creating custom MCP servers based on this template, follow these best practices to avoid common issues:

### Port Configuration

1. **Use the Correct Ports**: The base image exposes port `7501`. Always align your configuration with this port:
   - In the `.env` file, set `PORT=7501`
   - When running the container, map the external port to 7501: `docker run -p EXTERNAL_PORT:7501`
   - In the `.mcp.json` file, use your chosen external port: `"url": "http://localhost:EXTERNAL_PORT"`
   - In the Claude MCP settings, use the external port with the SSE suffix: `"url": "http://localhost:EXTERNAL_PORT/sse"`

2. **Consistent Port Usage**: Be consistent with your port numbering. If you choose external port 7777:
   - Docker command: `docker run -p 7777:7501`
   - `.mcp.json`: `"url": "http://localhost:7777"`
   - Claude settings: `"url": "http://localhost:7777/sse"`

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

# Command to run your MCP server
CMD ["python", "-m", "src.main"]
```

## Technical Details

### Protocol Support

BaseMcpServer **only** supports the HTTP+SSE protocol, not stdio. This choice is deliberate and aligns with the containerized, web-based approach to MCP server deployment.

#### What is HTTP+SSE in MCP?

HTTP+SSE (Server-Sent Events) is one of the standard transports supported by the MCP protocol:

- **HTTP**: Used for client-to-server communication (requests)
- **SSE**: Used for server-to-client communication (responses and events)

Unlike stdio (which is primarily used for local development and desktop integration), HTTP+SSE is designed for networked environments, making it ideal for:

- Web-based LLM integrations
- Service-to-service MCP communication
- Containerized deployments (like this one)
- Cloud environments

#### Implementation Details

This base image uses:
- **Starlette**: A lightweight ASGI framework that handles the HTTP+SSE protocol
- **Uvicorn**: An ASGI server that serves the Starlette application

The implementation is provided by the MCP Python SDK through the `.sse_app()` method, which creates an ASGI application that handles the HTTP+SSE protocol.

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
- HTTP+SSE protocol for MCP communication between server and clients

### Environment Variables and Configuration

The base image supports configuration through environment variables, which can be passed to derived images in several ways:

#### Available Environment Variables

- `HOST`: Interface to bind to (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 7501)
- `API_KEY`: Required for authentication (must be provided)
- `OTHER_SECRET`: Optional additional secret
- Any additional environment variables required by your specific implementation

#### Configuration Methods for Derived Images

##### 1. Using Command Line Environment Variables

```bash
docker run -p 7501:7501 \
  -e API_KEY=your_api_key \
  -e OTHER_SECRET=your_secret \
  yourdockerusername/your-mcp-server:latest
```

##### 2. Using an Environment File

Create a `.env` file with your configuration:

```
API_KEY=your_api_key
OTHER_SECRET=your_secret
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
echo "your_secret" | docker secret create other_secret -

docker service create \
  --name your-mcp-server \
  --secret api_key \
  --secret other_secret \
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

# Copy application code
COPY ./src ./src

CMD ["python", "-m", "src.main"]
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

## License

[MIT License](LICENSE)
