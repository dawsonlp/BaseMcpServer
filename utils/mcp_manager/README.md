# MCP Manager

A comprehensive command-line tool for managing Model Context Protocol (MCP) servers.

## Features

- **Config Status Dashboard** - View comprehensive MCP configuration status across VS Code/Cline and Claude Desktop
- Install and manage local MCP servers with isolated environments
- Configure connections to remote MCP servers
- Generate wrapper scripts for stdio-based MCP servers
- Automatically configure VS Code Cline integration
- Support for both stdio and HTTP+SSE transport modes
- **XDG Compliant** - Centralized management under `~/.config/mcp-manager`
- **Automatic Migration** - Seamlessly migrates existing configurations

## Installation

You can install MCP Manager globally using pipx:

```bash
# Install pip and pipx if you don't have them
pip install --user pipx
pipx ensurepath

# Install MCP Manager globally (recommended)
pipx install ./utils/mcp_manager

# Or directly from the repository
pipx install git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager
```

After installation, you can use the shorter `mcpmanager` command globally:

```bash
mcpmanager --help
```

## Usage

### Configuration Status Dashboard

Get a comprehensive view of your MCP configuration:

```bash
# View configuration status with rich formatting
mcpmanager config-info
```

This shows:
- VS Code/Cline and Claude Desktop configuration files status
- All configured servers with status indicators
- Management source identification (mcp-manager vs manual)
- Registry consistency analysis

### Installing a Local MCP Server

```bash
# Install from a local directory
mcpmanager install local example-server --source ./example

# Install from a Git repository  
mcpmanager install git jira-server --repo https://github.com/username/repo --path path/to/server
```

### Adding a Remote MCP Server

```bash
# Add a remote HTTP+SSE server
mcpmanager add remote-server --url http://remote-host:7501 --api-key your-api-key
```

### Listing Configured Servers

```bash
# List all configured servers
mcpmanager list

# List only local servers
mcpmanager list --local

# List only remote servers  
mcpmanager list --remote
```

### Running a Local Server

```bash
# Run with stdio transport (default)
mcpmanager run example-server

# Run with HTTP+SSE transport
mcpmanager run example-server --transport sse
```

### Configuring Editor Integration

```bash
# Configure VS Code Cline integration
mcpmanager configure vscode
```

## Directory Structure

MCP Manager creates the following directory structure under `~/.config/mcp-manager/`:

```
~/.config/mcp-manager/
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

**Migration**: If you have existing configurations under `~/.mcp_servers/`, they will be automatically migrated to the new location on first run.

## VS Code Cline Integration

MCP Manager automatically configures VS Code Cline integration by updating the settings file at:

```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

This allows Cline to connect to your MCP servers directly from VS Code. Use `mcpmanager config-info` to verify your configuration status.

## Commands Reference

| Command | Description |
|---------|-------------|
| `mcpmanager config-info` | Show comprehensive configuration status with Rich formatting |
| `mcpmanager install local <name> --source <path>` | Install local MCP server |
| `mcpmanager list` | List all configured servers |
| `mcpmanager run <server>` | Run a local server |
| `mcpmanager configure vscode` | Configure VS Code Cline integration |
| `mcpmanager help` | Show detailed help and examples |

## Quick Start

For detailed setup instructions including jira-helper configuration, see the [Quick Start Guide](../../QUICKSTART.md).

## License

MIT
