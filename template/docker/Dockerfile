# Use the base MCP server image as a foundation
# The DOCKER_USERNAME will be passed as a build argument
ARG DOCKER_USERNAME

FROM docker.io/${DOCKER_USERNAME}/base-mcp-server:latest

# Set working directory
WORKDIR /app

# Copy the application code
# This copies your src directory containing the MCP server implementation
COPY ./src ./src

# Add metadata - replace with your own information
LABEL maintainer="Your Name <your.email@example.com>" \
      version="0.1.0" \
      description="Your MCP Server Description"

# The command to run the MCP server
# This executes the main.py module in the src package
CMD ["python", "-m", "src.main"]

# Optional: If you need to install additional dependencies,
# uncomment and modify the following:
#
# RUN pip install --no-cache-dir some-package another-package

# Optional: If you need to copy additional files (like configurations),
# uncomment and modify the following:
#
# COPY ./some-config-file.json /app/
