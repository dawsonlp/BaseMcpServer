"""
Validate a local server's configuration.

Only local stdio servers exist, so validation reduces to a well-formed name,
a real source directory (ideally with a pyproject.toml), and — best effort —
that the installed venv's Python is present.
"""

import re

from mcp_manager.core.models import Server, ValidationResult

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_server_config(server: Server) -> ValidationResult:
    """Validate a server's configuration. Errors are fatal; warnings are advisory."""
    result = ValidationResult(is_valid=True)

    if not server.name or len(server.name) > 50 or not _NAME_RE.match(server.name):
        result.add_error(
            "name",
            "Invalid server name",
            "Use 1-50 characters: letters, digits, '_' or '-'.",
        )

    if server.source_dir:
        if not server.source_dir.exists() or not server.source_dir.is_dir():
            result.add_error(
                "source_dir",
                f"Source directory not found: {server.source_dir}",
                "Reinstall the server from a valid source directory.",
            )
        elif not (server.source_dir / "pyproject.toml").exists():
            result.add_warning(
                "source_dir",
                "No pyproject.toml in the source directory",
                "mcp-manager installs servers as uv packages; a pyproject.toml is expected.",
            )

    if server.venv_dir:
        python_path = server.get_python_executable()
        if python_path and not python_path.exists():
            result.add_warning(
                "venv_dir",
                "Python executable not found in the server's virtual environment",
                "Reinstall the server to recreate its environment.",
            )

    return result
