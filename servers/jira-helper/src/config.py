"""
Configuration module for the Jira MCP server.

This module handles loading and validating configuration from YAML files.
Supports multiple Jira instances through clean YAML configuration.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

def find_config_file():
    """
    Find the config.yaml file in order of preference:
    1. ~/.mcp_servers/jira-helper-config.yaml (production)
    2. ./config.yaml (local development)
    3. ./config.yaml.example (fallback template)

    Returns:
        str: Path to the config file
    """
    # Production config (safe from git)
    production_config = Path.home() / ".mcp_servers" / "jira-helper-config.yaml"
    if production_config.exists():
        logger.info(f"Using production config: {production_config}")
        return str(production_config)

    # Local development config
    local_config = Path.cwd() / "config.yaml"
    if local_config.exists():
        logger.info(f"Using local config: {local_config}")
        return str(local_config)

    # Fallback to example template
    example_config = Path.cwd() / "config.yaml.example"
    if example_config.exists():
        logger.warning(f"Using example config: {example_config}")
        return str(example_config)

    logger.error("No config file found!")
    raise FileNotFoundError("No config.yaml file found. Please create one from config.yaml.example")


class JiraInstance:
    """
    Represents a single Jira instance configuration.
    """
    def __init__(self, name: str, url: str, user: str, token: str, description: str = ""):
        self.name = name
        self.url = url
        self.user = user
        self.token = token
        self.description = description or f"Jira instance at {url}"

    def __repr__(self):
        return f"JiraInstance(name='{self.name}', url='{self.url}', user='{self.user}')"


class Settings:
    """
    Server settings and configuration loaded from YAML files.

    Supports multiple Jira instances through clean YAML configuration.
    """

    def __init__(self):
        self.config_file = find_config_file()
        self.config_data = self._load_config()

        # Load server configuration
        server_config = self.config_data.get('server', {})
        self.server_name: str = server_config.get('name', 'jira-helper-server')
        self.host: str = server_config.get('host', '0.0.0.0')
        self.port: int = server_config.get('port', 7501)
        self.api_key: str = server_config.get('api_key', 'example_key')
        self.debug_mode: bool = server_config.get('debug_mode', False)
        self.log_level: str = server_config.get('log_level', 'INFO')

        # Default instance configuration
        self.default_jira_instance: str | None = self.config_data.get('default_jira_instance')

        # Legacy configuration (for backward compatibility)
        legacy_config = self.config_data.get('legacy', {})
        self.JIRA_URL: str = legacy_config.get('jira_url', 'https://example.atlassian.net')
        self.JIRA_USER: str = legacy_config.get('jira_user', 'user@example.com')
        self.JIRA_TOKEN: str = legacy_config.get('jira_token', '')

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                logger.info(f"Successfully loaded config from {self.config_file}")
                return config_data or {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config file {self.config_file}: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_file}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            raise

    def get_jira_instances(self) -> dict[str, JiraInstance]:
        """
        Get all configured Jira instances.

        Returns:
            Dict[str, JiraInstance]: Dictionary mapping instance names to JiraInstance objects
        """
        instances = {}

        # Load instances from YAML configuration
        jira_instances = self.config_data.get('jira_instances', [])

        for instance_config in jira_instances:
            name = instance_config.get("name")
            if name:
                instances[name] = JiraInstance(
                    name=name,
                    url=instance_config.get("url", ""),
                    user=instance_config.get("user", ""),
                    token=instance_config.get("token", ""),
                    description=instance_config.get("description", "")
                )

        # Add legacy single instance if configured and not already present
        if (self.JIRA_URL and self.JIRA_URL != "https://example.atlassian.net" and
            self.JIRA_USER and self.JIRA_USER != "user@example.com" and
            self.JIRA_TOKEN):

            # Use "primary" as the default name for legacy configuration
            legacy_name = "primary"
            if legacy_name not in instances:
                instances[legacy_name] = JiraInstance(
                    name=legacy_name,
                    url=self.JIRA_URL,
                    user=self.JIRA_USER,
                    token=self.JIRA_TOKEN,
                    description="Primary Jira instance (legacy configuration)"
                )

        return instances

    def get_default_instance_name(self) -> str | None:
        """
        Get the name of the default Jira instance.

        Returns:
            Optional[str]: Name of the default instance, or None if no instances configured
        """
        instances = self.get_jira_instances()
        if not instances:
            return None

        # Use configured default if specified
        if self.default_jira_instance and self.default_jira_instance in instances:
            return self.default_jira_instance

        # Prefer "primary" if it exists
        if "primary" in instances:
            return "primary"

        # Otherwise return the first instance
        return next(iter(instances.keys()))

    def get_jira_instance(self, instance_name: str | None = None) -> JiraInstance | None:
        """
        Get a specific Jira instance by name, or the default instance.

        Args:
            instance_name: Name of the instance to get, or None for default

        Returns:
            Optional[JiraInstance]: The requested instance, or None if not found
        """
        instances = self.get_jira_instances()
        if not instances:
            return None

        if instance_name is None:
            instance_name = self.get_default_instance_name()

        return instances.get(instance_name) if instance_name else None


# Create a settings instance for importing in other modules
settings = Settings()
