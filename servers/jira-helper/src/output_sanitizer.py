"""
Output sanitization utilities for jira-helper.

Pure functions for sanitizing user-authored content before it is returned in
tool responses. Applied at field-extraction time, not at the serialization
boundary.

See: docs/architecture/cline-safe-output.md
"""


def sanitize_string(value: str) -> str:
    """
    Escape angle bracket sequences in a user-authored string.

    Replaces ``<`` with ``&lt;`` to prevent angle bracket sequences from
    being interpreted as protocol markup by Cline or other XML-sensitive
    consumers.

    This function is idempotent: ``&lt;`` contains no ``<``, so applying
    the function twice produces the same result as applying it once.

    Args:
        value: The string to sanitize. None is treated as empty string.

    Returns:
        The sanitized string, or an empty string if value is None.
    """
    if not value:
        return value if value == "" else ""
    return value.replace("<", "&lt;")


def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum character length.

    If the string exceeds max_length, it is truncated to max_length characters
    and the suffix is appended. Strings at or below max_length are returned
    unchanged.

    Args:
        value: The string to truncate. None is treated as empty string.
        max_length: Maximum number of characters before truncation.
        suffix: String appended when truncation occurs. Defaults to "...".

    Returns:
        The original string if within max_length, or a truncated string with
        suffix appended. Returns empty string if value is None.
    """
    if not value:
        return value if value == "" else ""
    if len(value) <= max_length:
        return value
    return value[:max_length] + suffix