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

You can install MCP Manager globally using uv:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install MCP Manager globally from this checkout
uv tool install ./utils/mcp_manager

# Or directly from the repository
uv tool install "git+https://github.com/dawsonlp/BaseMcpServer.git@v1.0.4#subdirectory=utils/mcp_manager"

# Ensure uv's tool executable directory is on your PATH
uv tool update-shell
```

You can also install MCP Manager globally using pipx:

```bash
# Install pip and pipx if you don't have them
pip install --user pipx
pipx ensurepath

# Install MCP Manager globally from this checkout
pipx install ./utils/mcp_manager

# Or directly from the repository
pipx install git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager
```

After installation, you can use the `mcp-manager` command globally:

```bash
mcp-manager --help
```

**Note:** For backward compatibility, `mcpmanager` (without hyphen) still works as an alias.

## Usage

### Configuration Status Dashboard

Get a comprehensive view of your MCP configuration:

```bash
# View configuration status with rich formatting  
mcp-manager info system
```

This shows:
- VS Code/Cline and Claude Desktop configuration files status
- All configured servers with status indicators
- Management source identification (mcp-manager vs manual)
- Registry consistency analysis

### Installing a Local MCP Server

Local servers are installed into isolated per-server environments under `~/.config/mcp-manager/servers/`.
For package-based servers, MCP Manager installs the package into that environment so editor integrations can run the server executable directly.

```bash
# Install from a local directory (default: isolated package installation)
mcp-manager install local example-server --source ./example

# Use the legacy source-copy virtual environment flow instead
mcp-manager install local example-server --source ./example --no-pipx

# Install from a Git repository
mcp-manager install git jira-server --repo https://github.com/username/repo --path path/to/server
```

**Requirements**: 
- For default package installation: `pyproject.toml` file is required in the server directory
- For `--no-pipx` source-copy installation: `requirements.txt` or `pyproject.toml` file is required

**Note:** The default local-server installer currently uses MCP Manager's own per-server virtual environment and `pip` internally. The `--no-pipx` option name is retained for compatibility with earlier releases.

### Adding a Remote MCP Server

```bash
# Add a remote HTTP+SSE server
mcp-manager install remote remote-server --url http://remote-host:7501 --api-key your-api-key
```

### Listing Configured Servers

```bash
# List all configured servers
mcp-manager list

# List only local servers
mcp-manager list --type local

# List only remote servers  
mcp-manager list --type remote
```

### Running a Local Server

```bash
# Run with stdio transport (default)
mcp-manager server start example-server

# Run with HTTP+SSE transport
mcp-manager server start example-server --transport sse
```

### Configuring Editor Integration

```bash
# Configure VS Code Cline integration
mcp-manager config cline
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

## Migration Notes (v0.3.0)

**Breaking Change**: Default installation method changed from source-copy virtual environments to isolated package installation.

### For Existing Users

- **Existing servers**: All previously installed servers continue to work normally
- **New installations**: Now default to isolated package installation (requires `pyproject.toml`)
- **Migration path**: Use `--no-pipx` flag if your server lacks `pyproject.toml`

### Example Migration

```bash
# Before v0.3.0
mcp-manager install local my-server --source ./my-server

# v0.3.0+ (default - isolated package installation, requires pyproject.toml)
mcp-manager install local my-server --source ./my-server

# v0.3.0+ (if no pyproject.toml - source-copy virtual environment)
mcp-manager install local my-server --source ./my-server --no-pipx
```

### Benefits of New Default
- **Better Isolation**: Complete isolation from system Python
- **Easier Management**: Cleaner upgrades and dependency handling
- **Modern Standards**: Follows current Python packaging best practices

## VS Code Cline Integration

MCP Manager automatically configures VS Code Cline integration by updating the settings file at:

```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

This allows Cline to connect to your MCP servers directly from VS Code. Use `mcp-manager info system` to verify your configuration status.

## Commands Reference

| Command | Description |
|---------|-------------|
| `mcp-manager info system` | Show comprehensive configuration status with Rich formatting |
| `mcp-manager install local <name> --source <path>` | Install local MCP server with isolated package environment |
| `mcp-manager install local <name> --source <path> --no-pipx` | Install local MCP server with source-copy virtual environment |
| `mcp-manager list` | List all configured servers |
| `mcp-manager server start <server>` | Run a local server |
| `mcp-manager config cline` | Configure VS Code Cline integration |
| `mcp-manager --help` | Show detailed help and examples |

## Quick Start

For detailed setup instructions including jira-helper configuration, see the [Quick Start Guide](../../QUICKSTART.md).

## License

MIT
