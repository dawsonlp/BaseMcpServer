#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Check if no parameters are provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 [image-name] [tag] [port] <docker-username>"
  echo ""
  echo "Parameters:"
  echo "  [image-name]      Name of the Docker image (default: example-mcp-server)"
  echo "  [tag]             Tag for the Docker image (default: latest)"
  echo "  [port]            Port to expose (default: 7501)"
  echo "  <docker-username> Docker Hub username (required)"
  echo ""
  echo "Example: $0 example-mcp-server latest 7501 myusername"
  exit 1
fi

# Set image name, tag, and port
IMAGE_NAME=${1:-"example-mcp-server"}
TAG=${2:-"latest"}
PORT=${3:-"7501"}
DOCKER_USERNAME=$4

# Check if Docker username is provided
if [ -z "$DOCKER_USERNAME" ]; then
  echo "Error: Docker Hub username must be provided as the fourth argument"
  echo "Usage: $0 [image-name] [tag] [port] <docker-username>"
  exit 1
fi

echo "Building Example MCP server image: $IMAGE_NAME:$TAG"
echo "Using base image from Docker Hub: $DOCKER_USERNAME/base-mcp-server:latest"

# Build the Docker image with buildx and load it into local registry
docker buildx build --load \
  --build-arg DOCKER_USERNAME=$DOCKER_USERNAME \
  -t "$IMAGE_NAME:$TAG" \
  -f docker/Dockerfile .

echo "Example MCP server image built successfully: $IMAGE_NAME:$TAG"

# Tag the image for Docker Hub
echo "Tagging image for Docker Hub as $DOCKER_USERNAME/$IMAGE_NAME:$TAG"
docker tag "$IMAGE_NAME:$TAG" "docker.io/$DOCKER_USERNAME/$IMAGE_NAME:$TAG"

# Check if we're logged in to Docker Hub
if ! docker info | grep -q "Username: $DOCKER_USERNAME"; then
  echo "You are not logged in to Docker Hub as $DOCKER_USERNAME"
  echo "Please login with: docker login -u $DOCKER_USERNAME"
  echo "Then push manually with: docker push docker.io/$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
else
  echo "You can push to Docker Hub with: docker push docker.io/$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
fi

echo "To run: docker run -p $PORT:7501 $IMAGE_NAME:$TAG"
