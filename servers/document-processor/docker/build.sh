#!/bin/bash
# Multi-architecture Docker build script for mdproc
# Builds and pushes to dawsonlp registry

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="dawsonlp"
IMAGE_NAME="mdproc"
VERSION="1.0.0"
PLATFORMS="linux/amd64,linux/arm64"

echo -e "${BLUE}🐳 Building multi-arch Docker image for mdproc${NC}"
echo -e "${YELLOW}Registry: ${REGISTRY}${NC}"
echo -e "${YELLOW}Image: ${IMAGE_NAME}${NC}"
echo -e "${YELLOW}Version: ${VERSION}${NC}"
echo -e "${YELLOW}Platforms: ${PLATFORMS}${NC}"
echo

# Check if buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker buildx is not available${NC}"
    echo "Please install Docker buildx or use a newer version of Docker"
    exit 1
fi

# Check if we're logged into the registry
echo -e "${BLUE}🔐 Checking Docker registry authentication...${NC}"
if ! docker info | grep -q "Username:"; then
    echo -e "${YELLOW}⚠️  Not logged into Docker registry. Please run: docker login${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create and use buildx builder if it doesn't exist
BUILDER_NAME="mdproc-builder"
if ! docker buildx inspect $BUILDER_NAME >/dev/null 2>&1; then
    echo -e "${BLUE}🔧 Creating buildx builder: ${BUILDER_NAME}${NC}"
    docker buildx create --name $BUILDER_NAME --use
else
    echo -e "${BLUE}🔧 Using existing buildx builder: ${BUILDER_NAME}${NC}"
    docker buildx use $BUILDER_NAME
fi

# Build and push multi-arch image
echo -e "${BLUE}🚀 Building and pushing multi-arch image...${NC}"
echo

# Change to the project root directory
cd "$(dirname "$0")/.."

# Build with buildx
docker buildx build \
    --platform $PLATFORMS \
    --tag $REGISTRY/$IMAGE_NAME:latest \
    --tag $REGISTRY/$IMAGE_NAME:$VERSION \
    --push \
    --progress=plain \
    .

echo
echo -e "${GREEN}✅ Multi-arch build completed successfully!${NC}"
echo
echo -e "${BLUE}📦 Images pushed to registry:${NC}"
echo -e "  • ${REGISTRY}/${IMAGE_NAME}:latest"
echo -e "  • ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo
echo -e "${BLUE}🚀 Usage examples:${NC}"
echo -e "${YELLOW}# Direct usage${NC}"
echo -e "docker run --rm -v \$(pwd):/workspace ${REGISTRY}/${IMAGE_NAME} convert -i document.md -f pdf"
echo
echo -e "${YELLOW}# Recommended alias${NC}"
echo -e "alias mdproc='docker run --rm -v \$(pwd):/workspace ${REGISTRY}/${IMAGE_NAME}'"
echo -e "mdproc convert -i document.md -f pdf"
echo
echo -e "${YELLOW}# Test the image${NC}"
echo -e "docker run --rm ${REGISTRY}/${IMAGE_NAME} --version"
echo -e "docker run --rm ${REGISTRY}/${IMAGE_NAME} formats"
echo
