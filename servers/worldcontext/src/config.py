"""Configuration management for WorldContext MCP Server."""

from mcp_commons import create_config, load_dotenv_file

load_dotenv_file()

# mcp-commons looks under ~/.config/mcp-manager/servers/worldcontext/config.yaml
# first, then ~/.config/worldcontext/config.yaml, then ./config.yaml.
config = create_config(server_name="worldcontext", env_prefix="WORLDCONTEXT")
