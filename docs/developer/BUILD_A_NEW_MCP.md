# Building a New MCP Server

Every server in this repository uses one direct MCP Python SDK v2 pattern:

1. Tool implementations are plain Python functions.
2. `tool_config.py` maps public tool names to those functions.
3. `create_server()` constructs `MCPServer` and calls `add_tool()`.
4. No MCP decorators and no MCP Commons dependency are used.

Fork [`servers/template/`](../../servers/template/) rather than creating a
second architecture.

## Package layout

```text
servers/<name>/
├── pyproject.toml
├── uv.lock
├── config.yaml.example
├── src/
│   ├── config.py
│   ├── main.py
│   └── tool_config.py
└── tests/
    ├── test_tools.py
    └── test_server_factory.py
```

## Dependency boundary

Allow upgrades within the stable SDK v2 line, with an explicit upper bound so
a future breaking major release is not selected automatically.

```toml
[project]
dependencies = ["mcp>=2.0.0,<3.0.0", "PyYAML>=6.0.3"]
```

Run `uv lock` after changing dependencies and commit the lockfile for these
deployable server applications.

## Tool implementations

Keep business behavior independent of the MCP runtime:

```python
def say_hello(name: str, style: str = "casual") -> dict:
    """Generate a greeting for one person."""
    if not name:
        return {"success": False, "error": "name is required"}
    text = f"Hello, {name}." if style == "formal" else f"Hey {name}!"
    return {"success": True, "greeting": text}


MY_SERVER_TOOLS = {
    "say_hello": {
        "function": say_hello,
        "description": "Generate a greeting for someone.",
    },
}


def get_tools_config() -> dict:
    return MY_SERVER_TOOLS
```

Do not decorate the function. Its signature and type annotations remain the
source for the SDK-generated input schema.

## Server factory

`main.py` owns construction and transport wiring:

```python
from mcp.server import MCPServer

from config import config
from tool_config import get_tools_config


def create_server() -> MCPServer:
    server = MCPServer(
        name=str(config.get("server", "name", default="my-server")),
        description="What this server does",
    )
    for name, spec in get_tools_config().items():
        function = spec["function"]
        if not callable(function):
            raise TypeError(f"Tool {name!r} is not callable")
        server.add_tool(
            function,
            name=name,
            description=spec.get("description") or f"Tool: {name}",
        )
    return server


def create_app():
    return create_server().streamable_http_app(host="127.0.0.1")
```

The template also provides CLI parsing and calls `MCPServer.run()` directly.
Supported transports are:

- `stdio` for local MCP clients;
- `streamable-http` for new network deployments;
- `sse` only for legacy clients.

## Configuration

The template's package-local reader checks, in order:

1. `~/.config/mcp-manager/servers/<name>/config.yaml`
2. `~/.config/<name>/config.yaml`
3. `./config.yaml`

`<PREFIX>_<SECTION>_<KEY>` environment variables override YAML values.

## Tests

Test business functions directly, then test registration through the official
in-memory client:

```python
import anyio
from mcp.client import Client

from main import create_server


def test_server_exposes_tools():
    async def check():
        async with Client(create_server()) as client:
            result = await client.list_tools()
        assert {tool.name for tool in result.tools} == {"say_hello"}

    anyio.run(check)
```

Run `uv run --locked --extra dev pytest`.

## Install and connect

```bash
mcp-manager install my-server --source ./servers/my-server
mcp-manager sync
```

Restart the client after synchronization.
