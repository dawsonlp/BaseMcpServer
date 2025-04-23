#!/bin/bash
# run.sh - Activates the venv and runs the MCP server

# Script location directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if venv exists
if [ ! -d "$DIR/.venv" ]; then
    echo "Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$DIR/.env" ]; then
    echo "Warning: .env file not found. Using default settings."
    echo "Consider copying .env.example to .env and updating Jira credentials."
fi

# Activate the venv
source "$DIR/.venv/bin/activate"

# Set PYTHONPATH
export PYTHONPATH="$DIR/src:$PYTHONPATH"

# Change to the src directory
cd "$DIR/src"

# Get transport mode from args or default to sse
TRANSPORT=${1:-sse}

echo "Starting Jira MCP server with $TRANSPORT transport..."

# Run the server
python main.py $TRANSPORT
