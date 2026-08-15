# BaseMcpServer

A monorepo of [Model Context Protocol](https://modelcontextprotocol.io/) servers plus the `mcp-manager` CLI that installs and configures them.

## What's in this repo

```
BaseMcpServer/
├── utils/mcp_manager/         # CLI for installing + managing MCP servers (canonical install path)
├── servers/
│   ├── jira-helper/           # Jira + Confluence integration server (multi-instance)
│   ├── worldcontext/          # Current-context tools (date/time, market, news, dev-tool versions)
│   ├── mcpservercreator/      # Generator that scaffolds new MCP servers from a code snippet
│   ├── loadbearing-youtube/   # Extract a YouTube transcript + expose its load-bearing components
│   └── template/              # Starter scaffold to fork when building a new server
├── docs/
│   ├── adr/                   # Architecture Decision Records
│   ├── developer/             # Implementation guides (build a new MCP server, client support, etc.)
│   └── user/                  # End-user docs (Cline compatibility, etc.)
└── QUICKSTART.md              # End-to-end jira-helper onboarding
```

Every server in this repo is a Python package installable via `mcp-manager install`, gets its own isolated [`uv`](https://docs.astral.sh/uv/)-managed environment under `~/.config/mcp-manager/servers/<name>/.venv`, and can be wired into supported MCP clients with a single `mcp-manager sync` call. The repository currently supports and tests macOS and Linux; Windows is explicitly out of scope.

## Quick install

```bash
# 1. One-time: install uv and mcp-manager
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install "git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager"
uv tool update-shell

# 2. Install whichever servers you want
mcp-manager install jira-helper        --source ./servers/jira-helper
mcp-manager install worldcontext       --source ./servers/worldcontext
mcp-manager install mcpservercreator   --source ./servers/mcpservercreator
mcp-manager install loadbearing-youtube --source ./servers/loadbearing-youtube

# 3. Edit the per-server config files (where credentials go) — see each server's README
$EDITOR ~/.config/mcp-manager/servers/jira-helper/config.yaml

# 4. Wire the servers into installed supported clients
mcp-manager sync
```

For an end-to-end walkthrough with jira-helper (including Atlassian API token setup), see [QUICKSTART.md](QUICKSTART.md).

## Building a new MCP server

Fork [`servers/template/`](servers/template/) and follow the README inside it. Every server uses MCP Python SDK v2 directly: a `create_server()` factory constructs `MCPServer`, then registers plain tool functions through `add_tool()`. Decorator-based registration and MCP Commons are not used.

Detailed reference: [`docs/developer/BUILD_A_NEW_MCP.md`](docs/developer/BUILD_A_NEW_MCP.md).

For dynamically generating a server from a code snippet, see the [`mcpservercreator`](servers/mcpservercreator/) server itself, once installed.

## Connecting clients

```bash
mcp-manager sync      # sync every detected supported client
# or selectively:
mcp-manager sync --platform cline
mcp-manager sync --platform codex
```

`mcp-manager` supports Cline, Claude Desktop, Claude Code, VS Code native MCP, Codex, and Antigravity. It writes or delegates stdio entries that point at the executable in each server's managed environment. Restart the affected client for new entries to take effect.

Example entry (written automatically; shown for reference):
```json
{
  "mcpServers": {
    "jira-helper": {
      "command": "/Users/<you>/.config/mcp-manager/servers/jira-helper/.venv/bin/jira-helper",
      "args": ["stdio"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Hand-added entries in your editor's settings file are preserved across `sync` — only entries that match a server name in the mcp-manager registry are overwritten.

## Architecture decisions

The major directional choices are tracked under [`docs/adr/`](docs/adr/):
- [ADR-003](docs/adr/ADR-003-uv-standardization.md) — current: all server installs go through `uv`
- [ADR-002](docs/adr/ADR-002-pipx-default-installation.md) — superseded; documents the earlier pipx-default attempt

## License

[MIT License](LICENSE)
