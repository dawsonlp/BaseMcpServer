#!/bin/bash

# Simple setup script for Document Processor MCP Server local development

set -e

echo "Document Processor MCP Server - Local Development Setup"
echo "======================================================"

# Check if Python 3.13 is available
if ! command -v python3.13 &> /dev/null; then
    echo "Error: Python 3.13 is not installed"
    echo "Please install Python 3.13 first"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.13 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p output input templates

# Copy example environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file to customize settings"
fi

# Copy example templates if templates directory is empty
if [ ! "$(ls -A templates)" ]; then
    echo "Copying example templates..."
    cp docker/templates/* templates/ 2>/dev/null || true
fi

echo ""
echo "Setup completed!"
echo ""
echo "To run locally:"
echo "  source venv/bin/activate"
echo "  cd src"
echo "  python main.py streamable-http"
echo ""
echo "To run in Docker:"
echo "  docker build -f docker/Dockerfile -t document-processor ."
echo "  docker run -d -p 7502:7502 \\"
echo "    -v \$(pwd)/output:/app/output \\"
echo "    -v \$(pwd)/input:/app/input \\"
echo "    -v \$(pwd)/templates:/app/templates \\"
echo "    document-processor"
