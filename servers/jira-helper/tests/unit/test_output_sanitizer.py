"""Unit tests for output_sanitizer module.

Tests assert business-meaningful outcomes: the sanitization eliminates the
protocol delimiter collision class, and truncation caps field length without
corrupting content.
"""

import pytest

from output_sanitizer import sanitize_string, truncate_string


# ---------------------------------------------------------------------------
# sanitize_string
# ---------------------------------------------------------------------------


def test_sanitize_string_escapes_single_angle_bracket():
    result = sanitize_string("hello <world>")
    assert "<" not in result
    assert "&lt;" in result


def test_sanitize_string_eliminates_environment_details_tag():
    """The known trigger pattern must not survive sanitization."""
    result = sanitize_string("Some text <environment_details> more text")
    assert "<environment_details>" not in result
    assert "<" not in result


def test_sanitize_string_escapes_multiple_angle_brackets():
    result = sanitize_string("<foo> and <bar> and <baz>")
    assert "<" not in result
    assert result.count("&lt;") == 3


def test_sanitize_string_is_idempotent():
    original = "text with <tag> inside"
    once = sanitize_string(original)
    twice = sanitize_string(once)
    assert once == twice


def test_sanitize_string_does_not_alter_clean_string():
    clean = "No angle brackets here, just plain text."
    assert sanitize_string(clean) == clean


def test_sanitize_string_handles_none_without_raising():
    result = sanitize_string(None)
    assert result == ""


def test_sanitize_string_handles_empty_string_without_raising():
    result = sanitize_string("")
    assert result == ""


# ---------------------------------------------------------------------------
# truncate_string
# ---------------------------------------------------------------------------


def test_truncate_string_truncates_long_string_and_appends_suffix():
    long_string = "A" * 250
    result = truncate_string(long_string, max_length=200)
    assert len(result) == 203  # 200 chars + "..."
    assert result.endswith("...")


def test_truncate_string_does_not_alter_short_string():
    short = "Short summary."
    result = truncate_string(short, max_length=200)
    assert result == short


def test_truncate_string_does_not_alter_string_exactly_at_limit():
    exact = "X" * 200
    result = truncate_string(exact, max_length=200)
    assert result == exact
    assert not result.endswith("...")


def test_truncate_string_handles_none_without_raising():
    result = truncate_string(None, max_length=200)
    assert result == ""


def test_truncate_string_handles_empty_string_without_raising():
    result = truncate_string("", max_length=200)
    assert result == ""


def test_truncate_string_uses_custom_suffix():
    long_string = "B" * 300
    result = truncate_string(long_string, max_length=100, suffix=" [truncated]")
    assert result.endswith(" [truncated]")
    assert len(result) == 112  # 100 + len(" [truncated]")