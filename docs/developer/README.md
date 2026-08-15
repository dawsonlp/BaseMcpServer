# Developer Documentation

This directory contains technical documentation for developers building and extending MCP servers in the BaseMcpServer project.

## Available Documentation

### [MCP Python SDK v2 Upgrade Development Checklist](development-checklist.md)
Status-bearing implementation checklist for dependency upgrades, MCP v2 adoption,
verification, and managed local deployment.

### [Build Your Own MCP Server](BUILD_A_NEW_MCP.md)
Complete guide for creating new MCP (Model Context Protocol) servers, including setup, development patterns, and best practices.

### [MCP Python SDK v2 Conventions](mcp-v2-conventions.md)
Current contract, metadata, lifecycle, resource, HTTP security, and tool-behavior
rules for maintained and generated servers.

### [MCP Result Adapter](mcp-result-adapter.md)
Technical documentation for the MCP result adapter system, including implementation details and usage patterns.

### [MCP Client Support Research](mcp-client-support.md)
Historical research and configuration notes used while extending mcp-manager beyond its original Cline and Claude Desktop support. Treat the implementation and `utils/mcp_manager/README.md` as authoritative for current support.

## Architecture & Patterns

The maintained servers use a deliberately small structure: plain business
functions, a tool-registration map, and a direct MCP server factory. The
manager keeps its registry model separate from client-specific file and CLI
adapters. Do not introduce additional architectural layers without a concrete
behavioral need.

## Development Workflow

1. **Setup**: Use the server template in `servers/template/` as a starting point
2. **Architecture**: Preserve the direct SDK factory and explicit registration boundaries
3. **Testing**: Separate unit tests from integration tests
4. **Documentation**: Update relevant docs and ADRs for architectural decisions

## Related Resources

- [Architectural Decision Records](../adr/) - Historical architecture decisions
- [User Documentation](../user/) - End-user guides and tutorials
- [Project Structure Overview](../../readme.md) - Overall project architecture

## Server-Specific Documentation

Individual MCP servers may have their own documentation in their respective directories:

- `servers/jira-helper/docs/` - Jira Helper MCP server
- `servers/worldcontext/` - World context server

## Tools and Utilities

- **mcp-manager**: Tool for managing MCP server installations and configurations
- **mcpservercreator**: Utility for generating new MCP servers from code snippets
