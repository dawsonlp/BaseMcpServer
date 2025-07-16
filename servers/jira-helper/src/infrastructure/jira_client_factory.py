"""
Jira Client Factory implementation using BaseJiraAdapter pattern.

This module provides the JiraClientFactory implementation with
centralized error handling and connection management.
"""

import logging

from jira import JIRA

from domain.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraInstanceNotFound,
    JiraTimeoutError,
)
from domain.ports import ConfigurationProvider, JiraClientFactory
from infrastructure.base_adapter import BaseJiraAdapter

logger = logging.getLogger(__name__)


class JiraClientFactoryImpl(BaseJiraAdapter, JiraClientFactory):
    """Factory for creating Jira clients using base adapter pattern."""

    def __init__(self, config_provider: ConfigurationProvider):
        super().__init__(self, config_provider)
        self._clients: dict[str, JIRA] = {}

    def create_client(self, instance_name: str | None = None) -> JIRA:
        """Create a Jira client for the specified instance."""
        async def operation(_):
            # Resolve instance name
            resolved_instance = self._resolve_instance_name(instance_name)

            # Check if client already exists
            if resolved_instance in self._clients:
                return self._clients[resolved_instance]

            # Get instance configuration
            instance = self._config_provider.get_instance(resolved_instance)
            if instance is None:
                available_instances = list(self._config_provider.get_instances().keys())
                raise JiraInstanceNotFound(resolved_instance, available_instances)

            # Create Jira client
            client = JIRA(
                server=instance.url,
                basic_auth=(instance.user, instance.token),
                timeout=30  # 30 second timeout
            )

            # Cache the client
            self._clients[resolved_instance] = client
            logger.info(f"Created Jira client for instance: {resolved_instance}")

            return client

        {
            "authentication": JiraAuthenticationError(instance_name or "default"),
            "unauthorized": JiraAuthenticationError(instance_name or "default"),
            "timeout": JiraTimeoutError("client_creation", instance_name or "default", 30),
            "connection": JiraConnectionError(instance_name or "default")
        }

        # Note: This is a sync method, so we need to handle it differently
        try:
            # Resolve instance name
            if instance_name is None:
                instance_name = self._config_provider.get_default_instance_name()
                if instance_name is None:
                    available_instances = list(self._config_provider.get_instances().keys())
                    raise JiraInstanceNotFound("default", available_instances)

            # Check if client already exists
            if instance_name in self._clients:
                return self._clients[instance_name]

            # Get instance configuration
            instance = self._config_provider.get_instance(instance_name)
            if instance is None:
                available_instances = list(self._config_provider.get_instances().keys())
                raise JiraInstanceNotFound(instance_name, available_instances)

            # Create Jira client
            client = JIRA(
                server=instance.url,
                basic_auth=(instance.user, instance.token),
                timeout=30  # 30 second timeout
            )

            # Cache the client
            self._clients[instance_name] = client
            logger.info(f"Created Jira client for instance: {instance_name}")

            return client

        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "unauthorized" in error_msg:
                raise JiraAuthenticationError(instance_name, str(e))
            elif "timeout" in error_msg:
                raise JiraTimeoutError("client_creation", instance_name, 30)
            else:
                raise JiraConnectionError(instance_name, str(e))

    def validate_instance(self, instance_name: str) -> bool:
        """Validate that an instance exists and is properly configured."""
        try:
            client = self.create_client(instance_name)
            # Try a simple API call to validate connection
            client.myself()
            return True
        except Exception:
            return False

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """Resolve instance name to use."""
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance
