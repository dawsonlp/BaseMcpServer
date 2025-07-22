"""
Configuration adapter to bridge Settings class with ConfigurationProvider interface.
"""

from typing import Dict, Optional
from domain.ports import ConfigurationProvider
from domain.models import JiraInstance
from config import Settings


class SettingsConfigurationAdapter(ConfigurationProvider):
    """Adapter that implements ConfigurationProvider interface using Settings class."""
    
    def __init__(self, settings: Settings):
        self._settings = settings
    
    def get_instances(self) -> Dict[str, JiraInstance]:
        """Get all configured Jira instances."""
        jira_instances = self._settings.get_jira_instances()
        
        # Convert to domain JiraInstance objects
        domain_instances = {}
        for name, instance in jira_instances.items():
            domain_instance = JiraInstance(
                name=instance.name,
                url=instance.url,
                user=instance.user,
                token=instance.token,
                description=instance.description
            )
            domain_instances[name] = domain_instance
        
        return domain_instances
    
    def get_default_instance_name(self) -> Optional[str]:
        """Get the name of the default instance."""
        return self._settings.get_default_instance_name()
    
    def get_instance(self, instance_name: Optional[str] = None) -> Optional[JiraInstance]:
        """Get a specific instance by name or the default instance."""
        settings_instance = self._settings.get_jira_instance(instance_name)
        
        if settings_instance is None:
            return None
        
        # Convert to domain JiraInstance
        return JiraInstance(
            name=settings_instance.name,
            url=settings_instance.url,
            user=settings_instance.user,
            token=settings_instance.token,
            description=settings_instance.description
        )
