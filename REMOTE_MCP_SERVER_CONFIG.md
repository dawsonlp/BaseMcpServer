# Remote MCP Server Configuration Guide

## Overview
This document explains how to properly configure remote MCP servers in Cline using the SSE (Server-Sent Events) transport.

## Configuration Format

### For Remote HTTP/HTTPS Servers
Use the SSE transport format with a `url` field:

```json
{
  "mcpServers": {
    "remote-server-name": {
      "url": "http://localhost:8001/mcp",
      "disabled": false,
      "autoApprove": ["tool1", "tool2"]
    }
  }
}
```

### For Local STDIO Servers
Use the command format:

```json
{
  "mcpServers": {
    "local-server-name": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "API_KEY": "your_api_key"
      },
      "disabled": false,
      "autoApprove": ["tool1", "tool2"]
    }
  }
}
```

## Key Differences

| Transport | Use Case | Configuration |
|-----------|----------|---------------|
| **SSE** | Remote servers over HTTP/HTTPS | `"url": "http://server/mcp"` |
| **STDIO** | Local servers via command line | `"command": "python", "args": [...]` |

## Common Configuration Options

- `disabled`: Boolean to enable/disable the server
- `autoApprove` / `alwaysAllow`: Array of tool names to auto-approve (see note below)
- `headers`: (SSE only) HTTP headers for authentication
- `env`: (STDIO only) Environment variables for the process

**⚠️ Field Name Inconsistency:** The Cline documentation shows both `autoApprove` and `alwaysAllow` in different places. Based on current working configurations, `autoApprove` appears to be the standard, but both may be supported. Use `autoApprove` for consistency with existing servers.

## Examples

### Remote Streamable HTTP Server
```json
{
  "mcpServers": {
    "test-mcp-server": {
      "url": "http://localhost:8001/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Remote Server with Authentication
```json
{
  "mcpServers": {
    "authenticated-server": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-token"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Local Python Server
```json
{
  "mcpServers": {
    "local-python-server": {
      "command": "python",
      "args": ["/Users/username/servers/my-server/server.py"],
      "env": {
        "PORT": "8001",
        "API_KEY": "secret"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Troubleshooting

### Schema Validation Errors
- Ensure you're using the correct format (SSE vs STDIO)
- Don't mix `url` with `command`/`args`
- Use `autoApprove` for tool permissions (correct field name)

### Connection Issues
- Verify the server is running and accessible
- Check firewall settings for remote servers
- Ensure the `/mcp` endpoint is properly mounted
- Test with curl: `curl -X POST http://localhost:8001/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`

### Authentication Problems
- Use `headers` field for HTTP authentication (not `apiKey`)
- Use `env` field for environment-based auth in STDIO servers
- Store sensitive tokens securely, not in the config file

## MCP-Manager Integration

The `mcp-manager` utility has been updated to generate correct Cline configurations:

### Fixed Issues:
- ✅ Kept `autoApprove` (correct field name)
- ✅ Changed `apiKey` → `headers: {"Authorization": "Bearer ..."}`
- ✅ Made authentication headers conditional

### Usage:
```bash
# The mcp-manager now generates correct configs for both local and remote servers
mcp-manager configure
```

## Best Practices

1. **Use STDIO for local development** - faster and more secure
2. **Use SSE for production deployments** - allows centralized hosting
3. **Always test connectivity** before adding to production config
4. **Use `autoApprove` sparingly** - only for trusted, safe tools
5. **Document your server endpoints** and required authentication
6. **Use mcp-manager** - it now generates correct configurations automatically
