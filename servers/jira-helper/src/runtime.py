"""Small, typed server-lifespan state, independent of MCP registration."""

from collections.abc import Callable
from typing import Any, TypeVar

from jira_client import ClientRegistry, Service

T = TypeVar("T")


class RuntimeState:
    def __init__(self, clients: ClientRegistry):
        self.clients = clients

    def execute(
        self,
        service: Service,
        instance_name: str | None,
        operation: Callable[..., T],
        arguments: dict[str, Any],
    ) -> T:
        name = self.clients.resolve_name(instance_name)
        with self.clients.operation(service, name) as get_client:
            return operation(instance_name=name, get_client=get_client, **arguments)
