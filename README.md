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
