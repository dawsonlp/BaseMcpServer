"""Protocol and failure tests for the generated Jira workflow resources."""

import os
import sys

import anyio
import pytest
from mcp.client import Client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tools.workflow as workflow  # noqa: E402
from main import create_server  # noqa: E402


def _stub_workflow(monkeypatch, tmp_path):
    monkeypatch.setattr(workflow, "resolve_instance_name", lambda _name: "test")
    monkeypatch.setattr(workflow, "get_jira_client", lambda _name: object())
    monkeypatch.setattr(
        workflow,
        "_extract_workflow_data",
        lambda _client, _project, _issue_type: {
            "statuses": [
                {"name": "Open", "category": "To Do"},
                {"name": "Done", "category": "Done"},
            ],
            "transitions": [
                {"from_status": "Open", "to_status": "Done", "name": "Finish"},
            ],
        },
    )
    monkeypatch.setitem(workflow.WORKFLOW_RESOURCE_PATHS, "png", tmp_path / "workflow.png")
    monkeypatch.setitem(workflow.WORKFLOW_RESOURCE_PATHS, "svg", tmp_path / "workflow.svg")


def test_workflow_resource_generation_and_read(monkeypatch, tmp_path):
    _stub_workflow(monkeypatch, tmp_path)

    async def check() -> None:
        async with Client(create_server(), raise_exceptions=True) as client:
            result = await client.call_tool(
                "generate_project_workflow_graph",
                {"project_key": "TEST", "output_format": "png"},
            )
            assert result.structured_content is not None
            uri = result.structured_content["resource_uri"]
            assert "image_base64" not in result.structured_content
            resource = await client.read_resource(uri)
        assert resource.contents[0].mime_type == "image/png"
        assert resource.contents[0].blob

    anyio.run(check)


def test_missing_workflow_resource_is_an_mcp_error(monkeypatch, tmp_path):
    monkeypatch.setitem(workflow.WORKFLOW_RESOURCE_PATHS, "png", tmp_path / "missing.png")

    async def check() -> None:
        with pytest.raises(BaseExceptionGroup):
            async with Client(create_server(), raise_exceptions=True) as client:
                await client.read_resource(workflow.WORKFLOW_RESOURCE_URIS["png"])

    anyio.run(check)


def test_workflow_replacement_failure_preserves_previous_artifact(monkeypatch, tmp_path):
    _stub_workflow(monkeypatch, tmp_path)
    target = workflow.WORKFLOW_RESOURCE_PATHS["png"]
    target.write_bytes(b"previous")

    class RecordingContext:
        notifications: list[str] = []

        async def notify_resource_updated(self, uri: str) -> None:
            self.notifications.append(uri)

    context = RecordingContext()
    monkeypatch.setattr(workflow.os, "replace", lambda _source, _target: (_ for _ in ()).throw(OSError("boom")))

    async def check() -> None:
        with pytest.raises(workflow.JiraGraphError, match="boom"):
            await workflow.generate_project_workflow_graph("TEST", ctx=context)

    anyio.run(check)
    assert target.read_bytes() == b"previous"
    assert context.notifications == []


def test_workflow_notifies_after_successful_replacement(monkeypatch, tmp_path):
    _stub_workflow(monkeypatch, tmp_path)

    class RecordingContext:
        def __init__(self):
            self.notifications = []

        async def notify_resource_updated(self, uri: str) -> None:
            assert workflow.WORKFLOW_RESOURCE_PATHS["svg"].exists()
            self.notifications.append(uri)

    context = RecordingContext()

    async def check() -> None:
        result = await workflow.generate_project_workflow_graph(
            "TEST", output_format="svg", ctx=context,
        )
        assert result["resource_uri"] == workflow.WORKFLOW_RESOURCE_URIS["svg"]

    anyio.run(check)
    assert context.notifications == [workflow.WORKFLOW_RESOURCE_URIS["svg"]]
