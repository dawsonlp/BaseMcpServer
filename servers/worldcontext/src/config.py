"""
Configuration management for WorldContext MCP Server.

Consolidated to use mcp-commons configuration utilities.
"""

from pathlib import Path
from mcp_commons import create_config, load_dotenv_file

# Load environment variables from .env file if present
load_dotenv_file()

# Try multiple config file locations in order of preference
config_file = None
possible_locations = [
    Path.home() / ".config" / "mcp-manager" / "servers" / "worldcontext" / "config.yaml",  # mcp-manager managed
    Path.home() / ".config" / "worldcontext" / "config.yaml",  # legacy location
    Path.cwd() / "config.yaml"  # local development
]

for location in possible_locations:
    if location.exists():
        config_file = str(location)
        break

# Create configuration using mcp-commons
config = create_config(config_file=config_file, env_prefix="WORLDCONTEXT")
