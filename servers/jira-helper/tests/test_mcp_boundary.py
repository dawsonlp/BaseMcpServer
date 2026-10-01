"""Public error, lifecycle, and schema contracts in both protocol eras."""

import anyio
import pytest
import requests
from mcp.client import Client

from config import settings
from exceptions import JiraAuthenticationError, JiraPermissionError, JiraConnectionError
from jira_client import ClientRegistry
from main import create_server
from tools import issues


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_errors_are_actionable_and_unexpected_errors_are_sanitized(mode, monkeypatch):
    calls = []

    def factory(*_):
        calls.append(True)
        raise AssertionError("client should not be acquired for invalid input")

    async def check():
        server = create_server(
            client_registry_factory=lambda: ClientRegistry(settings, factory)
        )
        async with Client(server, mode=mode) as client:
            result = await client.call_tool("get_issue_details", {"issue_key": "bad"})
            assert result.is_error
            assert "Expected format: PROJECT-123" in result.content[0].text
            assert calls == []
            for error, text in [
                (JiraAuthenticationError("SECRET"), "authentication"),
                (JiraPermissionError("SECRET"), "permissions"),
                (JiraConnectionError("SECRET"), "connectivity"),
                (RuntimeError("SECRET"), "Error executing tool"),
            ]:

                def fail(**_):
                    raise error

                monkeypatch.setattr(issues, "list_jira_projects", fail)
                result = await client.call_tool("list_jira_projects", {})
                assert result.is_error
                assert text in result.content[0].text
                assert "SECRET" not in result.content[0].text

    anyio.run(check)


def test_unknown_instance_and_wrapped_permission_error():
    class Forbidden:
        def projects(self):
            response = requests.Response()
            response.status_code = 403
            raise requests.HTTPError("SECRET upstream body", response=response)

        def close(self):
            pass

    async def check():
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "list_jira_projects", {"instance_name": "__not_configured__"}
            )
            assert result.is_error
            assert "not found in configuration" in result.content[0].text
        server = create_server(
            client_registry_factory=lambda: ClientRegistry(
                settings, lambda *_: Forbidden()
            )
        )
        async with Client(server) as client:
            result = await client.call_tool("list_jira_projects", {})
            assert result.is_error
            assert "permissions" in result.content[0].text
            assert "SECRET" not in result.content[0].text

    anyio.run(check)


def test_factory_instances_own_separate_lazy_clients():
    created = []
    registries = []

    class Fake:
        closed = 0

        def projects(self):
            return [
                {"key": "TEST", "name": "Test", "id": "1", "projectTypeKey": "software"}
            ]

        def close(self):
            self.closed += 1

    def factory(*_):
        client = Fake()
        created.append(client)
        return client

    def registry():
        r = ClientRegistry(settings, factory)
        registries.append(r)
        return r

    async def check():
        one, two = (
            create_server(client_registry_factory=registry),
            create_server(client_registry_factory=registry),
        )
        assert not created and not registries
        async with Client(one) as a, Client(two) as b:
            assert not created
            for c in (a, b):
                result = await c.call_tool("list_jira_projects", {})
                assert result.structured_content["projects"][0]["key"] == "TEST"
            assert len(created) == 2 and created[0] is not created[1]
        assert all(c.closed == 1 for c in created)

    anyio.run(check)


def test_partial_creation_is_not_converted_to_failure():
    class Fake:
        creations = 0

        def issue_create(self, **_):
            self.creations += 1
            return {"key": "TEST-1"}

        def create_issue_link(self, _):
            raise RuntimeError("SECRET")

        def close(self):
            pass

    fake = Fake()

    async def check():
        server = create_server(
            client_registry_factory=lambda: ClientRegistry(settings, lambda *_: fake)
        )
        async with Client(server) as c:
            result = await c.call_tool(
                "create_issue_with_links",
                {
                    "project_key": "TEST",
                    "summary": "test",
                    "links": [{"issue_key": "TEST-2"}],
                },
            )
            assert not result.is_error
            assert result.structured_content["key"] == "TEST-1"
            assert result.structured_content["link_errors"]
            assert "SECRET" not in str(result.structured_content)
            assert fake.creations == 1

    anyio.run(check)


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_cancellation_does_not_close_client_under_running_work(mode):
    from threading import Event

    entered, release, finished = Event(), Event(), Event()
    scopes = []

    class Fake:
        closed = False

        def projects(self):
            entered.set()
            assert release.wait(5)
            assert not self.closed
            finished.set()
            return []

        def close(self):
            assert finished.is_set()
            self.closed = True

    fake = Fake()

    async def check():
        server = create_server(
            client_registry_factory=lambda: ClientRegistry(settings, lambda *_: fake)
        )
        async with Client(server, mode=mode) as client:

            async def call():
                with anyio.CancelScope() as scope:
                    scopes.append(scope)
                    await client.call_tool("list_jira_projects", {})

            async with anyio.create_task_group() as group:
                group.start_soon(call)
                try:
                    with anyio.fail_after(2):
                        while not entered.is_set():
                            await anyio.sleep(0.01)
                    scopes[0].cancel()
                    await anyio.sleep(0)
                    assert not fake.closed
                finally:
                    release.set()
        assert fake.closed and finished.is_set()

    anyio.run(check)


def test_nested_schema_and_raw_upstream_payload():
    class Fake:
        def issue(self, _):
            return {"key": "TEST-1", "future_upstream_field": {"arbitrary": True}}

        def close(self):
            pass

    async def check():
        server = create_server(
            client_registry_factory=lambda: ClientRegistry(settings, lambda *_: Fake())
        )
        async with Client(server) as c:
            tools = {t.name: t for t in (await c.list_tools()).tools}
            schema = tools["list_jira_projects"].output_schema
            assert set(schema["$defs"]["ProjectInfo"]["required"]) == {
                "id",
                "key",
                "name",
                "project_type",
            }
            workflow_schema = tools["generate_project_workflow_graph"].output_schema
            assert "resource_uri" in workflow_schema["properties"]
            assert "WorkflowStatus" in workflow_schema["$defs"]
            assert all(
                "ctx" not in t.input_schema["properties"]
                and "get_client" not in t.input_schema["properties"]
                for t in tools.values()
            )
            result = await c.call_tool(
                "get_full_issue_details", {"issue_key": "TEST-1", "raw_data": True}
            )
            assert result.structured_content["raw_data"]["future_upstream_field"] == {
                "arbitrary": True
            }

    anyio.run(check)


def test_http_lifespan_and_host_origin_protection():
    from starlette.testclient import TestClient

    owned = []

    class TrackingRegistry(ClientRegistry):
        closed = False

        def close(self):
            super().close()
            self.closed = True

    def registry():
        r = TrackingRegistry(settings)
        owned.append(r)
        return r

    server = create_server(client_registry_factory=registry)
    app = server.streamable_http_app(host="localhost")
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
    headers = {
        "accept": "application/json, text/event-stream",
        "host": "localhost:8000",
        "origin": "http://localhost:3000",
    }
    with TestClient(app) as c:
        assert len(owned) == 1 and not owned[0].closed
        assert c.post("/mcp", json=payload, headers=headers).status_code == 200
        assert (
            c.post(
                "/mcp", json=payload, headers={**headers, "host": "evil.test"}
            ).status_code
            == 421
        )
        assert (
            c.post(
                "/mcp", json=payload, headers={**headers, "origin": "https://evil.test"}
            ).status_code
            == 403
        )
        assert len(owned) == 1
    assert owned[0].closed
