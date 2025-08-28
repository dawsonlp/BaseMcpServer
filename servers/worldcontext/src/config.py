"""
Configuration management for WorldContext MCP Server.

Consolidated to use mcp-commons configuration utilities.
"""

from pathlib import Path
from mcp_commons import create_config, load_dotenv_file

# Load environment variables from .env file if present
load_dotenv_file()

# Try multiple config file locations
config_file = None
possible_locations = [
    Path.home() / ".config" / "worldcontext" / "config.yaml",
    Path.cwd() / "config.yaml"
]

for location in possible_locations:
    if location.exists():
        config_file = str(location)
        break

# Create configuration using mcp-commons
config = create_config(config_file=config_file, env_prefix="WORLDCONTEXT")
