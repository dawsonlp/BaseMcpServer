"""Factory-based entry point for the WorldContext MCP server."""

import logging
import sys
from importlib.metadata import version
from typing import Literal, cast

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from config import config
from tool_config import get_tools_config

Transport = Literal["stdio", "sse", "streamable-http"]
TRANSPORTS: tuple[Transport, ...] = ("stdio", "sse", "streamable-http")
DESCRIPTION = "Context Provider"
PACKAGE_VERSION = version("worldcontext-mcp-server")
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _transport_security(host: str) -> TransportSecuritySettings | None:
    if host in _LOOPBACK_HOSTS:
        return None
    allowed_hosts = _string_list(config.get("server", "allowed_hosts", default=[]))
    allowed_origins = _string_list(config.get("server", "allowed_origins", default=[]))
    if not allowed_hosts or not allowed_origins:
        raise ValueError(
            "Non-loopback Streamable HTTP requires non-empty server.allowed_hosts "
            "and server.allowed_origins."
        )
    return TransportSecuritySettings(
        allowed_hosts=allowed_hosts, allowed_origins=allowed_origins,
    )


def create_server() -> MCPServer:
    """Build a new server and register tools through the public SDK API."""
    server = MCPServer(
        name=str(config.get("server", "name", default="worldcontext")),
        description=DESCRIPTION,
        version=PACKAGE_VERSION,
    )
    for tool_name, spec in get_tools_config().items():
        function = spec.get("function")
        if not callable(function):
            raise TypeError(f"Tool {tool_name!r} does not define a callable function")
        server.add_tool(
            function,
            name=tool_name,
            title=spec["title"],
            description=spec.get("description") or f"Tool: {tool_name}",
            annotations=cast(ToolAnnotations, spec["annotations"]),
            structured_output=True,
        )
    return server


def create_app():
    """Build a Streamable HTTP ASGI app for an external ASGI server."""
    host = str(config.get("server", "host", default="localhost"))
    return create_server().streamable_http_app(
        host=host, transport_security=_transport_security(host),
    )


def _print_help() -> None:
    print(
        "WorldContext MCP Server\n\n"
        "Usage: worldcontext [stdio|streamable-http|sse]\n"
        "       worldcontext --transport [stdio|streamable-http|sse]\n\n"
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
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    run_options = {}
    if transport != "stdio":
        host = str(config.get("server", "host", default="localhost"))
        run_options = {
            "host": host,
            "port": int(config.get("server", "port", default=7501)),
        }
        if transport == "streamable-http":
            run_options["transport_security"] = _transport_security(host)
    try:
        create_server().run(transport, **run_options)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
