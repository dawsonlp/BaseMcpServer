"""Protocol-level checks for factory-based server construction."""

import os
import sys
from importlib.metadata import version

import anyio
from mcp.client import Client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import create_app, create_server  # noqa: E402
import tool_config  # noqa: E402
from tool_config import get_tools_config  # noqa: E402


def test_factory_exposes_registered_tools_over_mcp():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=True) as client:
            result = await client.list_tools()
            assert client.server_info.version == version("loadbearing-youtube-mcp-server")
        assert {tool.name for tool in result.tools} == set(get_tools_config())
        assert all(tool.title and tool.description and tool.annotations for tool in result.tools)
        assert all(tool.output_schema is not None for tool in result.tools)
        assert all("kwargs" not in tool.input_schema.get("properties", {}) for tool in result.tools)
        analyze = next(tool for tool in result.tools if tool.name == "analyze_video")
        assert analyze.annotations.read_only_hint is False
        poll = next(tool for tool in result.tools if tool.name == "get_analysis_result")
        assert poll.input_schema["properties"]["wait_seconds"]["minimum"] == 0
        assert poll.input_schema["properties"]["wait_seconds"]["maximum"] == 45

    anyio.run(check)


def test_app_factory_builds_streamable_http_app():
    app = create_app()
    assert app is not None


def test_executor_is_owned_by_one_server_lifespan(monkeypatch):
    executors = []

    class FakeExecutor:
        def __init__(self, **_kwargs):
            self.shutdown_calls = []
            executors.append(self)

        def shutdown(self, **kwargs):
            self.shutdown_calls.append(kwargs)

    monkeypatch.setattr(tool_config, "ThreadPoolExecutor", FakeExecutor)

    async def check() -> None:
        async with Client(create_server(), raise_exceptions=True):
            assert len(executors) == 1
            assert executors[0].shutdown_calls == []

    anyio.run(check)
    assert executors[0].shutdown_calls == [{"wait": True, "cancel_futures": True}]


def test_tool_exception_is_reported_as_mcp_error():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=False) as client:
            result = await client.call_tool("get_video_transcript", {"url": ""})
        assert result.is_error is True
        assert result.structured_content is None

    anyio.run(check)
