#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Default values
IMAGE_NAME="jira-mcp-server"
TAG="latest"
PORT="7501"
CONTAINER_NAME="jira-mcp-server"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -i, --image IMAGE_NAME    Docker image name (default: jira-mcp-server)"
    echo "  -t, --tag TAG             Docker image tag (default: latest)"
    echo "  -p, --port PORT           Host port to bind (default: 7501)"
    echo "  -n, --name CONTAINER_NAME Container name (default: jira-mcp-server)"
    echo "  -e, --env-file ENV_FILE   Environment file path (default: .env)"
    echo "  -d, --detach              Run in detached mode"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Run with defaults using .env file"
    echo "  $0 -d                     # Run in detached mode"
    echo "  $0 -p 8501 -n my-jira     # Custom port and container name"
    echo "  $0 --env-file prod.env    # Use custom environment file"
    echo ""
    echo "Environment Variables (if not using .env file):"
    echo "  JIRA_URL                  Your Jira instance URL"
    echo "  JIRA_USER                 Your Jira username/email"
    echo "  JIRA_TOKEN                Your Jira API token"
    echo "  API_KEY                   MCP server API key"
}

# Parse command line arguments
DETACH_MODE=""
ENV_FILE=".env"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -d|--detach)
            DETACH_MODE="-d"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if the image exists
if ! docker image inspect "$IMAGE_NAME:$TAG" >/dev/null 2>&1; then
    echo "Error: Docker image '$IMAGE_NAME:$TAG' not found."
    echo "Please build the image first using: ./docker/build.sh"
    exit 1
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Warning: Environment file '$ENV_FILE' not found."
    echo "You can:"
    echo "1. Create it from the example: cp .env.example $ENV_FILE"
    echo "2. Set environment variables manually"
    echo "3. Use a different env file with --env-file option"
    echo ""
    read -p "Continue without env file? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    ENV_FILE_ARG=""
else
    ENV_FILE_ARG="--env-file $ENV_FILE"
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo "Stopping and removing existing container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

# Run the container
echo "Starting Jira MCP Server..."
echo "Image: $IMAGE_NAME:$TAG"
echo "Container: $CONTAINER_NAME"
echo "Port: $PORT"
echo "Environment file: $ENV_FILE"

if [ -n "$DETACH_MODE" ]; then
    echo "Mode: Detached"
else
    echo "Mode: Interactive (Ctrl+C to stop)"
fi

echo ""

# Build the docker run command
DOCKER_CMD="docker run --rm $DETACH_MODE -p $PORT:7501 --name $CONTAINER_NAME"

if [ -n "$ENV_FILE_ARG" ]; then
    DOCKER_CMD="$DOCKER_CMD $ENV_FILE_ARG"
fi

DOCKER_CMD="$DOCKER_CMD $IMAGE_NAME:$TAG"

# Execute the command
eval $DOCKER_CMD

if [ -n "$DETACH_MODE" ]; then
    echo ""
    echo "Container started successfully!"
    echo ""
    echo "To check logs: docker logs -f $CONTAINER_NAME"
    echo "To stop: docker stop $CONTAINER_NAME"
    echo "To test: curl http://localhost:$PORT/health"
else
    echo ""
    echo "Container stopped."
fi
