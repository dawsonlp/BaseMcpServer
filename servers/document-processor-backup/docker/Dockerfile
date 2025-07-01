# Use Ubuntu 25.04 as base image for better document processing support
FROM ubuntu:25.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    # Python and pip
    python3.13 \
    python3.13-dev \
    python3.13-venv \
    python3-pip \
    # Document processing tools
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Additional utilities
    curl \
    wget \
    git \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1001 mcpuser && \
    mkdir -p /app /app/output /app/input /app/templates && \
    chown -R mcpuser:mcpuser /app

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Create and activate virtual environment
RUN python3.13 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies in virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./src ./src

# Copy template files
COPY ./docker/templates/ /app/templates/

# Set PYTHONPATH to include src as a sources root
ENV PYTHONPATH="/app/src"

# Set working directory to src
WORKDIR /app/src

# Change ownership of all files to mcpuser
RUN chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Expose the default port
EXPOSE 7502

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7502/health || exit 1

# Add metadata
LABEL maintainer="Document Processor MCP Server" \
      version="0.1.0" \
      description="Document Processor MCP Server - Convert markdown to PDF, HTML, DOCX, and text"

# Run main with streamable-http transport mode
CMD ["python3.13", "main.py", "streamable-http"]
