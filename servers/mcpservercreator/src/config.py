"""
Configuration settings for the MCP Server Creator.
"""

import os
import logging
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

def find_env_file():
    """
    Find the .env file in order of preference:
    1. ~/.config/mcp-manager/servers/mcpservercreator/.env (mcp-manager managed)
    2. Current directory .env (local development)
    3. Docker workdir /app/.env (containerized deployment)
    
    Returns:
        str: Path to the .env file or ".env" if not found
    """
    # MCP-manager managed config location
    mcp_manager_env = Path.home() / ".config" / "mcp-manager" / "servers" / "mcpservercreator" / ".env"
    if mcp_manager_env.exists():
        logger.info(f"Found mcp-manager .env file at: {mcp_manager_env}")
        return str(mcp_manager_env)
    
    # Local development
    current_dir = Path.cwd()
    env_file = current_dir / ".env"
    if env_file.exists():
        logger.info(f"Found local .env file at: {env_file}")
        return str(env_file)
    
    # Docker workdir /app
    docker_env = Path("/app/.env")
    if docker_env.exists():
        logger.info(f"Found docker .env file at: {docker_env}")
        return str(docker_env)
    
    logger.warning("No .env file found, using default settings")
    return ".env"


class Settings(BaseSettings):
    """Configuration settings for the MCP Server Creator server."""
    
    # MCP server settings
    host: str = "0.0.0.0"
    port: int = 7501
    api_key: str = "example_key"
    server_name: str = "mcpservercreator-server"
    
    # Server creator settings
    output_dir: str = "/tmp/generated_mcp_servers"
    template_dir: str = Field(default_factory=lambda: os.path.join(os.path.dirname(__file__), "templates"))
    
    # Security settings
    validate_code: bool = True
    restricted_imports: list[str] = Field(default=[
        "os.system", "subprocess", "shutil.rmtree", "eval", "exec", 
        "__import__", "importlib", "pathlib.Path.unlink", "open"
    ])
    
    # Configure settings to load from .env file
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_default=True
    )


settings = Settings()
