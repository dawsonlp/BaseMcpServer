"""
Configuration module for the MCP server.

This module handles loading and validating environment variables using pydantic-settings.
Customize this file to include any configuration parameters your server requires.
"""

import os
import logging
from pathlib import Path
from pydantic import Field
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
    Customize this class to include any settings your MCP server needs.
    """
    
    # MCP Server identity
    server_name: str = "template-server"
    
    # Server settings - Customize with your preferred defaults
    host: str = "0.0.0.0"  # Listen on all network interfaces
    port: int = 7501  # Default MCP server port
    
    # Security settings - Replace with your authentication requirements
    api_key: str = Field(default="your_default_api_key")  # Change this for production!
    
    # Add your own custom settings below
    # example_setting: str = Field(default="default_value")
    
    # Configure settings to load from .env file
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_default=True
    )


# Create a settings instance for importing in other modules
settings = Settings()
