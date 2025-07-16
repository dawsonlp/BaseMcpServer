# MCP Server Compatibility with Cline

## Overview
This guide provides essential information for developing MCP servers that work reliably with Cline, based on documented compatibility issues and best practices.

## Critical Reference
**Primary Issue Tracker**: [Fix MCP System Issues and Compatibility Problems #4391](https://github.com/cline/cline/issues/4391)

This comprehensive GitHub issue consolidates 40+ MCP-related problems affecting Cline's Model Context Protocol functionality. All MCP server developers should review this issue for the latest compatibility information.

## Transport Compatibility

### ✅ Working Transports
- **STDIO Transport** (Local servers via command line) - Most reliable
- **SSE Transport** (Server-Sent Events for remote servers) - Recommended for HTTP

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

### Configuration Issues
- **Schema Validation Breaking** - Updates break existing configurations
- **Missing transportType Field** - Causes server configuration failures
- **Environment Variable Problems** - PATH inheritance and $HOME not defined issues
- **Cross-Platform Path Issues** - Hardcoded Documents/Cline/MCP path problems

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

### 3. Error Handling
- Implement robust connection retry logic
- Handle 'MCP error -32000: Connection closed' gracefully
- Provide clear error messages for debugging

### 4. Cross-Platform Compatibility
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

## Version Compatibility

### Cline Versions with Known Issues
- **v3.17.5+**: HTTP transport regression
- **v3.17.10**: Remote MCP server issues
- **Current**: Multiple ongoing compatibility problems

### Recommendations
- Test with multiple Cline versions
- Monitor issue #4391 for updates
- Have fallback strategies for broken features

## Getting Help

1. **Check Issue #4391** - Comprehensive issue tracker
2. **Test with MCP Inspector** - Verify server works outside Cline
3. **Use SSE Transport** - Most reliable option currently
4. **Report New Issues** - Help improve Cline's MCP support

## Summary

MCP server development for Cline requires careful attention to transport selection, configuration format, and known compatibility issues. Use SSE transport, avoid StreamableHttpTransport, and implement robust error handling. Monitor the GitHub issue tracker for updates and fixes.

The MCP ecosystem is rapidly evolving, and many of these issues are being actively addressed by the Cline development team.
