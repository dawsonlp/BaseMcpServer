"""
Configuration module for the Document Processor MCP server.

This module handles loading and validating environment variables using pydantic-settings.
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
    Document Processor server settings and configuration loaded from environment variables.
    
    Environment variables can be set directly or loaded from a .env file.
    """
    
    # MCP Server identity
    server_name: str = "document-processor"
    
    # Server settings
    host: str = "0.0.0.0"  # Listen on all network interfaces
    port: int = 7502  # Default port for document processor
    
    # Security settings
    api_key: str = Field(default="doc_processor_api_key")
    
    # Document processing settings
    output_directory: str = Field(default="/app/output", description="Directory for output files")
    input_directory: str = Field(default="/app/input", description="Directory for input files")
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    
    # PDF generation settings
    pdf_engine: str = Field(default="weasyprint", description="PDF engine: weasyprint, pdfkit, or reportlab")
    
    # HTML template settings
    html_template_dir: str = Field(default="/app/templates", description="Directory for HTML templates")
    
    # Configure settings to load from .env file
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_default=True
    )


# Create a settings instance for importing in other modules
settings = Settings()
