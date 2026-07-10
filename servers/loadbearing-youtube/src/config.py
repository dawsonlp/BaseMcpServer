"""Configuration management for the loadbearing_youtube MCP Server."""

from mcp_commons import create_config, load_dotenv_file

load_dotenv_file()

# mcp-commons looks under ~/.config/mcp-manager/servers/loadbearing-youtube/config.yaml
# first, then ~/.config/loadbearing-youtube/config.yaml, then ./config.yaml.
config = create_config(server_name="loadbearing-youtube", env_prefix="LOADBEARING_YOUTUBE")
