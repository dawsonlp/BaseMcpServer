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

# Find the .env file in script directory or parent directories
def find_env_file():
    """
    Find the .env file relative to this script's location or in parent directories.
    
    Returns:
        str: Path to the .env file or ".env" if not found
    """
    # Get the directory containing this config.py file
    script_dir = Path(__file__).parent
    
    # Search locations in order of preference
    search_locations = [
        script_dir / ".env",                    # Same directory as config.py
        script_dir.parent / ".env",             # Parent directory (likely location)
        Path.cwd() / ".env",                    # Current working directory (fallback)
        Path("/app/.env")                       # Docker workdir
    ]
    
    for env_file in search_locations:
        if env_file.exists():
            logger.info(f"Found .env file at: {env_file}")
            return str(env_file)
    
    logger.warning("No .env file found, using default settings")
    logger.info(f"Searched locations: {[str(loc) for loc in search_locations]}")
    return ".env"


class Settings(BaseSettings):
    """
    Server settings and configuration loaded from environment variables.
    
    Environment variables can be set directly or loaded from a .env file.
    """
    
    # MCP Server identity
    server_name: str = "jira-clone-server"
    
    # Server settings (rarely need to be changed in Docker environments)
    # These defaults work well with Docker's port mapping
    host: str = "0.0.0.0"  # Listen on all interfaces
    port: int = 7501       # Default MCP port
    
    # API key for authentication (should be changed in production)
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
