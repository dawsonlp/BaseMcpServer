#!/bin/bash
# setup.sh - Creates and configures a virtual environment for this MCP server

# Script location directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Try to use Python 3.13 specifically
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD=python3.13
else
    echo "Python 3.13 not found, falling back to system python..."
    PYTHON_CMD=python
    
    # Check Python version
    PY_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if (( $(echo "$PY_VERSION < 3.13" | bc -l) )); then
        echo "Warning: Using Python $PY_VERSION, but Python 3.13+ is recommended"
        echo "Please consider upgrading your Python installation"
    fi
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create a venv if it doesn't exist
if [ ! -d "$DIR/.venv" ]; then
    echo "Creating virtual environment in $DIR/.venv..."
    $PYTHON_CMD -m venv "$DIR/.venv"
else
    echo "Using existing virtual environment in $DIR/.venv"
fi

# Activate the venv
source "$DIR/.venv/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r "$DIR/requirements.txt"

echo ""
echo "Setup complete! To activate this environment, run:"
echo "source $DIR/.venv/bin/activate"
echo ""
echo "To start the MCP server, run:"
echo "cd $DIR/src && python main.py sse"
echo ""
echo "Remember to set your Jira credentials in .env file before running the server"
