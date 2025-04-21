# Stage 1: Builder
FROM python:3.13-slim AS builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /build

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && pip install --upgrade pip \
    && pip install build wheel \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install MCP base dependencies
RUN pip wheel --no-deps --wheel-dir /wheels \
    mcp>=1.6.0 \
    starlette>=0.46.2 \
    uvicorn>=0.34.1 \
    sse-starlette>=2.2.1 \
    pydantic-settings>=2.8.1 \
    httpx>=0.28.1

# Stage 2: Runtime
FROM python:3.13-slim AS runtime

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /wheels /wheels

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

# Add metadata
LABEL maintainer="MCP User" \
      version="0.1.0" \
      description="Base MCP Server Docker Image"

# Expose the default MCP server port
EXPOSE 7501

# The actual command will be provided by the downstream images
CMD ["python"]
