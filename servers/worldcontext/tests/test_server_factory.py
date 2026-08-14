"""Protocol-level checks for factory-based server construction."""

from importlib.metadata import version

import anyio
from mcp.client import Client

from main import create_app, create_server
from tool_config import get_tools_config


def test_factory_exposes_registered_tools_over_mcp():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=True) as client:
            result = await client.list_tools()
            assert client.server_info.version == version("worldcontext-mcp-server")
        assert {tool.name for tool in result.tools} == set(get_tools_config())
        assert all(tool.title and tool.description and tool.annotations for tool in result.tools)
        assert all(tool.output_schema is not None for tool in result.tools)
        assert all("kwargs" not in tool.input_schema.get("properties", {}) for tool in result.tools)
        news = next(tool for tool in result.tools if tool.name == "get_news_headlines")
        assert news.input_schema["properties"]["count"]["minimum"] == 1
        assert news.input_schema["properties"]["count"]["maximum"] == 20
        current = next(tool for tool in result.tools if tool.name == "get_current_datetime")
        assert current.output_schema["required"] == [
            "current_datetime", "current_date", "current_time", "day_of_week", "month",
            "year", "week_number", "timezone", "utc_datetime", "unix_timestamp",
            "formatted_display",
        ]

    anyio.run(check)


def test_app_factory_builds_streamable_http_app():
    app = create_app()
    assert app is not None


def test_tool_exception_is_reported_as_mcp_error():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=False) as client:
            result = await client.call_tool("get_python_package_version", {"package_name": ""})
        assert result.is_error is True
        assert result.structured_content is None

    anyio.run(check)
