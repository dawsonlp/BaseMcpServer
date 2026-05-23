"""Configuration for the template MCP server."""

from mcp_commons import create_config, load_dotenv_file

load_dotenv_file()

# mcp_commons looks under ~/.config/mcp-manager/servers/template/config.yaml
# first, then ~/.config/template/config.yaml, then ./config.yaml.
config = create_config(server_name="template", env_prefix="TEMPLATE")
