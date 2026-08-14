"""Protocol-level checks for factory-based server construction."""

import os
import sys
from importlib.metadata import version

import anyio
import pytest
from mcp.client import Client
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import _transport_security, create_app, create_server  # noqa: E402
from config import config  # noqa: E402
from tool_config import get_tools_config  # noqa: E402


def test_factory_exposes_registered_tools_over_mcp():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=True) as client:
            result = await client.list_tools()
            response = await client.call_tool("echo", {"message": "hello"})
            assert client.server_info.version == version("template-mcp-server")
        assert {tool.name for tool in result.tools} == set(get_tools_config())
        tool = result.tools[0]
        assert tool.title == "Echo"
        assert tool.annotations.read_only_hint is True
        assert tool.output_schema is not None
        assert "kwargs" not in tool.input_schema.get("properties", {})
        assert tool.output_schema["required"] == ["server", "message"]
        assert response.structured_content == {"server": "template", "message": "hello"}

    anyio.run(check)


def test_app_factory_builds_streamable_http_app():
    app = create_app()
    assert app is not None


def test_streamable_http_rejects_untrusted_host_and_origin():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }
    base_headers = {"accept": "application/json, text/event-stream"}
    with TestClient(create_app()) as client:
        accepted = client.post(
            "/mcp",
            headers={**base_headers, "host": "localhost:8000", "origin": "http://localhost:3000"},
            json=payload,
        )
        rejected_host = client.post(
            "/mcp",
            headers={**base_headers, "host": "evil.test", "origin": "http://localhost:3000"},
            json=payload,
        )
        rejected_origin = client.post(
            "/mcp",
            headers={**base_headers, "host": "localhost:8000", "origin": "https://evil.test"},
            json=payload,
        )
    assert accepted.status_code == 200
    assert rejected_host.status_code == 421
    assert rejected_origin.status_code == 403


def test_non_loopback_policy_must_be_explicit(monkeypatch):
    monkeypatch.setattr(config, "get", lambda _section, _key, default=None: default)
    with pytest.raises(ValueError, match="allowed_hosts"):
        _transport_security("0.0.0.0")

    values = {
        "allowed_hosts": ["mcp.example.test"],
        "allowed_origins": ["https://client.example.test"],
    }
    monkeypatch.setattr(
        config, "get", lambda _section, key, default=None: values.get(key, default),
    )
    policy = _transport_security("0.0.0.0")
    assert policy is not None
    assert policy.allowed_hosts == ["mcp.example.test"]
    assert policy.allowed_origins == ["https://client.example.test"]
