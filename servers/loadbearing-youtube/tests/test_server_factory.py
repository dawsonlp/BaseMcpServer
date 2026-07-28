"""Protocol-level checks for factory-based server construction."""

import os
import sys

import anyio
from mcp.client import Client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import create_app, create_server  # noqa: E402
from tool_config import get_tools_config  # noqa: E402


def test_factory_exposes_registered_tools_over_mcp():
    async def check() -> None:
        async with Client(create_server()) as client:
            result = await client.list_tools()
        assert {tool.name for tool in result.tools} == set(get_tools_config())

    anyio.run(check)


def test_app_factory_builds_streamable_http_app():
    app = create_app()
    assert app is not None
