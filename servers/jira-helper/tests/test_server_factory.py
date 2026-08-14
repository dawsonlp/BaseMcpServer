"""Protocol-level checks for factory-based server construction."""

from importlib.metadata import version

import anyio
from mcp.client import Client

from config import settings
from main import _transport_security, create_app, create_server
from tool_config import get_resources, get_tools_config


def test_factory_exposes_registered_tools_over_mcp():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=True) as client:
            result = await client.list_tools()
            resources = await client.list_resources()
            assert client.server_info.version == version("jira-helper")
        assert {tool.name for tool in result.tools} == set(get_tools_config())
        assert {str(resource.uri) for resource in resources.resources} == {
            str(resource.uri) for resource in get_resources()
        }
        assert all(tool.title and tool.description and tool.annotations for tool in result.tools)
        assert all("kwargs" not in tool.input_schema.get("properties", {}) for tool in result.tools)
        assert all(tool.output_schema is not None for tool in result.tools)

        create_schema = next(
            tool.input_schema for tool in result.tools if tool.name == "create_jira_ticket"
        )
        assert create_schema["required"] == ["project_key", "summary"]
        assert create_schema["properties"]["labels"]["anyOf"][0]["items"] == {"type": "string"}
        assert create_schema["properties"]["custom_fields"]["anyOf"][0]["additionalProperties"] is True

        search_schema = next(
            tool.input_schema for tool in result.tools if tool.name == "search_jira_issues"
        )
        assert search_schema["properties"]["max_results"]["minimum"] == 1
        assert search_schema["properties"]["max_results"]["maximum"] == 1000

        workflow_schema = next(
            tool.input_schema for tool in result.tools
            if tool.name == "generate_project_workflow_graph"
        )
        assert workflow_schema["properties"]["output_format"]["enum"] == ["png", "svg", "json"]

    anyio.run(check)


def test_app_factory_builds_streamable_http_app(monkeypatch):
    monkeypatch.setattr(settings, "host", "127.0.0.1")
    app = create_app()
    assert app is not None


def test_non_loopback_transport_requires_explicit_policy(monkeypatch):
    monkeypatch.setattr(settings, "allowed_hosts", [])
    monkeypatch.setattr(settings, "allowed_origins", [])
    try:
        _transport_security("0.0.0.0")
    except ValueError as error:
        assert "allowed_hosts" in str(error)
    else:
        raise AssertionError("non-loopback transport must fail closed")

    monkeypatch.setattr(settings, "allowed_hosts", ["mcp.example.test"])
    monkeypatch.setattr(settings, "allowed_origins", ["https://client.example.test"])
    policy = _transport_security("0.0.0.0")
    assert policy is not None
    assert policy.allowed_hosts == ["mcp.example.test"]
    assert policy.allowed_origins == ["https://client.example.test"]


def test_tool_results_and_validation_errors_use_mcp_contracts():
    async def check() -> None:
        async with Client(create_server(), raise_exceptions=False) as client:
            success = await client.call_tool("validate_jql_query", {"jql": "project = TEST"})
            invalid = await client.call_tool("validate_jql_query", {})
            # The SDK's argument models intentionally ignore additional
            # properties; arbitrary Jira fields still have an explicit
            # custom_fields channel.
            with_extra = await client.call_tool(
                "validate_jql_query", {"jql": "project = TEST", "unused": True},
            )
        assert success.is_error is False
        assert success.structured_content == {
            "valid": True, "jql": "project = TEST", "issues": [],
        }
        assert invalid.is_error is True

        assert with_extra.is_error is False

    anyio.run(check)
