"""Workflow responsiveness, publication and actual MCP subscription delivery."""

from threading import Event
from types import SimpleNamespace

import anyio
import pytest
from mcp import MCPError
from mcp.client import Client
from mcp.client.subscriptions import ResourceUpdated

from config import settings
from jira_client import ClientRegistry
from main import create_server
from tools import workflow


@pytest.fixture
def server(monkeypatch, tmp_path):
    monkeypatch.setattr(
        workflow,
        "_extract_workflow_data",
        lambda *_: {
            "statuses": [
                {"name": "Open", "category": "To Do"},
                {"name": "Done", "category": "Done"},
            ],
            "transitions": [
                {"from_status": "Open", "to_status": "Done", "name": "Finish"}
            ],
        },
    )
    for fmt in ("png", "svg"):
        monkeypatch.setitem(
            workflow.WORKFLOW_RESOURCE_PATHS, fmt, tmp_path / f"workflow.{fmt}"
        )
    return create_server(
        client_registry_factory=lambda: ClientRegistry(
            settings, lambda *_: SimpleNamespace(close=lambda: None)
        )
    )


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_workflow_generation_and_read(server, mode):
    async def check():
        async with Client(server, mode=mode) as client:
            result = await client.call_tool(
                "generate_project_workflow_graph", {"project_key": "TEST"}
            )
            assert not result.is_error
            uri = result.structured_content["resource_uri"]
            assert "image_base64" not in result.structured_content
            resource = await client.read_resource(uri)
            assert resource.contents[0].mime_type == "image/png"
            assert resource.contents[0].blob

    anyio.run(check)


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_missing_workflow_resource_has_precise_error(server, mode):
    async def check():
        async with Client(server, mode=mode) as client:
            for uri in (
                workflow.WORKFLOW_RESOURCE_URIS["png"],
                "jira-workflow://unknown",
            ):
                with pytest.raises(MCPError) as caught:
                    await client.read_resource(uri)
                assert caught.value.code == -32602
                assert caught.value.data == {"uri": uri}

    anyio.run(check)


def test_subscription_receives_success_and_no_failed_publication(server, monkeypatch):
    uri = workflow.WORKFLOW_RESOURCE_URIS["svg"]
    path = workflow.WORKFLOW_RESOURCE_PATHS["svg"]
    path.write_text("previous")
    replace = workflow.os.replace

    def fail(*_):
        raise OSError("controlled failure")

    async def check():
        async with Client(server) as client:
            async with client.listen(resource_subscriptions=[uri]) as subscription:
                assert uri in subscription.honored.resource_subscriptions
                monkeypatch.setattr(workflow.os, "replace", fail)
                result = await client.call_tool(
                    "generate_project_workflow_graph",
                    {"project_key": "TEST", "output_format": "svg"},
                )
                assert result.is_error
                assert path.read_text() == "previous"
                with anyio.move_on_after(0.1) as timeout:
                    await anext(subscription)
                assert timeout.cancel_called
                monkeypatch.setattr(workflow.os, "replace", replace)
                result = await client.call_tool(
                    "generate_project_workflow_graph",
                    {"project_key": "TEST", "output_format": "svg"},
                )
                assert not result.is_error
                with anyio.fail_after(3):
                    event = await anext(subscription)
                assert isinstance(event, ResourceUpdated) and event.uri == uri
                resource = await client.read_resource(uri)
                assert "<svg" in resource.contents[0].text

    anyio.run(check)


def test_blocked_workflow_allows_unrelated_mcp_call(server, monkeypatch):
    entered, release = Event(), Event()

    def blocking(*_):
        entered.set()
        assert release.wait(5)
        return {"statuses": [], "transitions": []}

    monkeypatch.setattr(workflow, "_extract_workflow_data", blocking)

    async def check():
        async with Client(server) as client:

            async def generate():
                result = await client.call_tool(
                    "generate_project_workflow_graph",
                    {"project_key": "TEST", "output_format": "json"},
                )
                assert not result.is_error

            async with anyio.create_task_group() as group:
                group.start_soon(generate)
                try:
                    with anyio.fail_after(2):
                        while not entered.is_set():
                            await anyio.sleep(0.01)
                        result = await client.call_tool(
                            "validate_jql_query", {"jql": "project = TEST"}
                        )
                        assert not result.is_error
                finally:
                    release.set()

    anyio.run(check)


def test_render_failure_closes_figure(server, monkeypatch):
    import matplotlib.pyplot as plt
    import networkx as nx

    before = plt.get_fignums()
    monkeypatch.setattr(
        nx,
        "spring_layout",
        lambda *a, **kw: (_ for _ in ()).throw(ValueError("layout failed")),
    )

    async def check():
        async with Client(server) as client:
            result = await client.call_tool(
                "generate_project_workflow_graph", {"project_key": "TEST"}
            )
            assert result.is_error

    anyio.run(check)
    assert plt.get_fignums() == before


def test_rendering_is_serialized_across_server_instances(server, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock
    import networkx as nx

    # Finish font-cache initialization before timing synchronization waits.
    import matplotlib.pyplot as plt

    assert not plt.get_fignums()
    original = nx.spring_layout
    entered, release = Event(), Event()
    guard = Lock()
    active = peak = calls = 0

    def layout(*args, **kwargs):
        nonlocal active, peak, calls
        with guard:
            active += 1
            calls += 1
            peak = max(peak, active)
            first = calls == 1
        try:
            if first:
                entered.set()
                assert release.wait(5)
            return original(*args, **kwargs)
        finally:
            with guard:
                active -= 1

    monkeypatch.setattr(nx, "spring_layout", layout)

    def generate(name):
        return workflow.generate_project_workflow_graph(
            "TEST", instance_name=name, output_format="svg", get_client=lambda: object()
        )

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(generate, "one")
        assert entered.wait(3)
        second = pool.submit(generate, "two")
        release.set()
        assert first.result(5)["resource_uri"] == second.result(5)["resource_uri"]
    assert calls == 2 and peak == 1
