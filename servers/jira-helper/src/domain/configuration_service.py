"""
Configuration service for instance and configuration management.

This service consolidates InstanceService with configuration logic
into a single, focused service.
"""

from domain.base_service import BaseJiraService
from domain.models import JiraInstance
from domain.ports import ConfigurationProvider, Logger


class ConfigurationService(BaseJiraService):
    """Domain service for instance and configuration management."""

    def __init__(self, config_provider: ConfigurationProvider, logger: Logger):
        super().__init__(config_provider, logger)

    def get_instances(self) -> list[JiraInstance]:
        """Get all configured Jira instances."""
        try:
            instances_dict = self._config_provider.get_instances()
            instances = list(instances_dict.values())
            self._logger.debug(f"Retrieved {len(instances)} configured instances")
            return instances
        except Exception as e:
            self._logger.error(f"Failed to get instances: {str(e)}")
            raise

    def get_default_instance(self) -> JiraInstance | None:
        """Get the default Jira instance."""
        try:
            default_instance = self._config_provider.get_instance()
            if default_instance:
                self._logger.debug(f"Retrieved default instance: {default_instance.name}")
            else:
                self._logger.warning("No default instance configured")
            return default_instance
        except Exception as e:
            self._logger.error(f"Failed to get default instance: {str(e)}")
            raise

    def get_instance_by_name(self, instance_name: str) -> JiraInstance | None:
        """Get a specific instance by name."""
        try:
            instances = self._config_provider.get_instances()
            instance = instances.get(instance_name)
            if instance:
                self._logger.debug(f"Retrieved instance: {instance_name}")
            else:
                self._logger.warning(f"Instance not found: {instance_name}")
            return instance
        except Exception as e:
            self._logger.error(f"Failed to get instance {instance_name}: {str(e)}")
            raise

    def get_default_instance_name(self) -> str | None:
        """Get the name of the default instance."""
        try:
            return self._config_provider.get_default_instance_name()
        except Exception as e:
            self._logger.error(f"Failed to get default instance name: {str(e)}")
            raise

    def validate_instance_exists(self, instance_name: str) -> bool:
        """Validate that an instance exists in configuration."""
        try:
            instances = self._config_provider.get_instances()
            exists = instance_name in instances
            if not exists:
                self._logger.warning(f"Instance does not exist: {instance_name}")
            return exists
        except Exception as e:
            self._logger.error(f"Failed to validate instance {instance_name}: {str(e)}")
            return False

    def get_available_instance_names(self) -> list[str]:
        """Get list of all available instance names."""
        try:
            instances = self._config_provider.get_instances()
            names = list(instances.keys())
            self._logger.debug(f"Retrieved {len(names)} instance names")
            return names
        except Exception as e:
            self._logger.error(f"Failed to get instance names: {str(e)}")
            raise
