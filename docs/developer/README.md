# Developer Documentation

This directory contains technical documentation for developers building and extending MCP servers in the BaseMcpServer project.

## Available Documentation

### [Build Your Own MCP Server](BUILD_A_NEW_MCP.md)
Complete guide for creating new MCP (Model Context Protocol) servers, including setup, development patterns, and best practices.

### [MCP Result Adapter](mcp-result-adapter.md)
Technical documentation for the MCP result adapter system, including implementation details and usage patterns.

## Architecture & Patterns

This project follows hexagonal (ports-and-adapters) architecture principles:

- **Domain Layer**: Core business logic and models
- **Application Layer**: Use cases and service orchestration  
- **Infrastructure Layer**: External integrations (databases, APIs)
- **Adapters Layer**: Protocol-specific implementations (MCP, HTTP)

## Development Workflow

1. **Setup**: Use the server template in `servers/template/` as a starting point
2. **Architecture**: Follow domain-driven design principles
3. **Testing**: Separate unit tests from integration tests
4. **Documentation**: Update relevant docs and ADRs for architectural decisions

## Related Resources

- [Architectural Decision Records](../adr/) - Historical architecture decisions
- [User Documentation](../user/) - End-user guides and tutorials
- [Project Structure Overview](../../readme.md) - Overall project architecture

## Server-Specific Documentation

Individual MCP servers may have their own documentation in their respective directories:

- `servers/jira-helper/docs/` - Jira Helper MCP server
- `servers/document-processor/` - Document processing server
- `servers/worldcontext/` - World context server

## Tools and Utilities

- **mcp-manager**: Tool for managing MCP server installations and configurations
- **mcpservercreator**: Utility for generating new MCP servers from code snippets
