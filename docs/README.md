# BaseMcpServer Documentation

This directory contains all documentation for the BaseMcpServer project, organized for easy navigation.

## Documentation Structure

### 📖 [User Documentation](user/)
Documentation for end users of the MCP servers and tools.

### 🛠️ [Developer Documentation](developer/)
Technical documentation for developers building and extending MCP servers.

### 🏛️ [Architectural Decision Records (ADRs)](adr/)
Historical record of important architectural decisions made during development.

## Quick Links

- **Getting Started**: See [QUICKSTART.md](../QUICKSTART.md) in the project root
- **Project Overview**: See [readme.md](../readme.md) in the project root
- **Build Your Own MCP Server**: [Developer Guide](developer/BUILD_A_NEW_MCP.md)
- **Cline Compatibility**: [User Guide](user/cline-compatibility.md)

## Project Structure

```
BaseMcpServer/
├── readme.md                    # Project overview and introduction
├── QUICKSTART.md               # Quick setup and usage guide
├── docs/                       # All documentation (this directory)
│   ├── user/                   # End-user documentation
│   ├── developer/              # Technical/developer documentation
│   └── adr/                    # Architectural Decision Records
├── servers/                    # MCP server implementations
└── utils/                      # Utility tools (mcp-manager, etc.)
```

## Contributing to Documentation

When adding new documentation:

- **User guides** and tutorials → `docs/user/`
- **Technical specifications** and API docs → `docs/developer/`
- **Architecture decisions** → `docs/adr/`
- **In-progress bug reports** → live alongside the server they describe (e.g. `servers/jira-helper/BUG_*.md`)

Keep the main project `readme.md` and `QUICKSTART.md` in the root for immediate visibility.
