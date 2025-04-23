# MCP Manager

A comprehensive command-line tool for managing Model Context Protocol (MCP) servers.

## Features

- Install and manage local MCP servers with isolated environments
- Configure connections to remote MCP servers
- Generate wrapper scripts for stdio-based MCP servers
- Automatically configure VS Code Cline integration
- Support for both stdio and HTTP+SSE transport modes
- Centralized management under ~/.mcp_servers

## Installation

You can install MCP Manager using pipx:

```bash
# Install pip and pipx if you don't have them
pip install --user pipx
pipx ensurepath

# Install MCP Manager
pipx install mcp-manager

# Or directly from the repository
pipx install git+https://github.com/yourusername/BaseMcpServer.git#subdirectory=utils/mcp_manager
```

## Usage

### Installing a Local MCP Server

```bash
# Install from a local directory
mcp-manager install local example-server --source ./example

# Install from a Git repository
mcp-manager install git jira-server --repo https://github.com/username/repo --path path/to/server
```

### Adding a Remote MCP Server

```bash
# Add a remote HTTP+SSE server
mcp-manager add remote-server --url http://remote-host:7501 --api-key your-api-key
```

### Listing Configured Servers

```bash
# List all configured servers
mcp-manager list

# List only local servers
mcp-manager list --local

# List only remote servers
mcp-manager list --remote
```

### Running a Local Server

```bash
# Run with stdio transport (default)
mcp-manager run example-server

# Run with HTTP+SSE transport
mcp-manager run example-server --transport sse
```

### Configuring Editor Integration

```bash
# Configure VS Code Cline integration
mcp-manager configure vscode
```

## Directory Structure

MCP Manager creates the following directory structure:

```
~/.mcp_servers/
├── servers/                  # Local server installations
│   ├── example-server/       
│   │   ├── .venv/            # Virtual environment
│   │   ├── src/              # Source code
│   │   └── meta.json         # Metadata
├── bin/                      # Generated wrapper scripts
│   ├── example-server.sh     # Wrapper for stdio mode
└── config/                   # Configuration
    ├── servers.json          # Server registry
    └── editors/              # Editor configurations
        └── vscode-cline.json # Generated VS Code Cline config
```

## VS Code Cline Integration

MCP Manager automatically configures VS Code Cline integration by updating the settings file at:

```
~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

This allows Claude to connect to your MCP servers directly from VS Code.

## License

MIT
