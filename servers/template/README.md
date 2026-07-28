# MCP Server Template

Starter package for a direct MCP Python SDK v2 server. It uses plain tool
functions, a `create_server()` factory, and imperative `MCPServer.add_tool()`
registration. It does not use decorators or MCP Commons.

## Structure

```text
servers/template/
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

## Create a server

```bash
cp -r servers/template servers/my-server
cd servers/my-server
```

Then update:

- project and console-script names in `pyproject.toml`;
- server name and environment prefix in `src/config.py`;
- defaults and description in `src/main.py`;
- `config.yaml.example`;
- the tool functions and registry in `src/tool_config.py`.

## Add a tool

```python
def list_widgets(category: str | None = None) -> dict:
    """List widgets, optionally filtered by category."""
    return {"widgets": []}


TEMPLATE_TOOLS = {
    "list_widgets": {
        "function": list_widgets,
        "description": "List widgets, optionally filtered by category.",
    },
}
```

`create_server()` registers this map with `add_tool()`. Do not add an MCP
decorator to the function.

## Run and test

```bash
uv lock
uv run --locked --extra dev pytest
uv run --locked template stdio
uv run --locked template streamable-http
uv run --locked template sse  # legacy only
```

For stdio servers, stdout is the JSON-RPC channel. Send logs to stderr and do
not use bare `print()` inside tool implementations.

## Install

```bash
mcp-manager install my-server --source ./servers/my-server
mcp-manager sync
```

See [`docs/developer/BUILD_A_NEW_MCP.md`](../../docs/developer/BUILD_A_NEW_MCP.md)
for the full pattern.
