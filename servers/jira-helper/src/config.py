"""
Configuration module for the Jira MCP server.

This module handles loading and validating configuration from environment variables.
Supports both single instance (legacy) and multiple Jira instances through JSON configuration.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class JiraInstance(BaseModel):
    """
    Represents a single Jira instance configuration.
    """
    name: str = Field(..., description="Unique name for this Jira instance")
    url: str = Field(..., description="Jira instance URL")
    user: str = Field(..., description="Jira username/email")
    token: str = Field(..., description="Jira API token")
    description: str = Field(default="", description="Optional description of this instance")

    def __repr__(self):
        return f"JiraInstance(name='{self.name}', url='{self.url}', user='{self.user}')"


class Settings(BaseSettings):
    """
    Server settings and configuration loaded from environment variables.
    
    Supports both single instance (legacy) and multiple Jira instances through JSON configuration.
    """
    
    # Server configuration
    SERVER_NAME: str = Field(default="jira-helper-server", description="MCP server name")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=7501, description="Server port")
    API_KEY: str = Field(default="your_api_key_here", description="API key for authentication")
    DEBUG_MODE: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Legacy single instance configuration (for backward compatibility)
    JIRA_URL: str = Field(default="", description="Legacy single Jira instance URL")
    JIRA_USER: str = Field(default="", description="Legacy single Jira instance user")
    JIRA_TOKEN: str = Field(default="", description="Legacy single Jira instance token")
    
    # Multiple instances configuration (JSON format)
    JIRA_INSTANCES: str = Field(default="", description="JSON array of Jira instances")
    
    # Default instance configuration
    DEFAULT_JIRA_INSTANCE: str = Field(default="", description="Name of the default Jira instance")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_jira_instances(self) -> Dict[str, JiraInstance]:
        """
        Get all configured Jira instances.
        
        Returns:
            Dict[str, JiraInstance]: Dictionary mapping instance names to JiraInstance objects
        """
        instances = {}
        
        # First, try to load instances from JIRA_INSTANCES JSON
        if self.JIRA_INSTANCES:
            try:
                instances_data = json.loads(self.JIRA_INSTANCES)
                if isinstance(instances_data, list):
                    for instance_config in instances_data:
                        if isinstance(instance_config, dict) and "name" in instance_config:
                            instance = JiraInstance(**instance_config)
                            instances[instance.name] = instance
                            logger.info(f"Loaded Jira instance: {instance.name}")
                else:
                    logger.error("JIRA_INSTANCES must be a JSON array")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JIRA_INSTANCES JSON: {e}")
            except Exception as e:
                logger.error(f"Error loading Jira instances: {e}")
        
        # Add legacy single instance if configured and not already present
        if (self.JIRA_URL and self.JIRA_USER and self.JIRA_TOKEN and 
            not any(inst.url == self.JIRA_URL for inst in instances.values())):
            
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
                logger.info(f"Loaded legacy Jira instance as: {legacy_name}")
        
        return instances
    
    def get_default_instance_name(self) -> Optional[str]:
        """
        Get the name of the default Jira instance.
        
        Returns:
            Optional[str]: Name of the default instance, or None if no instances configured
        """
        instances = self.get_jira_instances()
        if not instances:
            return None
        
        # Use configured default if specified and exists
        if self.DEFAULT_JIRA_INSTANCE and self.DEFAULT_JIRA_INSTANCE in instances:
            return self.DEFAULT_JIRA_INSTANCE
        
        # Prefer "primary" if it exists (legacy compatibility)
        if "primary" in instances:
            return "primary"
        
        # Otherwise return the first instance
        return next(iter(instances.keys()))
    
    def get_jira_instance(self, instance_name: Optional[str] = None) -> Optional[JiraInstance]:
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
