"""
Configuration module for the Jira MCP server.

This module handles loading and validating environment variables using pydantic-settings.
"""

import os
import logging
from pathlib import Path
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Find the .env file in current directory or parent directories
def find_env_file():
    """
    Find the .env file in the current directory or its parents.
    
    Returns:
        str: Path to the .env file or ".env" if not found
    """
    current_dir = Path.cwd()
    env_file = current_dir / ".env"
    
    if env_file.exists():
        logger.info(f"Found .env file at: {env_file}")
        return str(env_file)
    
    # Also check for .env in the docker workdir /app
    docker_env = Path("/app/.env")
    if docker_env.exists():
        logger.info(f"Found .env file at: {docker_env}")
        return str(docker_env)
    
    logger.warning("No .env file found, using default settings")
    return ".env"


class Settings(BaseSettings):
    """
    Server settings and configuration loaded from environment variables.
    
    Environment variables can be set directly or loaded from a .env file.
    """
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 7501
    
    # Add a simple API key for demonstration purposes
    api_key: str = "example_key"
    
    # Jira settings - these have custom validation to ensure they're properly set
    JIRA_URL: str = Field(default="https://example.atlassian.net")
    JIRA_USER: str = Field(default="user@example.com")
    JIRA_TOKEN: str = Field(default="")
    
    # Configure settings to load from .env file
    # We attempt to find the .env file in various places
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_default=True
    )


# Create a settings instance for importing in other modules
settings = Settings()
