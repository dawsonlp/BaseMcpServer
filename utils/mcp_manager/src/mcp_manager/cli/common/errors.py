"""
Error handling for the MCP Manager CLI.

One error type and one handler. Commands raise MCPManagerError with a clear
message (or any exception bubbles up); handle_error renders it and exits.
"""

import sys
from typing import Optional

from rich.panel import Panel

from mcp_manager.cli.common.output import StatusIcon, get_output_manager


class MCPManagerError(Exception):
    """A user-facing error carrying a clean, printable message."""


def handle_error(error: Exception, context: Optional[str] = None, exit_on_error: bool = True) -> None:
    """Render an error and (by default) exit non-zero."""
    output = get_output_manager()
    title = f"{StatusIcon.ERROR} Error"
    if context:
        title += f" — {context}"
    message = str(error) or error.__class__.__name__
    output.console.print(Panel(message, title=title, border_style="red", padding=(1, 2)))
    if exit_on_error:
        sys.exit(getattr(error, "exit_code", 1))
