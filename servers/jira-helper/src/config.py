"""
Configuration module for the Jira MCP server.

Loads a YAML config that lists Jira/Confluence instances under
`instances.<name>.jira` / `instances.<name>.confluence`. Path discovery
delegates to `mcp_commons.find_server_config` (mcp-manager-first, then
XDG, then CWD).
"""

import logging
from pathlib import Path

import yaml
from mcp_commons import find_server_config

logger = logging.getLogger(__name__)


def _resolve_config_path() -> Path:
    """Locate config.yaml. Fail fast if no real config exists."""
    path = find_server_config("jira-helper", filename="config.yaml")
    if path is None:
        raise FileNotFoundError(
            "No config.yaml found for jira-helper. Expected at "
            "~/.config/mcp-manager/servers/jira-helper/config.yaml. "
            "Copy config.yaml.example to that location and fill in your "
            "Jira/Confluence instance details."
        )
    return path


class JiraInstance:
    """A single Jira instance configuration."""

    def __init__(self, name: str, url: str, user: str, token: str, description: str = ""):
        self.name = name
        self.url = url
        self.user = user
        self.token = token
        self.description = description or f"Jira instance at {url}"

    def __repr__(self):
        return f"JiraInstance(name='{self.name}', url='{self.url}', user='{self.user}')"


class ConfluenceInstance:
    """A single Confluence instance configuration."""

    def __init__(self, name: str, url: str, user: str, token: str, description: str = ""):
        self.name = name
        self.url = url
        self.user = user
        self.token = token
        self.description = description or f"Confluence instance at {url}"

    def __repr__(self):
        return f"ConfluenceInstance(name='{self.name}', url='{self.url}', user='{self.user}')"


class Settings:
    """Server settings loaded from the resolved YAML config file."""

    def __init__(self):
        self.config_file = _resolve_config_path()
        self.config_data = self._load_config()

        server_config = self.config_data.get("server", {})
        self.server_name: str = server_config.get("name", "jira-helper-server")
        self.host: str = server_config.get("host", "0.0.0.0")
        self.port: int = server_config.get("port", 7501)
        self.api_key: str = server_config.get("api_key", "example_key")
        self.debug_mode: bool = server_config.get("debug_mode", False)
        self.log_level: str = server_config.get("log_level", "INFO")
        self.log_file: str = server_config.get("log_file", "/tmp/jira_helper_debug.log")

        self.default_jira_instance: str | None = self.config_data.get("default_jira_instance")

    def _load_config(self) -> dict:
        try:
            with open(self.config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            logger.info(f"Loaded config from {self.config_file}")
            return data
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config file {self.config_file}: {e}")
            raise

    def get_jira_instances(self) -> dict[str, JiraInstance]:
        """All Jira instances under `instances.<name>.jira` in the config."""
        instances: dict[str, JiraInstance] = {}
        for instance_name, instance_data in self.config_data.get("instances", {}).items():
            jira_config = instance_data.get("jira") or {}
            if jira_config.get("url"):
                instances[instance_name] = JiraInstance(
                    name=instance_name,
                    url=jira_config.get("url", ""),
                    user=jira_config.get("username", jira_config.get("user", "")),
                    token=jira_config.get("api_token", jira_config.get("token", "")),
                    description=instance_data.get("description", ""),
                )
        return instances

    def get_default_instance_name(self) -> str | None:
        instances = self.get_jira_instances()
        if not instances:
            return None
        if self.default_jira_instance and self.default_jira_instance in instances:
            return self.default_jira_instance
        if "primary" in instances:
            return "primary"
        return next(iter(instances.keys()))

    def get_jira_instance(self, instance_name: str | None = None) -> JiraInstance | None:
        instances = self.get_jira_instances()
        if not instances:
            return None
        if instance_name is None:
            instance_name = self.get_default_instance_name()
        return instances.get(instance_name) if instance_name else None

    def get_confluence_instances(self) -> dict[str, ConfluenceInstance]:
        """All Confluence instances under `instances.<name>.confluence` in the config."""
        instances: dict[str, ConfluenceInstance] = {}
        for instance_name, instance_data in self.config_data.get("instances", {}).items():
            confluence_config = instance_data.get("confluence") or {}
            if confluence_config.get("url"):
                instances[instance_name] = ConfluenceInstance(
                    name=instance_name,
                    url=confluence_config.get("url", ""),
                    user=confluence_config.get("username", confluence_config.get("user", "")),
                    token=confluence_config.get("api_token", confluence_config.get("token", "")),
                    description=instance_data.get("description", ""),
                )
        return instances

    def get_confluence_instance(self, instance_name: str | None = None) -> ConfluenceInstance | None:
        instances = self.get_confluence_instances()
        if not instances:
            return None
        if instance_name is None:
            instance_name = self.get_default_instance_name()
        return instances.get(instance_name) if instance_name else None


# Module-level singleton imported by other modules.
settings = Settings()
