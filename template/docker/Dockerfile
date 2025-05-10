# Use the base MCP server image as a foundation
ARG DOCKER_USERNAME

FROM docker.io/${DOCKER_USERNAME}/base-mcp-server:latest

# Set working directory
WORKDIR /app

# Optional: Install additional dependencies
# Uncomment and modify the following to add your required packages:
# RUN pip install --no-cache-dir package-name another-package

# Copy the application code
COPY ./src ./src

# Set PYTHONPATH to include src as a sources root
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Set working directory to src
WORKDIR /app/src

# Environment variables will be provided at runtime
# .env file can be mounted if needed

# Add metadata - replace with your own information
LABEL maintainer="Your Name <your.email@example.com>" \
      version="0.1.0" \
      description="Template MCP Server Docker Image"

# Run main directly with sse transport mode
CMD ["python", "main", "sse"]
