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
│   └── template/              # Starter scaffold to fork when building a new server
├── docs/
│   ├── adr/                   # Architecture Decision Records
│   ├── developer/             # Implementation guides (build a new MCP server, client support, etc.)
│   └── user/                  # End-user docs (Cline compatibility, etc.)
└── QUICKSTART.md              # End-to-end jira-helper onboarding
```

Every server in this repo is a Python package installable via `mcp-manager install local`, gets its own isolated [`uv`](https://docs.astral.sh/uv/)-managed environment under `~/.config/mcp-manager/servers/<name>/.venv`, and is wired into VS Code/Cline + Claude Desktop with a single `mcp-manager config sync` call.

## Quick install

```bash
# 1. One-time: install uv and mcp-manager
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install "git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager"
uv tool update-shell

# 2. Install whichever servers you want
mcp-manager install local jira-helper      --source ./servers/jira-helper
mcp-manager install local worldcontext     --source ./servers/worldcontext
mcp-manager install local mcpservercreator --source ./servers/mcpservercreator

# 3. Edit the per-server config files (where credentials go) — see each server's README
$EDITOR ~/.config/mcp-manager/servers/jira-helper/config.yaml

# 4. Wire the servers into Cline + Claude Desktop
mcp-manager config sync
```

For an end-to-end walkthrough with jira-helper (including Atlassian API token setup), see [QUICKSTART.md](QUICKSTART.md).

## Building a new MCP server

Fork [`servers/template/`](servers/template/) and follow the README inside it. The template gives you the same shared infrastructure as the other servers — bulk tool registration, config-file discovery, argv-driven transport dispatch, stdio-safe logging — all via [`mcp-commons`](https://pypi.org/project/mcp-commons/).

Detailed reference: [`docs/developer/BUILD_A_NEW_MCP.md`](docs/developer/BUILD_A_NEW_MCP.md).

For dynamically generating a server from a code snippet, see the [`mcpservercreator`](servers/mcpservercreator/) server itself, once installed.

## Connecting clients

```bash
mcp-manager config sync      # write to both Cline + Claude Desktop
# or selectively:
mcp-manager config cline
mcp-manager config claude
```

`mcp-manager` writes `mcpServers` entries that point at `~/.config/mcp-manager/servers/<name>/.venv/bin/<name>` over stdio. Restart your editor for the new entries to take effect.

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

Hand-added entries in your editor's settings file are preserved across `config sync` — only entries that match a server name in the mcp-manager registry are overwritten.

## Architecture decisions

The major directional choices are tracked under [`docs/adr/`](docs/adr/):
- [ADR-003](docs/adr/ADR-003-uv-standardization.md) — current: all server installs go through `uv`
- [ADR-002](docs/adr/ADR-002-pipx-default-installation.md) — superseded; documents the earlier pipx-default attempt

## License

[MIT License](LICENSE)
