# Jira Helper MCP Server Documentation

## Overview

The Jira Helper MCP Server provides comprehensive Jira integration capabilities through the Model Context Protocol (MCP). It offers a clean, hexagonal architecture with robust search functionality, issue management, and workflow operations.

## Documentation Structure

### For Users
- **[Getting Started](user/getting-started.md)** - Quick setup and basic usage
- **[Available Tools](user/available-tools.md)** - Complete tool reference
- **[Configuration](user/configuration.md)** - Setup and configuration guide
- **[Troubleshooting](user/troubleshooting.md)** - Common issues and solutions

### For Developers
- **[Architecture Overview](developer/architecture.md)** - System design and patterns
- **[Development Setup](developer/development-setup.md)** - Local development environment
- **[Testing Guide](developer/testing.md)** - Testing strategies and tools
- **[Extension Guide](developer/extensions.md)** - Adding new functionality

### Architecture Documentation
- **[Hexagonal Architecture](architecture/hexagonal-design.md)** - Core architectural patterns
- **[Search System](architecture/search-system.md)** - Search functionality design
- **[MCP Integration](architecture/mcp-integration.md)** - MCP protocol implementation

## Quick Start

1. **Install**: `mcp-manager install local jira-helper --source servers/jira-helper --force`
2. **Configure**: Copy `config.yaml.example` to `config.yaml` and add your Jira details
3. **Test**: Use any MCP-compatible client to access the tools

## Key Features

- **Comprehensive Search**: Advanced JQL and filter-based search capabilities
- **Issue Management**: Create, update, transition, and manage Jira issues
- **Time Tracking**: Log work, manage estimates, and track time
- **Workflow Operations**: Handle issue transitions and workflow management
- **Security**: Built-in JQL injection prevention and input validation
- **Performance**: Optimized for large result sets and complex queries

## Architecture Highlights

- **Hexagonal Architecture**: Clean separation of concerns
- **DRY Principle**: Eliminated duplicate code through refactoring
- **Security First**: Input validation and sanitization throughout
- **Production Ready**: Thoroughly tested with real Jira instances

---

**Last Updated**: January 2025  
**Version**: 2.0.0  
**Maintainer**: Development Team
