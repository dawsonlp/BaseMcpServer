# MCP Manager

A comprehensive command-line tool for managing Model Context Protocol (MCP) servers.

## Features

- **Config Status Dashboard** - View comprehensive MCP configuration status across every supported agent
- Install and manage local MCP servers with isolated environments
- Configure connections to remote MCP servers
- Generate wrapper scripts for stdio-based MCP servers
- **One-command install into multiple AI agents** - Cline, Claude Desktop, Claude Code, VS Code (native MCP), and Codex
- Support for both stdio and HTTP+SSE transport modes
- **XDG Compliant** - Centralized management under `~/.config/mcp-manager`
- **Automatic Migration** - Seamlessly migrates existing configurations

## Installation

MCP Manager is distributed as a [uv](https://docs.astral.sh/uv/) tool. Internally it installs every managed MCP server into its own uv-managed environment, so a working `uv` on `PATH` is a hard requirement.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install MCP Manager globally from this checkout
uv tool install ./utils/mcp_manager

# Or directly from the repository
uv tool install "git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager"

# Ensure uv's tool executable directory is on your PATH
uv tool update-shell
```

After installation:

```bash
mcp-manager --help
```

`mcpmanager` (without the hyphen) is registered as an alias for the same command.

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

Local servers are installed into isolated per-server environments under `~/.config/mcp-manager/servers/<name>/.venv` using [uv](https://docs.astral.sh/uv/). The server's package is installed into that environment so editor integrations can run the server executable directly.

```bash
# Install from a local directory containing a pyproject.toml
mcp-manager install local example-server --source ./example
```

**Requirements**:
- `uv` must be available on `PATH`
- A `pyproject.toml` file is required in the server directory

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
├── servers/                  # Per-server isolated environments
│   └── <server-name>/
│       ├── .venv/            # uv-managed virtual environment (the server is `uv pip install`ed here)
│       └── config.yaml       # Server-specific config / credentials (preserved across reinstall)
├── logs/                     # Per-server log files
└── config/
    └── servers.json          # Registry of installed servers
```

## Migration Notes (v1.2.0)

**Breaking Change**: Legacy state migrations and the `install from-template` / `list-templates` stub commands have been removed. Registry entries from pre-1.1.0 installs (`installation_type: "pipx"` or `"venv"`; `server_type: "local_stdio"`/`"local_sse"`/etc.) and data under `~/.mcp_servers/` are no longer auto-migrated.

On startup, any registry entries that fail to validate are skipped with a clear message instructing you to reinstall them:

```
mcp-manager install local <name> --source <path> --force
```

Per-server `config.yaml` files under `~/.config/mcp-manager/servers/<name>/` (API keys, credentials) **are preserved automatically** on reinstall — `install local --force` backs up and restores `config.yaml` so authentication details survive the migration.

### v1.1.0 (earlier)

The `--no-pipx` source-copy install flow was removed. Local servers are always installed as isolated packages using `uv`.

## Supported Agents

`mcp-manager config sync` pushes the registry into every installed agent it recognizes. Each server is written in the format that agent expects:

| Agent | Mechanism | Location |
|-------|-----------|----------|
| Cline (VS Code) | JSON file (`mcpServers`) | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` |
| Claude Desktop | JSON file (`mcpServers`) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Code | `claude mcp add` CLI (user scope) | `~/.claude.json` |
| VS Code (native MCP) | JSON file (`servers` + `type`) | `~/Library/Application Support/Code/User/mcp.json` |
| Codex | `codex mcp add` CLI | `~/.codex/config.toml` |

For file-based agents, entries you added by hand are preserved — only servers with a matching name are overwritten, and the file is backed up first. Claude Code and Codex keep MCP servers inside large, live-mutated config files, so mcp-manager delegates to their own `mcp add` / `mcp remove` CLIs rather than rewriting those files directly. Use `mcp-manager info system` to verify configuration status.

## Commands Reference

| Command | Description |
|---------|-------------|
| `mcp-manager info system` | Show comprehensive configuration status with Rich formatting |
| `mcp-manager info list` | List all configured servers |
| `mcp-manager install local <name> --source <path>` | Install local MCP server into an isolated uv-managed environment |
| `mcp-manager install remote <name> --url <url>` | Register a remote MCP server |
| `mcp-manager server start <name>` | Run a local server |
| `mcp-manager server stop <name>` | Stop a running server |
| `mcp-manager server restart <name>` | Restart a server |
| `mcp-manager config cline` | Write the registry to VS Code/Cline settings |
| `mcp-manager config claude` | Write the registry to Claude Desktop settings |
| `mcp-manager config claude-code` | Register the registry with Claude Code (`claude mcp add`, user scope) |
| `mcp-manager config vscode` | Write the registry to VS Code native MCP settings (`mcp.json`) |
| `mcp-manager config codex` | Register the registry with Codex (`codex mcp add`) |
| `mcp-manager config sync` | Push the registry to all installed AI agents |
| `mcp-manager config validate` | Validate every server's installation |
| `mcp-manager remove server <name>` | Remove a server completely from all locations |
| `mcp-manager remove from-cline <name>` | Remove a server from VS Code/Cline only |
| `mcp-manager remove from-claude <name>` | Remove a server from Claude Desktop only |
| `mcp-manager remove from-registry <name>` | Remove a server from the mcp-manager registry only |
| `mcp-manager --help` | Show detailed help and examples |

## Quick Start

For detailed setup instructions including jira-helper configuration, see the [Quick Start Guide](../../QUICKSTART.md).

## License

MIT
