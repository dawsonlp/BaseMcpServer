#!/bin/bash

# Build script for Document Processor MCP Server Docker image
# This script builds a multi-architecture Docker image using BuildX

set -e

# Configuration
IMAGE_NAME="document-processor"
TAG="latest"
PLATFORMS="linux/amd64,linux/arm64"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Document Processor MCP Server Docker Image${NC}"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker buildx is not available${NC}"
    exit 1
fi

# Create builder if it doesn't exist
BUILDER_NAME="document-processor-builder"
if ! docker buildx inspect $BUILDER_NAME > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating new buildx builder: $BUILDER_NAME${NC}"
    docker buildx create --name $BUILDER_NAME --use
else
    echo -e "${YELLOW}Using existing buildx builder: $BUILDER_NAME${NC}"
    docker buildx use $BUILDER_NAME
fi

# Build the image
echo -e "${YELLOW}Building multi-architecture image...${NC}"
echo "Image: $IMAGE_NAME:$TAG"
echo "Platforms: $PLATFORMS"

# Change to the parent directory (where Dockerfile context should be)
cd "$(dirname "$0")/.."

# Build the image
docker buildx build \
    --platform $PLATFORMS \
    --tag $IMAGE_NAME:$TAG \
    --file docker/Dockerfile \
    --load \
    .

echo -e "${GREEN}Build completed successfully!${NC}"
echo ""
echo "To run the container:"
echo "  docker run -d \\"
echo "    --name document-processor \\"
echo "    -p 7502:7502 \\"
echo "    -v \$(pwd)/output:/app/output \\"
echo "    -v \$(pwd)/input:/app/input \\"
echo "    -v \$(pwd)/templates:/app/templates \\"
echo "    $IMAGE_NAME:$TAG"
echo ""
echo "To push to registry (if needed):"
echo "  docker buildx build --platform $PLATFORMS --tag your-registry/$IMAGE_NAME:$TAG --push ."
