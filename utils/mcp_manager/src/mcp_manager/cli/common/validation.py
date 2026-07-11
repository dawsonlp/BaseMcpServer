"""
CLI input validation helpers.

Only server-name validation is needed by the CLI (used at install time). The
former CLIValidator class validated ports/hosts/URLs for the removed
SSE/remote/process features and is gone.
"""

import re


def is_valid_server_name(name: str) -> bool:
    """Quick server-name validation: 1-50 chars, alphanumeric plus _ and -."""
    if not name or len(name) > 50:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))
