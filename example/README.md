# Example MCP Server

A simple, clean implementation of an MCP server built on the BaseMcpServer base image. This example demonstrates how to create a dockerized MCP server with custom tools and resources.

## Features

- **Simple Calculator Tool**: Perform basic arithmetic operations
- **Weather Simulation Tool**: Get simulated weather data for any city
- **Quotes Resources**: Access inspirational programming quotes
- **Fully Dockerized**: Easy to build and deploy
- **Based on MCP Python SDK**: Uses the official Model Context Protocol SDK

## Project Structure

```
example/
├── src/                     # Application code
│   ├── __init__.py
│   ├── config.py            # Configuration handling
│   ├── main.py              # Entry point for the server
│   └── server.py            # MCP server implementation with tools and resources
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Dockerfile to build the image
│   └── build.sh             # Build script for Docker image
└── .env.example             # Example environment variables
```

## Prerequisites

- Docker installed and configured
- The BaseMcpServer base image built and available (see the root project README.md)

## Building the Server

The example server builds upon the BaseMcpServer base image. You'll need to build that first if you haven't already.

```bash
# First, build the base image (from the project root)
./base-mcp-docker/build.sh base-mcp-server latest 7501 <your-docker-username>

# Then build the example server (from the project root)
./example/docker/build.sh example-mcp-server latest 7501 <your-docker-username>
```

Parameters:
- `example-mcp-server`: Image name (default)
- `latest`: Tag (default)
- `7501`: Port to expose (default)
- `<your-docker-username>`: **Required** - Your Docker Hub username (must match what was used for base image)

## Running the Server

```bash
docker run -p 7501:7501 example-mcp-server:latest
```

Or with a different port mapping:

```bash
docker run -p 8080:7501 example-mcp-server:latest
```

## Configuration

Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Available Tools and Resources

### Tools

1. **Calculator** (`calculator`)
   - Performs basic arithmetic operations
   - Parameters:
     - `operation`: String (add, subtract, multiply, divide)
     - `x`: Number (first operand)
     - `y`: Number (second operand)
   - Returns: `{"result": number}`

2. **Weather** (`get_weather`)
   - Gets simulated weather data for a location
   - Parameters:
     - `city`: String (city name)
     - `country`: String (optional country code)
   - Returns: Weather data including temperature, conditions, and humidity

### Resources

1. **Quotes List** (`resource://quotes`)
   - Returns a list of inspirational programming quotes

2. **Specific Quote** (`resource://quotes/{index}`)
   - Returns a specific quote by index (0-3)
   - Parameters:
     - `index`: Integer (quote index)

## Example Usage with MCP Client

When connecting an MCP client to this server, you would call tools like this:

```python
# Calculator tool example
result = await session.call_tool("calculator", {
    "operation": "add", 
    "x": 5, 
    "y": 3
})
# Returns: {"result": 8}

# Weather tool example
weather = await session.call_tool("get_weather", {
    "city": "San Francisco",
    "country": "US"  # Optional
})
# Returns: simulated weather data

# Accessing resources
quotes = await session.access_resource("resource://quotes")
# Returns: list of quotes

specific_quote = await session.access_resource("resource://quotes/2")
# Returns: the quote at index 2
```

## Security Considerations

- For production use, set a strong API key in the `.env` file
- Consider using HTTPS in production environments
- The container runs as a non-root user for improved security

## License

[MIT License](LICENSE)
