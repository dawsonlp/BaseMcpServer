"""Owned Atlassian clients and ordinary instance/key helpers."""

import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from threading import Condition, RLock
from typing import Literal, TypedDict

import requests
from atlassian import Jira, Confluence

from config import Settings
from exceptions import JiraConnectionError, JiraNotFoundError, JiraValidationError

Service = Literal["jira", "confluence"]
AtlassianClient = Jira | Confluence
ClientFactory = Callable[[Service, str, Settings], AtlassianClient]
ISSUE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")


class InstanceInfo(TypedDict):
    name: str
    url: str
    user: str
    description: str
    is_default: bool


def build_client(
    service: Service, name: str, configuration: Settings
) -> AtlassianClient:
    instance = (
        configuration.get_jira_instance(name)
        if service == "jira"
        else configuration.get_confluence_instance(name)
    )
    if instance is None:
        raise JiraNotFoundError(
            f"{service.title()} instance '{name}' not found in configuration."
        )
    session = requests.Session()
    try:
        cls = Jira if service == "jira" else Confluence
        client = cls(
            url=instance.url,
            username=instance.user,
            password=instance.token,
            cloud=instance.url.endswith(".atlassian.net"),
            session=session,
            timeout=75,
            backoff_and_retry=False,
        )
        if service == "jira":
            client.myself()
        return client
    except Exception as error:
        session.close()
        raise JiraConnectionError(
            "Failed to initialize Atlassian client", instance_name=name
        ) from error


class ClientRegistry:
    """One lifespan owns the clients; one lock serializes each service/instance.

    An operation holds its lock across all calls, including compound writes.
    Shutdown rejects new work and waits for queued/running operations before close.
    """

    def __init__(self, configuration: Settings, factory: ClientFactory = build_client):
        self.configuration = configuration
        self._factory = factory
        self._clients: dict[tuple[Service, str], AtlassianClient] = {}
        self._locks: dict[tuple[Service, str], RLock] = {}
        self._condition = Condition()
        self._active = 0
        self._closed = False

    def resolve_name(self, instance_name: str | None) -> str:
        name = instance_name or self.configuration.get_default_instance_name()
        if not name:
            raise JiraValidationError(
                "No Jira instances configured. Check config.yaml."
            )
        return name

    @contextmanager
    def operation(
        self, service: Service, name: str
    ) -> Iterator[Callable[[], AtlassianClient]]:
        key = (service, name)
        with self._condition:
            if self._closed:
                raise RuntimeError("Client registry is closed")
            lock = self._locks.setdefault(key, RLock())
            self._active += 1
            self._condition.notify_all()
        try:
            with lock:

                def acquire() -> AtlassianClient:
                    # This callable is scoped to the operation and must not escape it.
                    if key not in self._clients:
                        self._clients[key] = self._factory(
                            service, name, self.configuration
                        )
                    return self._clients[key]

                yield acquire
        finally:
            with self._condition:
                self._active -= 1
                self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.wait_for(lambda: self._active == 0)
            clients = list(self._clients.values())
            self._clients.clear()
        errors = []
        for client in clients:
            try:
                client.close()
            except Exception as error:
                errors.append(error)
        if errors:
            raise ExceptionGroup("Failed to close Atlassian clients", errors)


def get_instances_info(configuration: Settings) -> list[InstanceInfo]:
    """Get information about all configured Jira instances."""
    instances = configuration.get_jira_instances()
    default_name = configuration.get_default_instance_name()
    result = []
    for name, inst in instances.items():
        result.append(
            {
                "name": name,
                "url": inst.url,
                "user": inst.user,
                "description": inst.description,
                "is_default": name == default_name,
            }
        )
    return result


def validate_issue_key(issue_key: str) -> str:
    """Validate and return a cleaned issue key."""
    if not issue_key or not isinstance(issue_key, str):
        raise JiraValidationError("Issue key is required.")
    cleaned = issue_key.strip().upper()
    if not ISSUE_KEY_PATTERN.match(cleaned):
        raise JiraValidationError(
            f"Invalid issue key format: '{issue_key}'. Expected format: PROJECT-123"
        )
    return cleaned
