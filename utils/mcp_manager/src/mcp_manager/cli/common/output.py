"""
Console output for the MCP Manager CLI.

A thin wrapper over a Rich console with the four message levels the CLI uses.
Status/health tables lived here for the removed process-management features and
are gone; commands render their own tables directly.
"""

from enum import Enum
from typing import Optional

from rich.console import Console


class StatusIcon(str, Enum):
    """Status icons for consistent messages."""

    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"


class OutputTheme:
    """Color theme for console output."""

    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "blue"


class RichOutputManager:
    """Rich-based console output with the four message levels."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.theme = OutputTheme()

    def success(self, message: str, **kwargs) -> None:
        self.console.print(f"{StatusIcon.SUCCESS} {message}", style=self.theme.SUCCESS, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self.console.print(f"{StatusIcon.ERROR} {message}", style=self.theme.ERROR, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self.console.print(f"{StatusIcon.WARNING} {message}", style=self.theme.WARNING, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self.console.print(f"{StatusIcon.INFO} {message}", style=self.theme.INFO, **kwargs)


# Global output manager instance
output = RichOutputManager()


def get_output_manager() -> RichOutputManager:
    """Get the global output manager."""
    return output
