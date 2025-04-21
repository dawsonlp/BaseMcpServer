# Use the base MCP server image as a foundation
ARG DOCKER_USERNAME

FROM docker.io/${DOCKER_USERNAME}/base-mcp-server:latest

# Set working directory
WORKDIR /app

# Copy the application code
COPY ./src ./src

# Add metadata
LABEL maintainer="MCP Example" \
      version="0.1.0" \
      description="Example MCP Server Docker Image"

# The command to run the MCP server
CMD ["python", "-m", "src.main"]
