"""
Configuration module for the MCP server.

This module handles loading and validating environment variables using pydantic-settings.
Customize this file to include any configuration parameters your server requires.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Server settings and configuration loaded from environment variables.
    
    Environment variables can be set directly or loaded from a .env file.
    Customize this class to include any settings your MCP server needs.
    """
    
    # Server settings - Customize with your preferred defaults
    host: str = "0.0.0.0"  # Listen on all network interfaces
    port: int = 7501  # Default MCP server port
    
    # Security settings - Replace with your authentication requirements
    api_key: str = "your_default_api_key"  # Change this for production!
    
    # Add your own custom settings below
    # example_setting: str = "default_value"
    
    # Configure settings to load from .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Create a settings instance for importing in other modules
settings = Settings()
