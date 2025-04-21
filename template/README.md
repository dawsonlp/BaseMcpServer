# MCP Server Template

A clean, well-documented template for creating Model Context Protocol (MCP) servers using FastMCP and HTTP+SSE in a Docker container. This template provides everything you need to quickly build and deploy your own MCP server.

## What is MCP?

The Model Context Protocol (MCP) is a standard for communication between AI models and external tools/resources. An MCP server provides tools and resources that can be called by an AI model to access external functionality or data.

## Features

- **Ready-to-use template structure** for creating MCP servers
- **HTTP+SSE transport** for real-time communication
- **Docker containerization** for easy deployment and scaling
- **Clear, documented code** with extensive comments
- **Customizable configuration** via environment variables
- **Example implementations** of tools and resources

## Project Structure

```
template/
├── src/                     # Application code
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── main.py              # Server entry point
│   └── server.py            # MCP server implementation
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Container definition
│   └── build.sh             # Docker build script
├── .env.example             # Example environment variables
└── .mcp.json.template       # MCP configuration template
```

## Prerequisites

Before using this template, you need:

1. **Python 3.10+** installed on your development machine
2. **Docker** installed and configured
3. The **base-mcp-server** Docker image built (see instructions below)

## Getting Started

### Step 1: Clone or Copy the Template

Copy the template directory to create your new MCP server project:

```bash
cp -r template/ my-mcp-server/
cd my-mcp-server/
```

### Step 2: Customize the Configuration

1. Create an environment file:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

2. Update the MCP configuration:

```bash
cp .mcp.json.template .mcp.json
# Edit .mcp.json with your server details
```

### Step 3: Implement Your Tools and Resources

Edit `src/server.py` to implement your custom tools and resources. The template includes detailed comments and examples to guide you.

#### Example Tool Implementation

```python
@mcp.tool()
def my_custom_tool(parameter1: str, parameter2: int) -> Dict[str, Any]:
    """
    My custom tool that does something useful.
    
    Args:
        parameter1: Description of parameter1
        parameter2: Description of parameter2
        
    Returns:
        A dictionary with the result
    """
    # Your implementation here
    result = {"output": f"Processed {parameter1} {parameter2} times"}
    return result
```

#### Example Resource Implementation

```python
@mcp.resource("resource://my-resource")
def my_custom_resource() -> Dict[str, Any]:
    """
    My custom resource that provides useful data.
    
    Returns:
        A dictionary with the data
    """
    # Your implementation here
    return {"data": "Some useful information"}
```

### Step 4: Update Server Configuration

Edit `src/config.py` to add any additional configuration parameters your server needs.

### Step 5: Build the Docker Image

First, ensure you have built the base MCP server image:

```bash
# From the project root directory
./base-mcp-docker/build.sh base-mcp-server latest 7501 your-docker-username
```

Then build your custom MCP server:

```bash
# From your MCP server project directory
./docker/build.sh my-mcp-server latest 7501 your-docker-username
```

### Step 6: Run the Docker Container

```bash
docker run -p 7501:7501 --env-file .env my-mcp-server:latest
```

## Understanding MCP Annotations

The MCP Python SDK uses decorators to define tools and resources:

### Tool Annotations

```python
@mcp.tool()  # Basic tool
def basic_tool():
    return {"result": "success"}

@mcp.tool(name="custom_name")  # Tool with custom name
def tool_with_custom_name():
    return {"result": "success"}
```

### Resource Annotations

```python
@mcp.resource("resource://basic")  # Basic resource
def basic_resource():
    return {"data": "basic data"}

@mcp.resource("resource://parameterized/{id}")  # Parameterized resource
def parameterized_resource(id: str):
    return {"id": id, "data": f"data for {id}"}
```

## Development without Docker

For local development without Docker:

1. Install dependencies:

```bash
pip install mcp starlette uvicorn sse-starlette pydantic-settings httpx
```

2. Run the server:

```bash
python -m src.main
```

## Testing Your MCP Server

You can test your MCP server using the MCP test client:

```python
from mcp.client import McpClient

async def test_server():
    async with McpClient("http://localhost:7501") as client:
        # Call a tool
        result = await client.call_tool("example_tool", {
            "param1": "test",
            "param2": 42
        })
        print(f"Tool result: {result}")
        
        # Access a resource
        data = await client.access_resource("resource://example")
        print(f"Resource data: {data}")
```

## Security Considerations

- Always use a strong API key in production
- Consider using HTTPS for production deployments
- Review and update Docker security settings as needed
- The container runs as a non-root user for improved security

## Connecting with Claude Desktop and Cline

Once your MCP server is running, you can connect it to Claude Desktop or Cline (CLI client for Claude).

### Configuring Claude Desktop

1. Open Claude Desktop
2. Go to Settings > Advanced > MCP Servers
3. Click "Add MCP Server"
4. Enter the following information:
   - Name: Your server name (e.g., "My MCP Server")
   - URL: The server URL (e.g., "http://localhost:7501")
   - API Key: The API key you set in the .env file
5. Click "Save"
6. Your MCP server will now be available to Claude Desktop

### Configuring Cline in VSCode

To use your MCP server with Cline in VSCode, you need to edit a specific configuration file:

1. Create or edit the Cline MCP settings file:
   ```bash
   # Path may vary slightly depending on your OS
   # For Linux:
   mkdir -p ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/
   nano ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
   
   # For macOS:
   mkdir -p ~/Library/Application\ Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/
   nano ~/Library/Application\ Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
   
   # For Windows:
   # Create directory: %APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\
   # Then edit: cline_mcp_settings.json in that directory
   ```

2. Add your MCP server configuration with the following structure:

   ```json
   {
     "mcpServers": {
       "your-mcp-server-name": {
         "url": "http://localhost:7501/sse",
         "apiKey": "your_api_key_here",
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```

   Note that the URL should include `/sse` at the end to specify the Server-Sent Events transport.

3. Save the file and restart VSCode if it's already running

4. When using Cline in VSCode, it will automatically connect to your configured MCP server

### Testing the Connection

To verify that Claude can access your MCP server:

1. In Claude Desktop or Cline, ask Claude to use one of your tools:
   ```
   Please use the example_tool with param1="test" and param2=42
   ```

2. Claude should be able to call your tool and return the result

## Advanced Customization

### Adding Dependencies

If your MCP server requires additional Python packages:

1. Add them to the Dockerfile:

```dockerfile
RUN pip install --no-cache-dir package1 package2
```

### Using External ASGI Servers

The template supports using external ASGI servers like Uvicorn or Hypercorn:

```python
# In another file
from src.main import create_app

app = create_app()
```

Then run with your preferred ASGI server:

```bash
uvicorn myapp:app --host 0.0.0.0 --port 7501
```

## Contributing

Feel free to improve this template and submit pull requests!

## License

[MIT License](LICENSE)
