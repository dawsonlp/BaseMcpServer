#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Check if no parameters are provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 [image-name] [tag] [port]"
  echo ""
  echo "Parameters:"
  echo "  [image-name]      Name of the Docker image (default: jira-mcp-server)"
  echo "  [tag]             Tag for the Docker image (default: latest)"
  echo "  [port]            Port to expose (default: 7501)"
  echo ""
  echo "Example: $0 jira-mcp-server latest 7501"
  echo ""
  echo "This script builds a standalone Jira MCP server Docker image."
  echo "No external dependencies or base images are required."
  exit 1
fi

# Set image name, tag, and port
IMAGE_NAME=${1:-"jira-mcp-server"}
TAG=${2:-"latest"}
PORT=${3:-"7501"}

echo "Building Jira MCP server image: $IMAGE_NAME:$TAG"
echo "Exposed port: $PORT"

# Build the Docker image with buildx and load it into local registry
docker buildx build --load \
  -t "$IMAGE_NAME:$TAG" \
  -f docker/Dockerfile .

echo "Jira MCP server image built successfully: $IMAGE_NAME:$TAG"

# Provide usage instructions
echo ""
echo "=== Usage Instructions ==="
echo ""
echo "1. Create a .env file with your Jira credentials:"
echo "   cp .env.example .env"
echo "   # Edit .env with your actual Jira settings"
echo ""
echo "2. Run the container:"
echo "   docker run -p $PORT:7501 --env-file .env $IMAGE_NAME:$TAG"
echo ""
echo "3. Or run with individual environment variables:"
echo "   docker run -p $PORT:7501 \\"
echo "     -e JIRA_URL=https://your-domain.atlassian.net \\"
echo "     -e JIRA_USER=your-email@example.com \\"
echo "     -e JIRA_TOKEN=your-api-token \\"
echo "     -e API_KEY=your-secure-api-key \\"
echo "     $IMAGE_NAME:$TAG"
echo ""
echo "4. Test the server:"
echo "   curl http://localhost:$PORT/health"
echo ""
echo "5. Connect to Cline (VS Code):"
echo "   Add to cline_mcp_settings.json:"
echo "   {"
echo "     \"mcpServers\": {"
echo "       \"jira-mcp-server\": {"
echo "         \"url\": \"http://localhost:$PORT/sse\","
echo "         \"apiKey\": \"your-secure-api-key\","
echo "         \"disabled\": false"
echo "       }"
echo "     }"
echo "   }"
echo ""
echo "6. Connect to Claude Desktop:"
echo "   Add MCP Server:"
echo "   - Name: jira-mcp-server"
echo "   - URL: http://localhost:$PORT"
echo "   - API Key: your-secure-api-key"
