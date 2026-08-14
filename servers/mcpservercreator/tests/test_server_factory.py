"""Factory and generator checks for MCP Server Creator."""

import anyio
import pytest
from mcp.client import Client

from main import create_app, create_server
from server import create_server_files, validate_code_snippet
from tool_config import get_tools_config


def test_factory_exposes_registered_tools_over_mcp():
    async def check() -> None:
        async with Client(create_server()) as client:
            result = await client.list_tools()
        assert {tool.name for tool in result.tools} == set(get_tools_config())

    anyio.run(check)


def test_app_factory_builds_streamable_http_app():
    assert create_app() is not None


def test_generator_accepts_plain_functions_and_emits_factory(tmp_path):
    snippet = '''
def add_numbers(a: int, b: int) -> dict:
    """Add two numbers."""
    return {"result": a + b}
'''
    assert validate_code_snippet(snippet) == ["add_numbers"]

    server_dir = tmp_path / "generated-server"
    create_server_files(
        server_dir=server_dir,
        server_name="generated-server",
        code_snippet=snippet,
        description="Generated test server",
        author="Test",
        tool_names=["add_numbers"],
    )

    main_source = (server_dir / "src" / "main.py").read_text()
    pyproject = (server_dir / "pyproject.toml").read_text()
    assert "def create_server() -> MCPServer:" in main_source
    assert ".add_tool(" in main_source
    assert "@" not in main_source
    assert '"mcp>=2.0.0,<3.0.0"' in pyproject
    assert "prerelease" not in pyproject
    assert "mcp-commons" not in pyproject
    assert 'py-modules = ["main", "config", "server", "tool_config"]' in pyproject
    assert (server_dir / "README.md").exists()
    for python_file in (server_dir / "src").glob("*.py"):
        compile(python_file.read_text(), str(python_file), "exec")


def test_generator_rejects_decorators():
    snippet = '''
@mcp.tool()
def decorated_tool() -> dict:
    return {"ok": True}
'''
    with pytest.raises(ValueError, match="Decorators are not accepted"):
        validate_code_snippet(snippet)
