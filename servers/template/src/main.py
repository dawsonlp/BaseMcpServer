"""Main entry point for the template MCP server."""

from mcp_commons import create_mcp_app, run_cli

from config import config
from tool_config import get_tools_config


def main() -> None:
    run_cli(
        server_name=config.get("server", "name", default="template"),
        tools_config=get_tools_config(),
        description="- Template MCP Server (replace this description)",
        host=config.get("server", "host", default="localhost"),
        port=config.get("server", "port", default=7501),
    )


def create_app():
    """ASGI factory for running under an external server (uvicorn, etc.)."""
    return create_mcp_app(
        server_name=config.get("server", "name", default="template"),
        tools_config=get_tools_config(),
    )


if __name__ == "__main__":
    main()
