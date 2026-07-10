---
name: install-mcp-server
description: >-
  Install a BaseMcpServer MCP server (loadbearing-youtube, worldcontext,
  jira-helper, mcpservercreator) via mcp-manager and wire it into Claude
  Desktop / Cline. Use when the user wants to install, add, set up, or enable
  one of these MCP servers — for example the loadbearing-youtube tool that
  extracts a YouTube transcript and exposes its load-bearing components.
---

# Install a BaseMcpServer MCP server

This skill installs one of the MCP servers in the `dawsonlp/BaseMcpServer`
monorepo into the user's `mcp-manager` registry and (optionally) wires it into
Claude Desktop / Cline. It works whether or not the repo is already cloned.

## Server catalog

| Server | What it gives the agent | Needs config? |
|---|---|---|
| `loadbearing-youtube` | Extract a YouTube transcript and expose its **load-bearing components** (`analyze_video`, `get_video_transcript`, `list_analysis_providers`). | No — defaults to local Ollama. Optional OpenAI/Anthropic keys. |
| `worldcontext` | Current date/time, market, news, dev-tool versions. | Optional API keys for market/news. |
| `jira-helper` | Jira + Confluence integration. | **Yes** — Jira URL + credentials. |
| `mcpservercreator` | Scaffold new MCP servers from a code snippet. | No. |

## Fast path (recommended)

Run the bundled installer. It ensures `uv` + `mcp-manager` exist, locates the
server source (or shallow-clones the public repo), installs it, and syncs.

```bash
# from anywhere:
bash scripts/install_mcp_server.sh loadbearing-youtube
```

Useful flags:
- `--no-sync` — register the server but don't touch editor settings yet.
- `--force` — reinstall an already-installed server.
- `--transport sse` — install as an HTTP/SSE server instead of stdio.
- `--source DIR` — install from a specific local checkout.

> **Ask before syncing to editors.** `mcp-manager config sync` edits the user's
> Claude Desktop / Cline settings files (persistent app configuration). If the
> user only asked to "install" the server, run with `--no-sync` first, then
> confirm before syncing.

## Manual path (if you want to run the steps yourself)

```bash
# 1. One-time: uv + mcp-manager
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install "git+https://github.com/dawsonlp/BaseMcpServer.git#subdirectory=utils/mcp_manager"
uv tool update-shell

# 2. Get the repo (skip if already cloned; then cd into it)
git clone --depth 1 https://github.com/dawsonlp/BaseMcpServer.git
cd BaseMcpServer

# 3. Install the server (isolated uv env under ~/.config/mcp-manager/servers/<name>/)
mcp-manager install local loadbearing-youtube --source ./servers/loadbearing-youtube

# 4. (If the server needs credentials) edit its config, then sync into editors
$EDITOR ~/.config/mcp-manager/servers/loadbearing-youtube/config.yaml   # not needed for loadbearing-youtube
mcp-manager config sync
```

## Configuration notes

- Install copies `config.yaml.example` → `~/.config/mcp-manager/servers/<name>/config.yaml`.
- `loadbearing-youtube` works out of the box against a local **Ollama** daemon
  (no API key). To use a cloud model instead, set `analysis.provider` /
  `analysis.model` in that config, and export `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`.
- `jira-helper` requires real Jira credentials before it will work — edit its
  config before syncing.

## Verify

```bash
mcp-manager info list                    # server should appear as installed
mcp-manager info show loadbearing-youtube # details + config path
```

After a `config sync`, restart Claude Desktop / reload the VS Code window so the
client picks up the new server. The agent should then see tools like
`analyze_video`.

## Uninstall / redo

```bash
mcp-manager remove loadbearing-youtube   # reversible; then config sync again
```

## Troubleshooting

- **`mcp-manager: command not found`** after install → run `uv tool update-shell`
  and open a new shell.
- **`uv is required but was not found`** → install uv (step 1) and re-run.
- **`Server '<name>' already exists`** → add `--force` to reinstall.
- **loadbearing-youtube analysis errors about Ollama** → ensure `ollama serve`
  is running, or switch the provider to OpenAI/Anthropic in its config.
- The server installs from a pinned git dependency, so the machine needs network
  access to GitHub the first time.
