"""
Configuration adapter for the Jira Helper.

This module implements the ConfigurationProvider port using the existing
configuration system, bridging between the domain layer and the current
configuration implementation.
"""


from config import settings
from domain.exceptions import (
    JiraConfigurationMissingError,
    JiraInstanceConfigurationError,
)
from domain.models import JiraInstance
from domain.ports import ConfigurationProvider


class ConfigurationAdapter(ConfigurationProvider):
    """Adapter that implements ConfigurationProvider using the existing config system."""

    def __init__(self):
        self._settings = settings

    def get_instances(self) -> dict[str, JiraInstance]:
        """Get all configured Jira instances."""
        try:
            # Get instances from the existing settings
            instances_dict = self._settings.get_jira_instances()

            # Convert to domain models
            domain_instances = {}
            default_instance_name = self._settings.get_default_instance_name()

            for name, config_instance in instances_dict.items():
                try:
                    domain_instance = JiraInstance(
                        name=name,
                        url=config_instance.url,
                        user=config_instance.user,
                        token=config_instance.token,
                        description=config_instance.description,
                        is_default=(name == default_instance_name)
                    )
                    domain_instances[name] = domain_instance
                except Exception as e:
                    raise JiraInstanceConfigurationError(
                        name, f"Invalid configuration: {str(e)}"
                    )

            if not domain_instances:
                raise JiraConfigurationMissingError("No Jira instances configured")

            return domain_instances

        except Exception as e:
            if isinstance(e, JiraConfigurationMissingError | JiraInstanceConfigurationError):
                raise
            raise JiraConfigurationMissingError(f"Failed to load configuration: {str(e)}")

    def get_default_instance_name(self) -> str | None:
        """Get the name of the default instance."""
        try:
            return self._settings.get_default_instance_name()
        except Exception:
            return None

    def get_instance(self, instance_name: str | None = None) -> JiraInstance | None:
        """Get a specific instance by name or the default instance."""
        try:
            instances = self.get_instances()

            if instance_name is None:
                # Get default instance
                default_name = self.get_default_instance_name()
                if default_name and default_name in instances:
                    return instances[default_name]
                # If no default specified, return first instance
                if instances:
                    return next(iter(instances.values()))
                return None

            return instances.get(instance_name)

        except Exception:
            return None

    def validate_instance(self, instance_name: str) -> bool:
        """Validate that an instance exists and is properly configured."""
        try:
            instances = self.get_instances()
            if instance_name not in instances:
                return False

            instance = instances[instance_name]
            # Basic validation - the JiraInstance constructor already validates required fields
            return bool(instance.name and instance.url and instance.user and instance.token)

        except Exception:
            return False

    def get_instance_names(self) -> list[str]:
        """Get list of all configured instance names."""
        try:
            instances = self.get_instances()
            return list(instances.keys())
        except Exception:
            return []

    def has_instances(self) -> bool:
        """Check if any instances are configured."""
        try:
            instances = self.get_instances()
            return len(instances) > 0
        except Exception:
            return False
