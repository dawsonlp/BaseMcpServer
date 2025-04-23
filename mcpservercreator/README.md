# MCP Server Creator

A specialized MCP server that can dynamically create and install new MCP servers based on Python code snippets. This meta-MCP server enables rapid development and deployment of new MCP tools without having to manually create all the boilerplate files.

## Features

- Generate complete MCP servers from Python code snippets
- Automatically validate code for security concerns
- Install the generated servers locally with mcp-manager
- List all installed MCP servers

## Installation

The server can be installed using the mcp-manager:

```bash
mcp-manager install local mcpservercreator --source ./mcpservercreator
```

After installation, make sure to restart VS Code completely for the new server to be recognized by Cline.

## Usage

### Creating a New MCP Server

To create a new MCP server, use the `create_mcp_server` tool with the following arguments:

- `code_snippet`: Python code that defines one or more MCP tools using `@mcp.tool` decorators
- `server_name`: Name for the new MCP server (alphanumeric with optional hyphens)
- `description`: Optional description for the server
- `author`: Optional author name for the server

Example:

```python
<use_mcp_tool>
<server_name>mcpservercreator</server_name>
<tool_name>create_mcp_server</tool_name>
<arguments>
{
  "code_snippet": "@mcp.tool\ndef add_numbers(a: int, b: int) -> int:\n    \"\"\"Add two numbers together.\"\"\"\n    return a + b",
  "server_name": "simple-calculator",
  "description": "A simple calculator MCP server",
  "author": "Your Name"
}
</arguments>
</use_mcp_tool>
```

This will create a new MCP server named `simple-calculator` with a single tool that adds two numbers.

### Listing Installed Servers

To list all installed MCP servers, use the `list_installed_servers` tool:

```python
<use_mcp_tool>
<server_name>mcpservercreator</server_name>
<tool_name>list_installed_servers</tool_name>
<arguments>
{}
</arguments>
</use_mcp_tool>
```

## Security Notes

The server has built-in security features to prevent potentially harmful code execution:

- Code snippets are analyzed using Python's abstract syntax tree (AST)
- Potentially dangerous imports are blocked
- System operations like `os.system` and `subprocess` are not allowed
- File operations like `open()` and `Path.unlink()` are restricted

## Important Notes

1. After creating a new server, you must restart VS Code completely for it to be recognized.
2. The generated servers will be installed in stdio transport mode.
3. All generated servers are installed at `/tmp/generated_mcp_servers` by default.

## Example: Creating a Weather API Server

Here's a more complex example to create a weather API server:

```python
<use_mcp_tool>
<server_name>mcpservercreator</server_name>
<tool_name>create_mcp_server</tool_name>
<arguments>
{
  "code_snippet": "import requests\n\n@mcp.tool\ndef get_weather(city: str) -> dict:\n    \"\"\"Get the current weather for a city.\"\"\"\n    api_key = \"your_api_key_here\"\n    url = f\"https://api.example.com/weather?city={city}&appid={api_key}\"\n    \n    response = requests.get(url)\n    if response.status_code == 200:\n        return response.json()\n    else:\n        return {\"error\": f\"Failed to get weather: {response.status_code}\"}\n",
  "server_name": "weather-api",
  "description": "MCP server for querying weather data",
  "author": "Weather Expert"
}
</arguments>
</use_mcp_tool>
```

Note: The above example uses `requests` which would need to be added to the generated server's requirements.txt file manually.
