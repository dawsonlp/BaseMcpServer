"""Tests for the loadbearing_youtube MCP server tool layer.

These cover the adapter's contract (registration, input validation, provider
discovery passthrough) without hitting the network or an LLM. The analysis
logic itself is tested in the loadbearing_youtube package.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tool_config  # noqa: E402
from tool_config import (  # noqa: E402
    analyze_video,
    get_analysis_result,
    get_tools_config,
    get_video_transcript,
    list_analysis_jobs,
    list_analysis_providers,
)


def test_tools_registered():
    tools = get_tools_config()
    assert set(tools) == {
        "analyze_video",
        "get_analysis_result",
        "list_analysis_jobs",
        "get_video_transcript",
        "list_analysis_providers",
    }
    for name, spec in tools.items():
        assert callable(spec["function"])
        assert spec["description"]


def test_analyze_video_rejects_empty_url():
    result = analyze_video("")
    assert result["success"] is False
    assert "error" in result


def test_get_analysis_result_unknown_job():
    result = get_analysis_result("nope")
    assert result["success"] is False
    assert "unknown job_id" in result["error"]


def test_async_job_lifecycle(monkeypatch):
    """analyze_video should hand back a job_id while running, and
    get_analysis_result should return the finished report once done —
    without any network/LLM (analyze is stubbed)."""
    import threading

    release = threading.Event()

    class _FakeReport:
        def to_dict(self):
            return {"video_id": "vid", "analysis": {"thesis": "T", "components": []}}

    def _fake_analyze(url, provider=None, model=None, languages=None):
        release.wait(5)  # simulate a slow analysis until the test releases it
        return _FakeReport()

    monkeypatch.setattr(tool_config, "analyze", _fake_analyze)
    monkeypatch.setattr(tool_config, "render_markdown", lambda report: "# md")
    monkeypatch.setattr(tool_config, "_INLINE_WAIT_S", 0)  # force the "running" path

    started = analyze_video("https://youtu.be/abc")
    assert started["status"] == "running"
    job_id = started["job_id"]

    release.set()
    done = get_analysis_result(job_id, wait_seconds=5)
    assert done["status"] == "done"
    assert done["success"] is True
    assert done["video_id"] == "vid"
    assert done["markdown"] == "# md"

    listed = list_analysis_jobs()
    assert any(j["job_id"] == job_id for j in listed["jobs"])


def test_get_video_transcript_rejects_empty_url():
    result = get_video_transcript("")
    assert result["success"] is False
    assert "error" in result


def test_list_providers_reports_builtins():
    result = list_analysis_providers()
    assert result["success"] is True
    names = {p["name"] for p in result["providers"]}
    assert {"ollama", "openai", "anthropic"} <= names
