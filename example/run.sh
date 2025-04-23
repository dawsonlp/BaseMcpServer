#!/bin/bash
# run.sh - Activates the venv and runs the MCP server

# Script location directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if venv exists
if [ ! -d "$DIR/.venv" ]; then
    echo "Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate the venv
source "$DIR/.venv/bin/activate"

# Set PYTHONPATH
export PYTHONPATH="$DIR/src:$PYTHONPATH"

# Change to the src directory
cd "$DIR/src"

# Get transport mode from args or default to sse
TRANSPORT=${1:-sse}

echo "Starting MCP server with $TRANSPORT transport..."

# Run the server
python main.py $TRANSPORT
