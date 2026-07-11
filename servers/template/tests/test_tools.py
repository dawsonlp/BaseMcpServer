"""Tests for the template server's tools.

Tools are plain functions returning JSON-serialisable dicts, so you test them
by calling them directly — no MCP runtime needed. Replace these with tests for
your real tools.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tool_config import echo, get_tools_config  # noqa: E402


def test_tools_registered():
    tools = get_tools_config()
    assert "echo" in tools
    for spec in tools.values():
        assert callable(spec["function"])
        assert spec["description"]


def test_echo_returns_message():
    result = echo("hi")
    assert result["message"] == "hi"
    assert "server" in result
