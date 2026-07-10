"""Tests for the loadbearing_youtube MCP server tool layer.

These cover the adapter's contract (registration, input validation, provider
discovery passthrough) without hitting the network or an LLM. The analysis
logic itself is tested in the loadbearing_youtube package.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tool_config import (  # noqa: E402
    analyze_video,
    get_tools_config,
    get_video_transcript,
    list_analysis_providers,
)


def test_tools_registered():
    tools = get_tools_config()
    assert set(tools) == {"analyze_video", "get_video_transcript", "list_analysis_providers"}
    for name, spec in tools.items():
        assert callable(spec["function"])
        assert spec["description"]


def test_analyze_video_rejects_empty_url():
    result = analyze_video("")
    assert result["success"] is False
    assert "error" in result


def test_get_video_transcript_rejects_empty_url():
    result = get_video_transcript("")
    assert result["success"] is False
    assert "error" in result


def test_list_providers_reports_builtins():
    result = list_analysis_providers()
    assert result["success"] is True
    names = {p["name"] for p in result["providers"]}
    assert {"ollama", "openai", "anthropic"} <= names
