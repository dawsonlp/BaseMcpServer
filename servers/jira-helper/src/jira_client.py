"""
Jira and Confluence client factory.

Consolidates client creation, caching, and instance resolution from the
old infrastructure/atlassian_repository.py, config_adapter, and confluence adapter.
"""

import logging
import re

from config import settings
from exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraNotFoundError,
    JiraValidationError,
)

logger = logging.getLogger(__name__)

# Client caches — one Jira/Confluence client per instance name
_jira_clients: dict = {}
_confluence_clients: dict = {}

ISSUE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")


def resolve_instance_name(instance_name: str = None) -> str:
    """Resolve instance name, falling back to default."""
    if instance_name:
        return instance_name
    default = settings.get_default_instance_name()
    if not default:
        raise JiraValidationError("No Jira instances configured. Check config.yaml.")
    return default


def get_jira_client(instance_name: str = None):
    """Get or create a cached Jira client for the given instance."""
    from atlassian import Jira

    name = resolve_instance_name(instance_name)

    if name in _jira_clients:
        return _jira_clients[name]

    instance = settings.get_jira_instance(name)
    if not instance:
        raise JiraNotFoundError(f"Jira instance '{name}' not found in configuration.")

    try:
        client = Jira(
            url=instance.url,
            username=instance.user,
            password=instance.token,
            cloud=instance.url.endswith(".atlassian.net"),
        )
        # Validate connection
        client.myself()
        _jira_clients[name] = client
        logger.info(f"Connected to Jira instance '{name}' at {instance.url}")
        return client
    except Exception as e:
        error_msg = str(e).lower()
        if "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg:
            raise JiraAuthenticationError(
                f"Authentication failed for instance '{name}': {e}", instance_name=name
            )
        raise JiraConnectionError(
            f"Failed to connect to Jira instance '{name}': {e}", instance_name=name
        )


def get_confluence_client(instance_name: str = None):
    """Get or create a cached Confluence client for the given instance."""
    from atlassian import Confluence

    name = resolve_instance_name(instance_name)

    if name in _confluence_clients:
        return _confluence_clients[name]

    instance = settings.get_confluence_instance(name)
    if not instance:
        raise JiraNotFoundError(f"Confluence instance '{name}' not found in configuration.")

    try:
        client = Confluence(
            url=instance.url,
            username=instance.user,
            password=instance.token,
            cloud=instance.url.endswith(".atlassian.net"),
        )
        _confluence_clients[name] = client
        logger.info(f"Connected to Confluence instance '{name}' at {instance.url}")
        return client
    except Exception as e:
        error_msg = str(e).lower()
        if "401" in error_msg or "403" in error_msg:
            raise JiraAuthenticationError(
                f"Authentication failed for Confluence instance '{name}': {e}",
                instance_name=name,
            )
        raise JiraConnectionError(
            f"Failed to connect to Confluence instance '{name}': {e}",
            instance_name=name,
        )


def get_instances_info() -> list[dict]:
    """Get information about all configured Jira instances."""
    instances = settings.get_jira_instances()
    default_name = settings.get_default_instance_name()
    result = []
    for name, inst in instances.items():
        result.append({
            "name": name,
            "url": inst.url,
            "user": inst.user,
            "description": inst.description,
            "is_default": name == default_name,
        })
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