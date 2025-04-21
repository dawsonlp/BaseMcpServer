# BaseMcpServer

A minimal containerized base for MCP servers using the MCP Python SDK.

## Overview

BaseMcpServer provides a standardized Docker base image for building Model Context Protocol (MCP) servers. It is:

- **Simple**: Designed as a minimal implementation using the MCP Python SDK
- **Containerized**: Built specifically for Docker deployment
- **Protocol-specific**: Uses only the HTTP+SSE protocol (not stdio)
- **Reusable**: Serves as a foundation for derived MCP server implementations

This image provides all the common dependencies and configuration needed for MCP servers, so that derived projects can focus solely on implementing their specific tools and resources.

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

BaseMcpServer **only** supports the HTTP+SSE protocol, not stdio. This makes it ideal for:

- Web-based LLM integrations
- Service-to-service MCP communication
- Containerized deployments
- Cloud environments

### Python SDK Implementation

The image directly uses the MCP Python SDK with minimal abstraction:

- FastMCP for ergonomic tool definitions
- Built-in schema generation based on Python type hints
- Automatic validation of input/output formats
- SSE-based progress reporting

### Environment Variables

The base image can be configured with:

- `HOST`: Interface to bind to (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 7501)
- Any additional environment variables required by your implementation

## Development

This repository contains:

- `docker/Dockerfile`: Multi-stage Dockerfile for the base image
- `build.sh`: Build script with Docker Hub integration

## License

[MIT License](LICENSE)
