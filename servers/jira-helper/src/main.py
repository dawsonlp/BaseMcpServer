"""Factory-based entry point for the Jira Helper MCP server."""

import encodings.idna  # noqa: F401 -- required by headless macOS stdio subprocesses
import logging
import sys
from logging import FileHandler
from typing import Literal, cast

from mcp.server import MCPServer

from config import settings
from tool_config import get_tools_config

Transport = Literal["stdio", "sse", "streamable-http"]
TRANSPORTS: tuple[Transport, ...] = ("stdio", "sse", "streamable-http")
DESCRIPTION = "Jira and Confluence integration"


def create_server() -> MCPServer:
    """Build a new server and register tools through the public SDK API."""
    server = MCPServer(
        name=settings.server_name,
        description=DESCRIPTION,
        log_level=settings.log_level.upper(),
    )
    for tool_name, spec in get_tools_config().items():
        function = spec.get("function")
        if not callable(function):
            raise TypeError(f"Tool {tool_name!r} does not define a callable function")
        server.add_tool(
            function,
            name=tool_name,
            description=spec.get("description") or f"Tool: {tool_name}",
        )
    return server


def create_app():
    """Build a Streamable HTTP ASGI app for an external ASGI server."""
    return create_server().streamable_http_app(host=settings.host)


def _print_help() -> None:
    print(
        "Jira Helper MCP Server\n\n"
        "Usage: jira-helper [stdio|streamable-http|sse]\n"
        "       jira-helper --transport [stdio|streamable-http|sse]\n\n"
        "stdio is used by local MCP clients; streamable-http is the preferred "
        "network transport; sse is retained for legacy clients."
    )


def _parse_transport(argv: list[str] | None = None) -> Transport | None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"help", "--help", "-h"}:
        _print_help()
        return None
    if args[0] == "--transport":
        if len(args) != 2:
            raise SystemExit("--transport requires exactly one value")
        value = args[1]
    elif len(args) == 1:
        value = args[0]
    else:
        raise SystemExit("Expected one transport argument; use --help for usage")
    if value not in TRANSPORTS:
        raise SystemExit(f"Unknown transport {value!r}; choose one of {', '.join(TRANSPORTS)}")
    return cast(Transport, value)


def main() -> None:
    transport = _parse_transport()
    if transport is None:
        return
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[FileHandler(settings.log_file, mode="a")],
    )
    run_options = {}
    if transport != "stdio":
        run_options = {"host": settings.host, "port": settings.port}
    try:
        create_server().run(transport, **run_options)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
