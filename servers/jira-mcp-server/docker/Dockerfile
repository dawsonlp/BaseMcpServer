# Multi-stage build for a smaller final image
FROM python:3.13-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Production stage
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user
RUN groupadd --gid 1000 mcpuser && \
    useradd --uid 1000 --gid mcpuser --shell /bin/bash --create-home mcpuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy the application code
COPY ./src ./src

# Set PYTHONPATH to include src as a sources root
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Change ownership of the app directory to mcpuser
RUN chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Set working directory to src
WORKDIR /app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7501/health || exit 1

# Add metadata
LABEL maintainer="MCP Community" \
      version="1.0.0" \
      description="Standalone Jira MCP Server Docker Image" \
      org.opencontainers.image.title="Jira MCP Server" \
      org.opencontainers.image.description="A comprehensive MCP server for Jira integration" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="MCP Community"

# Expose the default MCP port
EXPOSE 7501

# Run main directly with sse transport mode
CMD ["python", "main.py", "sse"]
