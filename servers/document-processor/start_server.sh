#!/bin/bash

# Document Processor MCP Server Startup Script
# This script starts the document processor server in a Docker container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_IMAGE="document-processor:latest"
OUTPUT_DIR="$HOME/.mcp_servers/output/document-processor"

echo "🚀 Starting Document Processor MCP Server..."

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH" >&2
    exit 1
fi

# Check if the Docker image exists, build if not
if ! docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
    echo "📦 Building document processor Docker image..."
    cd "$SCRIPT_DIR"
    docker build -f docker/Dockerfile -t "$DOCKER_IMAGE" .
fi

# Stop any existing container
echo "🛑 Stopping any existing document processor containers..."
docker stop document-processor-server 2>/dev/null || true
docker rm document-processor-server 2>/dev/null || true

# Start the server
echo "🌐 Starting server on http://localhost:7502/mcp"
echo "📁 Output directory: $OUTPUT_DIR"
