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

---

## Protocol Delimiter Collision Risk

### What It Is

Cline injects XML-style tags (e.g., `<environment_details>`) into its internal context pipeline when
processing MCP tool results. If a tool response payload contains the same literal string, the Cline
parser treats it as a context injection point and silently truncates the tool result at that position.
The AI receives no result and may retry the call repeatedly, causing session degradation.

### What Triggers It

User-generated text fields returned in tool responses -- Jira ticket summaries, descriptions, comment
bodies, and Confluence page titles and content -- may contain angle bracket sequences if users have
pasted terminal output, IDE snippets, HTML templates, or prior Cline session content into ticket fields.

The failure is data-dependent and intermittent. It resolves on retry only if the retry happens to
return a different page of results that does not include the offending content.

### Protection in jira-helper (v2.1.0+)

jira-helper applies HTML entity escaping to all user-authored string fields before returning them in
tool responses. The character `<` is replaced with `&lt;` in:

- Jira issue `summary` (all tools)
- Jira issue `description` (`get_issue_details`, `get_full_issue_details`)
- Jira comment `body` (`get_full_issue_details`)
- Linked issue `summary` embedded in `get_full_issue_details` responses
- Confluence page `title` (`list_confluence_pages`, `get_confluence_page`, `search_confluence_pages`)
- Confluence page `body` (`get_confluence_page`)

Structural metadata fields (status names, assignee names, project keys, issue keys, dates, labels,
component names) are not altered -- these values come from Jira's controlled vocabulary and do not
contain angle brackets.

### Known Limitation: Confluence Body Entity-Escaping

`get_confluence_page` returns the page body with `<` replaced by `&lt;`. The AI reads this content
correctly for analysis and summarization purposes.

If a use case requires verbatim Confluence HTML to be written back to Confluence unchanged (read,
modify, write-back), the caller must reverse the entity escaping before passing the body to
`update_confluence_page` or `create_confluence_page`. Input parameters to write operations are
never sanitized -- only output fields are affected.

### Protection Coverage and Remaining Risk

The escaping protects against the known trigger class (angle bracket sequences in user-authored
fields) for the standard jira-helper tools. It does not protect against:

- Custom fields that may contain user-authored text returned via `raw_data=True` in
  `get_full_issue_details` (raw mode returns the unprocessed Jira API response)
- Future Cline protocol markers that do not use angle bracket syntax

### Workaround (Pre-fix or Raw Mode)

If the collision recurs in raw mode or via a future protocol marker:
- Use `max_results=5` or `max_results=10` to reduce the number of tickets returned per call
- Use `get_issue_details` for a specific known ticket key rather than bulk search
- Avoid pasting Cline session output directly into Jira ticket description fields
