# MCP Server Template

Starter scaffold for a new MCP server. Mirrors the structure used by the other servers in this repo (`worldcontext`, `jira-helper`, `mcpservercreator`) so it gets the same shared infrastructure: bulk tool registration, config-file discovery, argv parsing, transport dispatch, and stdio-safe logging — all via [`mcp-commons`](https://pypi.org/project/mcp-commons/).

## What you get out of the box

```
servers/template/
├── pyproject.toml          # Package metadata + mcp-commons dependency
├── config.yaml.example     # Sample config (copied to ~/.config/mcp-manager/.../config.yaml on install)
├── README.md
└── src/
    ├── __init__.py
    ├── config.py           # 3-line config loader (mcp_commons.create_config)
    ├── main.py             # 6-line entry point (mcp_commons.run_cli)
    └── tool_config.py      # Where you actually add tools
```

One example tool (`echo`) is wired up to show the registration pattern. Replace it with yours.

## Forking the template for a new server

```bash
# 1. Copy the template under a new name
cp -r servers/template servers/my-server
cd servers/my-server

# 2. Rename project identifiers in pyproject.toml
#    - name = "template-mcp-server"  ->  "my-server"
#    - [project.scripts] template = "main:main"  ->  my-server = "main:main"

# 3. Update server_name in:
#    - src/config.py  -> create_config(server_name="my-server", env_prefix="MY_SERVER")
#    - src/main.py    -> default values in the run_cli call
#    - src/tool_config.py  -> rename TEMPLATE_TOOLS to MY_SERVER_TOOLS (cosmetic)
#    - config.yaml.example -> server.name: my-server

# 4. Replace the echo example with your real tools (see "Adding tools" below)

# 5. Install via mcp-manager
mcp-manager install local my-server --source ./servers/my-server

# 6. Edit your real config
$EDITOR ~/.config/mcp-manager/servers/my-server/config.yaml

# 7. Wire it into your editor
mcp-manager config cline   # or: mcp-manager config claude
```

## Adding tools

A tool is just a function that takes JSON-serializable arguments and returns a JSON-serializable dict. Register it by adding an entry to the `TEMPLATE_TOOLS` dict in `src/tool_config.py`:

```python
def list_widgets(category: str | None = None) -> dict:
    """List widgets, optionally filtered by category."""
    # Your implementation...
    return {"widgets": [...]}


TEMPLATE_TOOLS = {
    "echo": {
        "function": echo,
        "description": "Echo a message back with the server name attached.",
    },
    "list_widgets": {                    # <-- new entry
        "function": list_widgets,
        "description": "List widgets, optionally filtered by category.",
    },
}
```

That's it. `mcp-commons` reads `TEMPLATE_TOOLS` at startup and registers each entry with FastMCP. No per-tool decorators required.

## Reading config inside a tool

`config.py` exports a `config` object loaded from your `config.yaml`. Use it inside tools:

```python
from config import config

def greet(name: str) -> dict:
    greeting = config.get("example", "greeting", default="Hello")
    return {"text": f"{greeting}, {name}!"}
```

## Transports

The template supports `stdio` (default for editor integration) and `sse` (for HTTP-based deployments) via `mcp_commons.run_cli`. Once installed, the editor invokes your server with `--transport stdio`; you don't normally run it by hand.

For local development without editor integration, you can run directly:
```bash
~/.config/mcp-manager/servers/my-server/.venv/bin/my-server stdio
~/.config/mcp-manager/servers/my-server/.venv/bin/my-server sse
~/.config/mcp-manager/servers/my-server/.venv/bin/my-server help
```

## Why your tools should log to stderr (not stdout)

When the server runs over `stdio`, **stdout is the JSON-RPC channel** — writing anything there corrupts the protocol and the host (Cline, Claude Desktop) silently truncates responses. `mcp-commons` >= 2.2.0 configures Python's `logging` module to route to `stderr` by default; using `logger.info(...)` / `logger.error(...)` is safe. Avoid bare `print()` in tool implementations unless you've redirected it.

## Connecting to a client

After `mcp-manager install local`, run:

```bash
mcp-manager config sync              # write to both Cline + Claude Desktop
# or selectively:
mcp-manager config cline
mcp-manager config claude
```

Then restart your editor.

## License

MIT.
