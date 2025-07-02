# Multi-arch Dockerfile for mdproc - Markdown Processor
# Follows compiler container pattern (like gcc/clang containers)

FROM ubuntu:25.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies for WeasyPrint and document processing
RUN apt-get update && apt-get install -y \
    # Python 3.13 and pip
    python3.13 \
    python3-pip \
    python3-venv \
    python3-dev \
    # pipx for isolated Python app installation
    pipx \
    # WeasyPrint system dependencies
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    # Font packages for proper PDF rendering
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-core \
    # Node.js for Mermaid diagram generation
    nodejs \
    npm \
    # Additional utilities
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Mermaid CLI globally
RUN npm install -g @mermaid-js/mermaid-cli

# Install Playwright browsers for Mermaid rendering
RUN npx playwright install --with-deps chromium

# Create symlink for python3.13 to python3 (if needed)
RUN ln -sf /usr/bin/python3.13 /usr/bin/python3

# Copy application code
COPY . /app

# Install mdproc using pipx for proper isolation
WORKDIR /app
RUN pipx install . --force

# Ensure pipx binaries are in PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory for mounted files (compiler pattern)
WORKDIR /workspace

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD mdproc --version || exit 1

# Labels for metadata
LABEL org.opencontainers.image.title="mdproc"
LABEL org.opencontainers.image.description="Markdown processor with hexagonal architecture - converts MD to PDF, HTML, DOCX, TXT"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="dawsonlp"
LABEL org.opencontainers.image.source="https://github.com/dawsonlp/mdproc"

# Direct entrypoint like compiler containers (gcc, clang, etc.)
ENTRYPOINT ["mdproc"]
CMD ["--help"]
