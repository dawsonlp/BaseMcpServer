"""
Configuration settings for the MCP Server Creator.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the MCP Server Creator server."""
    
    # MCP server settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 7501))
    api_key: str = os.getenv("API_KEY", "example_key")
    server_name: str = os.getenv("SERVER_NAME", "mcpservercreator-server")
    
    # Server creator settings
    output_dir: str = os.getenv("OUTPUT_DIR", "/tmp/generated_mcp_servers")
    template_dir: str = os.getenv("TEMPLATE_DIR", os.path.join(os.path.dirname(__file__), "templates"))
    
    # Security settings
    validate_code: bool = os.getenv("VALIDATE_CODE", "true").lower() == "true"
    restricted_imports: list[str] = [
        "os.system", "subprocess", "shutil.rmtree", "eval", "exec", 
        "__import__", "importlib", "pathlib.Path.unlink", "open"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
