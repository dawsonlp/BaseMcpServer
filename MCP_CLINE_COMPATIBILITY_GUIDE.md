# MCP Server Compatibility Guide for Cline

## Overview
This guide provides essential information for developing MCP servers that work reliably with Cline, based on known issues and compatibility problems documented in the Cline project.

## Critical Reference
**Primary Issue Tracker**: [Fix MCP System Issues and Compatibility Problems #4391](https://github.com/cline/cline/issues/4391)

This comprehensive GitHub issue consolidates 40+ MCP-related problems affecting Cline's Model Context Protocol functionality. All MCP server developers should review this issue for the latest compatibility information.

## Transport Compatibility

### ✅ Working Transports
- **STDIO Transport** (Local servers via command line)
- **SSE Transport** (Server-Sent Events for remote servers)

### ❌ Broken Transports
- **StreamableHttpTransport** - [Issue #3315](https://github.com/cline/cline/issues/3315)
  - Cline sends GET requests instead of required POST requests
  - Use SSE transport as workaround for HTTP-based servers

## Major Compatibility Issues

### Remote Server Problems
- **HTTP Transport Regression** (v3.17.5+) - Previously working remote servers now fail
- **Authorization Headers Not Sent** - Bearer tokens configured but not transmitted
- **User-Agent Header Issues** - Set to 'node' instead of proper Cline identification
- **SSE Connection Timeouts** - TCP connections close after 5 minutes
- **Request Failures** - Various HTTP status codes (503, etc.)

### Configuration and Schema Issues
- **Schema Validation Breaking** - Updates break existing configurations
- **Missing transportType Field** - Causes server configuration failures
- **Environment Variable Problems** - PATH inheritance and $HOME not defined issues
- **Cross-Platform Path Issues** - Hardcoded Documents/Cline/MCP path problems
- **Character Encoding Issues** - Non-ASCII folder names on Japanese Windows

### Installation and Startup Problems
- **Timeout Settings Ignored** - Server initialization timeouts not respected
- **Node.js Version Compatibility** - Version detection and compatibility issues
- **Windows-Specific Errors** - spawn EINVAL errors with npx.cmd files
- **NVM Compatibility Issues** - Problems with Node Version Manager
- **VSCodium Incompatibility** - Alternative VS Code distributions not supported
- **Python Server Issues** - Module import errors and environment setup problems

### Tool and Resource System Issues
- **Server Names Show 'undefined'** - In system prompts for SSE servers
- **Tool Execution Failures** - Due to incorrect server name resolution
- **Image Content Not Supported** - Base64 images show 'Empty Response'
- **Marketplace Proxy Issues** - Corporate proxy environments fail

## Recommended Development Practices

### 1. Transport Selection
```python
# ✅ RECOMMENDED: Use SSE transport for remote servers
mcp.run(transport="sse")

# ❌ AVOID: StreamableHttpTransport is broken
# mcp.run(transport="streamable-http")  # Don't use this
```

### 2. Configuration Format
```json
{
  "mcpServers": {
    "your-server": {
      "url": "http://localhost:8000/sse",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 3. Environment Variable Handling
- Don't rely on common environment variables being passed
- Explicitly configure required environment variables
- Test with minimal environment setups

### 4. Error Handling
- Implement robust connection retry logic
- Handle 'MCP error -32000: Connection closed' gracefully
- Provide clear error messages for debugging

### 5. Cross-Platform Compatibility
- Avoid hardcoded paths
- Test on Windows, macOS, and Linux
- Handle character encoding properly
- Support both regular VS Code and VSCodium

## Testing Your MCP Server

### 1. Use MCP Inspector First
Always test with the official MCP Inspector before testing with Cline:
```bash
npx @modelcontextprotocol/inspector
```

### 2. Test Multiple Transports
- Test STDIO transport for local development
- Test SSE transport for remote deployment
- Avoid StreamableHttpTransport entirely

### 3. Test Configuration Scenarios
- Test with minimal configuration
- Test with authorization headers
- Test timeout scenarios
- Test connection recovery

## Known Working Examples

### Minimal SSE Server (FastMCP)
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("YourServer")

@mcp.tool()
def your_tool(param: str) -> str:
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run(transport="sse")  # Use SSE, not streamable-http
```

### STDIO Server Configuration
```json
{
  "mcpServers": {
    "local-server": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "API_KEY": "your_api_key"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Troubleshooting Common Issues

### "MCP error -32000: Connection closed"
- Check server is actually running and accessible
- Verify correct transport type (SSE vs STDIO)
- Check for environment variable issues
- Ensure proper error handling in server code

### "StreamableHttpTransport not working"
- Switch to SSE transport immediately
- Update configuration to use `/sse` endpoint
- This is a known Cline bug, not your server

### Authorization headers not sent
- Known issue in Cline versions 3.17.5+
- May require server-side workarounds
- Monitor issue #4391 for fixes

### Server installation failures
- Check Node.js version compatibility
- Verify NVM setup if using Node Version Manager
- Test with VSCodium if using alternative VS Code
- Check for Windows-specific spawn issues

## Version Compatibility

### Cline Versions with Known Issues
- **v3.17.5+**: HTTP transport regression
- **v3.17.10**: Remote MCP server issues
- **Current**: Multiple ongoing compatibility problems

### Recommendations
- Test with multiple Cline versions
- Monitor issue #4391 for updates
- Have fallback strategies for broken features

## Future Considerations

The Cline team is actively working on fixing these issues. Key areas of improvement include:

1. **StreamableHttpTransport Support** - Proper POST request handling
2. **Authorization Header Forwarding** - Fixing header transmission
3. **Cross-Platform Path Resolution** - Better folder handling
4. **Environment Variable Inheritance** - Proper variable passing
5. **Image Content Support** - Base64 image processing
6. **Error Message Improvements** - Better debugging information

## Getting Help

1. **Check Issue #4391** - Comprehensive issue tracker
2. **Test with MCP Inspector** - Verify server works outside Cline
3. **Use SSE Transport** - Most reliable option currently
4. **Report New Issues** - Help improve Cline's MCP support

## Summary

MCP server development for Cline requires careful attention to transport selection, configuration format, and known compatibility issues. Use SSE transport, avoid StreamableHttpTransport, and implement robust error handling. Monitor the GitHub issue tracker for updates and fixes.

The MCP ecosystem is rapidly evolving, and many of these issues are being actively addressed by the Cline development team.
