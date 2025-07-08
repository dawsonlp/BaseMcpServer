#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Initialize variables
ENV_FILE=""
TRANSPORT_MODE=""

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [TRANSPORT_MODE]"
    echo ""
    echo "Options:"
    echo "  --env <path>    Specify path to environment file (default: .env)"
    echo ""
    echo "Transport modes:"
    echo "  sse       Run as HTTP+SSE server (for network/container use)"
    echo "  stdio     Run as stdio server (for local development)"
    echo "  help      Show detailed help information"
    echo ""
    echo "Examples:"
    echo "  $0 sse                           # Start HTTP+SSE server using .env"
    echo "  $0 stdio                         # Start stdio server using .env"
    echo "  $0 --env /path/to/custom.env sse # Start server with custom env file"
    echo "  $0 --env .env.prod stdio         # Start stdio with production env"
    echo ""
    echo "Prerequisites:"
    echo "  - Run ./scripts/setup.sh first to set up the environment"
    echo "  - Configure .env file with your Jira credentials"
    echo ""
    echo "Testing:"
    echo "  curl http://localhost:7501/health  # Test HTTP+SSE server"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENV_FILE="$2"
            shift 2
            ;;
        sse|stdio|help|--help|-h)
            TRANSPORT_MODE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Set default env file if not specified
if [ -z "$ENV_FILE" ]; then
    ENV_FILE=".env"
fi

# Convert relative path to absolute path
if [[ "$ENV_FILE" != /* ]]; then
    ENV_FILE="$PWD/$ENV_FILE"
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found." >&2
    echo "Please run ./scripts/setup.sh first to set up the development environment." >&2
    exit 1
fi

# Check if specified env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file not found: $ENV_FILE" >&2
    echo "Please create the environment file with your Jira credentials." >&2
    if [ "$ENV_FILE" = "$PWD/.env" ]; then
        echo "You can run: cp .env.example .env" >&2
    fi
    exit 1
fi

# Load environment variables from the specified file
echo "Loading environment from: $ENV_FILE" >&2
set -a  # Automatically export all variables
source "$ENV_FILE"
set +a  # Stop auto-exporting

# Validate required environment variables - halt and catch fire if missing
REQUIRED_VARS=("JIRA_URL" "JIRA_USER" "JIRA_TOKEN" "SERVER_NAME" "API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "Error: Required environment variables are missing from $ENV_FILE:" >&2
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var" >&2
    done
    echo "" >&2
    echo "Please add these variables to your environment file and try again." >&2
    echo "HALTING AND CATCHING FIRE! 🔥" >&2
    exit 1
fi

# Activate virtual environment (silent for stdio mode)
if [ "$TRANSPORT_MODE" != "stdio" ]; then
    echo "Activating virtual environment..."
fi
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import mcp" >/dev/null 2>&1; then
    echo "Error: Dependencies not installed." >&2
    echo "Please run ./scripts/setup.sh first to install dependencies." >&2
    exit 1
fi

# Set PYTHONPATH to include src directory
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Change to src directory
cd src

# Handle transport mode
if [ -z "$TRANSPORT_MODE" ]; then
    echo "No transport mode specified. Use 'help' for usage information."
    show_usage
    exit 1
fi

case "$TRANSPORT_MODE" in
    "sse")
        echo "Starting Jira MCP Server with HTTP+SSE transport..."
        echo "Server will be available at: http://localhost:7501"
        echo "Health check: http://localhost:7501/health"
        echo ""
        echo "Press Ctrl+C to stop the server"
        echo ""
        python main.py sse
        ;;
    "stdio")
        # Silent mode for Claude Desktop - no output to stdout except JSON
        python main.py stdio
        ;;
    "help"|"--help"|"-h")
        python main.py help
        ;;
    *)
        echo "Unknown transport mode: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
