# MCP Server Template

A clean, well-structured template for building Model Context Protocol (MCP) servers using FastMCP. This template provides the foundation for creating your own MCP server with custom tools and resources.

## Features

- **Ready-to-use template structure** for creating MCP servers
- **Clear separation of concerns** (main entry point, server logic, configuration)
- **Docker containerization** for easy deployment
- **Comprehensive transport support** (stdio for development, HTTP+SSE for production)
- **Example implementations** of tools and resources
- **Flexible configuration** via environment variables

## Project Structure

```
template/
├── src/                     # Application code
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management with auto-discovery
│   ├── main.py              # Server entry point with transport options
│   └── server.py            # MCP server implementation with example tools
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Container definition
│   └── build.sh             # Docker build script
├── run.sh                   # Convenience script to run the server
├── setup.sh                 # Setup script for virtual environment
├── requirements.txt         # Python dependencies
└── .env.example             # Example environment variables
```

## Prerequisites

- Python 3.13+ (recommended)
- Docker (for containerized deployment)

## Getting Started

### Option 1: Local Development

1. Clone this template to your new project:
   ```bash
   cp -r template/ my-mcp-server/
   cd my-mcp-server/
   ```

2. Create your environment and install dependencies:
   ```bash
   ./setup.sh
   ```

3. Create your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Run the server:
   ```bash
   ./run.sh       # Default SSE transport
   # or
   ./run.sh stdio # For STDIO transport (local development)
   ```

### Option 2: Docker Deployment

1. Build the Docker image:
   ```bash
   ./docker/build.sh my-mcp-server latest 7501 <your-docker-username>
   ```

2. Run the container:
   ```bash
   docker run -p 7501:7501 my-mcp-server:latest
   ```

## Customizing Your Server

### Adding Tools

Edit `src/server.py` and add functions within the `register_tools_and_resources` function:

```python
@srv.tool()
def my_custom_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    Tool description here
    
    Args:
        param1: First parameter
        param2: Second parameter
        
    Returns:
        A dictionary containing the result
    """
    # Your tool implementation
    return {"result": f"Processed {param1} with value {param2}"}
```

### Adding Resources

Add resource functions in `src/server.py`:

```python
@srv.resource("resource://my-custom-resource/{param_id}")
def my_custom_resource(param_id: str) -> Dict[str, Any]:
    """Resource description"""
    return {"id": param_id, "data": f"Resource data for {param_id}"}
```

## Connecting to Claude/Cline

1. Start your MCP server with the `sse` transport:
   ```bash
   ./run.sh sse  # or just ./run.sh (default)
   ```

2. Configure Claude Desktop or Cline to use your server:
   - For Claude Desktop: Settings → Advanced → MCP Servers → Add MCP Server
   - For Cline: Edit the MCP settings file (see help in `python main.py help`)

## Available Example Tools & Resources

The template includes example tools and resources to demonstrate implementation patterns:

### Tools
- `example_tool`: A simple example showing parameter handling
  - Parameters: `param1` (string), `param2` (integer), `optional_param` (boolean, optional)
  - Returns: Echo of the parameters received

### Resources
- `resource://example`: Basic resource returning static data
- `resource://example/{id}`: Parameterized resource demonstrating path parameters

## Security Considerations

- Set a strong API key in your `.env` file
- Consider using HTTPS in production environments
- Review Docker security settings for production deployment

## For More Information

For more details on using this template, run:
```bash
cd src && python main.py help
```

## License

[MIT License](LICENSE)
