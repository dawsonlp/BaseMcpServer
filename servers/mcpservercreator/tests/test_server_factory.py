"""Factory and generator checks for MCP Server Creator."""

from importlib.metadata import version

import anyio
import pytest
from mcp.client import Client

from main import create_app, create_server
from server import create_server_files, validate_code_snippet
from tool_config import get_tools_config


def test_factory_exposes_registered_tools_over_mcp():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=True) as client:
            result = await client.list_tools()
            help_result = await client.call_tool("help")
            assert client.server_info.version == version("mcpservercreator")
        assert {tool.name for tool in result.tools} == set(get_tools_config())
        assert all(tool.title and tool.description and tool.annotations for tool in result.tools)
        assert all(tool.output_schema is not None for tool in result.tools)
        assert all("kwargs" not in tool.input_schema.get("properties", {}) for tool in result.tools)
        create_tool = next(tool for tool in result.tools if tool.name == "create_mcp_server")
        assert create_tool.annotations.destructive_hint is True
        assert help_result.structured_content is not None
        assert set(help_result.structured_content) == {
            "description", "security_warning", "usage", "security_features", "limitations",
        }

    anyio.run(check)


def test_app_factory_builds_streamable_http_app():
    assert create_app() is not None


def test_generator_accepts_plain_functions_and_emits_factory(tmp_path):
    snippet = '''
def add_numbers(a: int, b: int) -> dict[str, int]:
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
    tool_config_source = (server_dir / "src" / "tool_config.py").read_text()
    pyproject = (server_dir / "pyproject.toml").read_text()
    config_example = (server_dir / "config.yaml.example").read_text()
    assert "def create_server() -> MCPServer:" in main_source
    assert ".add_tool(" in main_source
    assert "@" not in main_source
    assert "version=PACKAGE_VERSION" in main_source
    assert "structured_output=True" in main_source
    assert "TransportSecuritySettings" in main_source
    assert "ToolAnnotations" in tool_config_source
    assert "readOnlyHint=None" in tool_config_source
    assert 'host: "127.0.0.1"' in config_example
    assert "allowed_hosts" in config_example
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


@pytest.mark.parametrize(
    ("snippet", "message"),
    [
        ("def bad(value: str, **kwargs) -> dict[str, str]:\n    return {}\n", "explicit typed mapping"),
        ("def bad(value) -> dict[str, str]:\n    return {}\n", "untyped parameters"),
        ("def bad(value: str) -> dict:\n    return {}\n", "uses bare dict"),
    ],
)
def test_generator_rejects_false_schemas(snippet, message):
    with pytest.raises(ValueError, match=message):
        validate_code_snippet(snippet)
