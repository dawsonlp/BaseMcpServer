#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "Setting up Jira MCP Server for local development..."

# Function to check virtual environment status
check_virtual_env_status() {
    local current_dir=$(pwd)
    local python_path=$(which python 2>/dev/null || echo "")
    
    # Check if python points to our local .venv
    if [[ "$python_path" == "$current_dir/.venv"* ]]; then
        echo "✓ Local virtual environment is already active"
        return 0  # venv is active
    elif [[ -n "$VIRTUAL_ENV" && "$VIRTUAL_ENV" != "$current_dir/.venv" ]]; then
        echo "⚠️  Different virtual environment is active: $VIRTUAL_ENV"
        echo "   Please deactivate it first with: deactivate"
        echo "   Then run this script again."
        exit 1
    else
        echo "Local virtual environment is not active"
        return 1  # venv not active
    fi
}

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.13"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    echo "Please install Python $REQUIRED_VERSION or higher and try again."
    exit 1
fi

echo "✓ Python version check passed: $PYTHON_VERSION"

# Check if virtual environment is already active
if check_virtual_env_status; then
    echo "Skipping virtual environment activation (already active)"
    VENV_WAS_ACTIVE=true
else
    VENV_WAS_ACTIVE=false
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv .venv
        echo "✓ Virtual environment created"
    else
        echo "✓ Virtual environment already exists"
    fi

    # Activate virtual environment
    echo "Activating virtual environment..."
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "✓ Dependencies installed successfully"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created from .env.example"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your actual Jira credentials:"
    echo "   - JIRA_URL: Your Jira instance URL"
    echo "   - JIRA_USER: Your Jira username/email"
    echo "   - JIRA_TOKEN: Your Jira API token"
    echo "   - API_KEY: A secure API key for MCP client authentication"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Jira credentials"
echo "2. Run the server: ./scripts/run.sh sse"
echo "3. Test the server: curl http://localhost:7501/health"
echo ""
echo "For help: ./scripts/run.sh help"
