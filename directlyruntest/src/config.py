"""
Configuration module for the DirectlyRunTest MCP server.

This module handles loading and validating environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Server settings and configuration loaded from environment variables.
    
    Environment variables can be set directly or loaded from a .env file.
    """
    
    # MCP Server identity
    server_name: str = "directlyruntest-server"
    
    # Server settings (rarely need to be changed in Docker environments)
    # These defaults work well with Docker's port mapping
    host: str = "0.0.0.0"  # Listen on all interfaces
    port: int = 7501       # Default MCP port
    
    # API key for authentication (should be changed in production)
    api_key: str = "example_key"
    
    # Configure settings to load from .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Create a settings instance for importing in other modules
settings = Settings()
