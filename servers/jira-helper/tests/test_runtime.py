"""Ownership/concurrency checks with no Atlassian network access."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

import pytest

from jira_client import ClientRegistry, build_client


class FakeClient:
    def __init__(self):
        self.closed = 0

    def close(self):
        self.closed += 1


def test_registry_reuses_clients_serializes_and_drains_before_close():
    created = []
    entered, release, second_started, closing = Event(), Event(), Event(), Event()

    def factory(*_):
        client = FakeClient()
        created.append(client)
        return client

    registry = ClientRegistry(SimpleNamespace(), factory)

    def first():
        with registry.operation("jira", "one") as get:
            assert get() is get()
            entered.set()
            assert release.wait(3)

    def second():
        second_started.set()
        with registry.operation("jira", "one") as get:
            return get()

    def close():
        closing.set()
        registry.close()

    with ThreadPoolExecutor(4) as pool:
        a = pool.submit(first)
        assert entered.wait(3)
        b = pool.submit(second)
        assert second_started.wait(3)
        # An unrelated instance must proceed while 'one' is occupied.
        with registry.operation("jira", "two") as get:
            assert get() is not created[0]
        # Close only after the second operation has entered the owned queue.
        with registry._condition:
            assert registry._condition.wait_for(
                lambda: registry._active == 2, timeout=3
            )
        c = pool.submit(close)
        assert closing.wait(3)
        assert not c.done()
        assert created[0].closed == 0
        release.set()
        a.result(3)
        assert b.result(3) is created[0]
        c.result(3)
    assert [x.closed for x in created] == [1, 1]
    registry.close()
    assert [x.closed for x in created] == [1, 1]
    with pytest.raises(RuntimeError, match="closed"):
        with registry.operation("jira", "one"):
            pass


def test_failed_initialization_closes_session(monkeypatch):
    session = FakeClient()
    monkeypatch.setattr("jira_client.requests.Session", lambda: session)

    class BrokenClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 75
            assert kwargs["backoff_and_retry"] is False

        def myself(self):
            raise OSError("connection failed")

    monkeypatch.setattr("jira_client.Jira", BrokenClient)
    config = SimpleNamespace(
        get_jira_instance=lambda _: SimpleNamespace(
            url="https://test.atlassian.net", user="test", token="secret"
        )
    )
    with pytest.raises(Exception, match="initialize"):
        build_client("jira", "test", config)
    assert session.closed == 1
