# MCP Manager

A small command-line tool that installs local MCP servers into isolated
environments and syncs one registry into every AI client you use.

## What it does

- Installs a local MCP server into its own uv-managed environment.
- Keeps one registry (`~/.config/mcp-manager/config/servers.json`) as the single
  source of truth.
- Syncs that registry into Cline, Claude Desktop, Claude Code, VS Code (native
  MCP), Codex, and Antigravity — non-destructively (your hand-added entries are
  preserved).

## Installation

Distributed as a [uv](https://docs.astral.sh/uv/) tool. A working `uv` on `PATH`
is required (each managed server gets its own uv environment).

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install MCP Manager from this checkout...
uv tool install ./utils/mcp_manager
# ...or directly from the repository
uv tool install "git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager"

uv tool update-shell   # ensure uv's tool bin dir is on PATH
```

`mcpmanager` (no hyphen) is an alias for `mcp-manager`.

## Commands

Seven flat commands — run `mcp-manager <cmd> --help` for options.

| Command | Description |
|---------|-------------|
| `mcp-manager install <name> [--source DIR]` | Install a local server (source defaults to `./servers/<name>`) into an isolated uv env |
| `mcp-manager sync [--platform P]` | Push the registry into all installed AI clients (or one: `cline`, `claude`, `claude-code`, `vscode`, `codex`, `antigravity`) |
| `mcp-manager list` | List registered servers |
| `mcp-manager show <name>` | Show a server's details and config paths |
| `mcp-manager remove <name>` | Remove a server from the registry, every client, and disk |
| `mcp-manager validate [name]` | Validate server configuration |
| `mcp-manager version` | Show version and key paths |

## Typical flow

```bash
mcp-manager install worldcontext --source ./servers/worldcontext
$EDITOR ~/.config/mcp-manager/servers/worldcontext/config.yaml   # if it needs credentials
mcp-manager sync
```

Restart your editor for new entries to take effect.

## Directory structure

```
~/.config/mcp-manager/
├── servers/                  # per-server isolated environments
│   └── <name>/
│       ├── .venv/            # uv-managed venv (the server is `uv pip install`ed here)
│       └── config.yaml       # server config / credentials (preserved across reinstall)
└── config/
    └── servers.json          # registry of installed servers — the single source of truth
```

## Supported clients

`mcp-manager sync` writes each server in the format the client expects:

| Client | Mechanism | Location |
|--------|-----------|----------|
| Cline (VS Code) | JSON (`mcpServers`) | `.../globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` |
| Claude Desktop | JSON (`mcpServers`) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Code | `claude mcp add` (user scope) | `~/.claude.json` |
| VS Code (native MCP) | JSON (`servers` + `type`) | `~/Library/Application Support/Code/User/mcp.json` |
| Codex | `codex mcp add` | `~/.codex/config.toml` |
| Antigravity | JSON (`mcpServers`) | `~/.gemini/config/mcp_config.json` |

File-based clients: hand-added entries are preserved (only same-named servers
are overwritten, and the file is backed up first). Claude Code and Codex keep
MCP servers in large, live-mutated config files, so mcp-manager delegates to
their own `mcp add` / `mcp remove` CLIs.

## Quick Start

For an end-to-end walkthrough (including jira-helper credential setup), see the
[Quick Start Guide](../../QUICKSTART.md).

## License

MIT
