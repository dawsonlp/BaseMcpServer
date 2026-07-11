# Building a New MCP Server

Every server in this repo uses **one** pattern: a thin package built on
[`mcp-commons`](https://pypi.org/project/mcp-commons/) that declares its tools in
a single `tool_config.py` and is installed + synced by `mcp-manager`. To make a
new server, fork [`servers/template/`](../../servers/template/) and fill in your
tools. That's it — there is no second architecture to choose.

## Anatomy

```
servers/<name>/
├── pyproject.toml          # package + [project.scripts] entry point
├── config.yaml.example     # copied to the managed config on install
├── src/
│   ├── config.py           # create_config(server_name=..., env_prefix=...)
│   ├── main.py             # run_cli(...) / create_mcp_app(...)  (boilerplate)
│   └── tool_config.py      # your tools + get_tools_config()
└── tests/
    └── test_tools.py       # call your tool functions directly
```

`config.py` and `main.py` are boilerplate — copy them from the template
unchanged except the server name/port. All your work is in `tool_config.py`.

## 1. Fork the template

```bash
cp -r servers/template servers/my-server
```

Edit `pyproject.toml`: set `name`, the `[project.scripts]` entry, and
`[tool.setuptools] py-modules`/`package-dir`. Add any runtime dependencies.

```toml
[project]
name = "my-server-mcp-server"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["mcp>=1.27.0", "mcp-commons>=2.2.2", "PyYAML>=6.0.3"]

[project.scripts]
my-server = "main:main"

[tool.setuptools]
py-modules = ["main", "config", "tool_config"]
[tool.setuptools.packages.find]
where = ["src"]
[tool.setuptools.package-dir]
"" = "src"
```

> If your server name collides with a Python package it depends on, give the
> console script a distinct suffix (e.g. `my-server-mcp`) so the two don't
> shadow each other on `PATH`.

## 2. config.py (unchanged from the template)

```python
from mcp_commons import create_config, load_dotenv_file

load_dotenv_file()

# mcp-commons resolves ~/.config/mcp-manager/servers/<name>/config.yaml first,
# then ~/.config/<name>/config.yaml, then ./config.yaml.
config = create_config(server_name="my-server", env_prefix="MY_SERVER")
```

## 3. main.py (unchanged from the template)

```python
from mcp_commons import create_mcp_app, run_cli
from config import config
from tool_config import get_tools_config


def main() -> None:
    run_cli(
        server_name=config.get("server", "name", default="my-server"),
        tools_config=get_tools_config(),
        description="- What this server does",
        host=config.get("server", "host", default="localhost"),
        port=config.get("server", "port", default=7500),
    )


def create_app():
    return create_mcp_app(
        server_name=config.get("server", "name", default="my-server"),
        tools_config=get_tools_config(),
    )


if __name__ == "__main__":
    main()
```

## 4. tool_config.py (your actual work)

Each tool is a plain function that returns a JSON-serialisable dict. Register
them in one map; `mcp-commons` handles the MCP protocol.

```python
from typing import Any, Dict


def say_hello(name: str, style: str = "casual") -> Dict[str, Any]:
    """Greet someone. Args: name; style (formal|casual)."""
    if not name:
        return {"success": False, "error": "name is required"}
    text = f"Hello, {name}." if style == "formal" else f"Hey {name}!"
    return {"success": True, "greeting": text}


MY_SERVER_TOOLS: Dict[str, Dict[str, Any]] = {
    "say_hello": {
        "function": say_hello,
        "description": "Generate a greeting for someone.",
    },
}


def get_tools_config() -> Dict[str, Dict[str, Any]]:
    return MY_SERVER_TOOLS
```

Conventions that keep tools predictable:
- Return dicts, not raw strings; include a `success` boolean and an `error`
  string on failure rather than raising.
- Validate inputs and fail with a clear message.
- Write a one-line docstring describing each argument — it becomes the tool's
  schema description.
- For long-running work, return a job id and add a `get_*_result` tool to poll,
  so a single call stays under the client's request timeout (see
  `servers/loadbearing-youtube`).

## 5. Configuration and secrets

`config.yaml.example` is copied to
`~/.config/mcp-manager/servers/<name>/config.yaml` on install. Put defaults and
API keys there (read at runtime by the server); keys are **not** pushed into
editor configs. Read values with `config.get("section", "key", default=...)`;
`MY_SERVER_SECTION_KEY` environment variables override the file.

## 6. Tests

```python
from tool_config import say_hello

def test_say_hello():
    assert say_hello("Ada")["success"] is True
    assert say_hello("")["success"] is False
```

Run with `uv run pytest`.

## 7. Install and connect

```bash
mcp-manager install my-server --source ./servers/my-server
mcp-manager sync          # write into every detected AI client
```

Restart your editor to pick up the new server. See the top-level
[README](../../README.md) for the full install flow.

## Generating a server from a snippet

`servers/mcpservercreator` scaffolds a new server from a code snippet once
installed — useful for one-off tools.
