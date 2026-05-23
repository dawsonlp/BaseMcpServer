"""Main entry point for the MCP Server Creator."""

from mcp_commons import create_mcp_app, run_cli

from config import settings
from tool_config import get_tools_config


def main() -> None:
    run_cli(
        server_name=settings.server_name,
        tools_config=get_tools_config(),
        description="- Create and manage MCP servers",
        host=settings.host,
        port=settings.port,
    )


def create_app():
    """ASGI factory for running under an external server (uvicorn, etc.)."""
    return create_mcp_app(
        server_name=settings.server_name,
        tools_config=get_tools_config(),
    )


if __name__ == "__main__":
    main()
