"""Main entry point for the Jira Helper MCP server."""

# Force IDNA codec registration before any network calls.
#
# On macOS with Homebrew's Framework-build Python, encodings.idna (a stdlib
# codec submodule, not the third-party 'idna' package) can fail to load when
# Python is spawned as a headless subprocess via stdio pipes -- the transport
# used by MCP hosts such as Cline. Pre-importing it here, while sys.path is
# still in a reliable state during the normal import phase, ensures the codec
# is registered before requests/atlassian-python-api triggers a lazy
# codecs.lookup('idna') call on the first network connection.
#
# See: bug report "No module named 'encodings.idna'" / jira-helper 2.1.0
import encodings.idna  # noqa: F401

from mcp_commons import create_mcp_app, run_cli

from config import settings
from tool_config import get_tools_config


def main() -> None:
    run_cli(
        server_name=settings.server_name,
        tools_config=get_tools_config(),
        description="- Jira & Confluence Integration MCP Server",
        host=settings.host,
        port=settings.port,
        transports=("stdio", "sse", "streamable-http"),
        log_level=settings.log_level,
        log_file=settings.log_file,
    )


def create_app():
    """ASGI factory for running under an external server (uvicorn, etc.)."""
    return create_mcp_app(
        server_name=settings.server_name,
        tools_config=get_tools_config(),
    )


if __name__ == "__main__":
    main()
