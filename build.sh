#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set image name, tag, and port
IMAGE_NAME=${1:-"base-mcp-server"}
TAG=${2:-"latest"}
PORT=${3:-"7501"}
DOCKER_USERNAME=$4

# Check if Docker username is provided
if [ -z "$DOCKER_USERNAME" ]; then
  echo "Error: Docker Hub username must be provided as the fourth argument"
  echo "Usage: $0 [image-name] [tag] [port] <docker-username>"
  exit 1
fi

echo "Building base MCP server image: $IMAGE_NAME:$TAG"

# Build the Docker image with buildx and load it into local registry
docker buildx build --load -t "$IMAGE_NAME:$TAG" -f docker/Dockerfile .

echo "Base MCP server image built successfully: $IMAGE_NAME:$TAG"

# Tag the image for Docker Hub
echo "Tagging image for Docker Hub as $DOCKER_USERNAME/$IMAGE_NAME:$TAG"
docker tag "$IMAGE_NAME:$TAG" "docker.io/$DOCKER_USERNAME/$IMAGE_NAME:$TAG"

# Check if we're logged in to Docker Hub
if ! docker info | grep -q "Username: $DOCKER_USERNAME"; then
  echo "You are not logged in to Docker Hub as $DOCKER_USERNAME"
  echo "Please login with: docker login -u $DOCKER_USERNAME"
  echo "Then push manually with: docker push docker.io/$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
else
  echo "Pushing to Docker Hub as $DOCKER_USERNAME/$IMAGE_NAME:$TAG"
  if docker push "docker.io/$DOCKER_USERNAME/$IMAGE_NAME:$TAG"; then
    echo "Successfully pushed to Docker Hub"
  else
    echo "Failed to push to Docker Hub. Please check your Docker Hub credentials and permissions."
    echo "You can manually push with: docker push docker.io/$DOCKER_USERNAME/$IMAGE_NAME:$TAG"
  fi
fi

echo "To run: docker run -p $PORT:7501 $IMAGE_NAME:$TAG"
