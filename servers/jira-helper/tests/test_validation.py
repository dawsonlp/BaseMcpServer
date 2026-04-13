"""Tests for pure validation functions — no mocks needed."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from exceptions import JiraValidationError
from jira_client import validate_issue_key
from tools.search import validate_jql_query
import pytest


class TestValidateIssueKey:
    def test_valid_key(self):
        assert validate_issue_key("PROJ-123") == "PROJ-123"

    def test_valid_key_lowercase_normalized(self):
        assert validate_issue_key("proj-123") == "PROJ-123"

    def test_valid_key_with_whitespace(self):
        assert validate_issue_key("  PROJ-456  ") == "PROJ-456"

    def test_empty_key_raises(self):
        with pytest.raises(JiraValidationError):
            validate_issue_key("")

    def test_none_key_raises(self):
        with pytest.raises(JiraValidationError):
            validate_issue_key(None)

    def test_invalid_format_raises(self):
        with pytest.raises(JiraValidationError):
            validate_issue_key("not-a-key")

    def test_numbers_only_raises(self):
        with pytest.raises(JiraValidationError):
            validate_issue_key("12345")

    def test_no_dash_raises(self):
        with pytest.raises(JiraValidationError):
            validate_issue_key("PROJ123")


class TestValidateJqlQuery:
    def test_valid_jql(self):
        result = validate_jql_query(jql='project = "TEST"')
        assert result["valid"] is True

    def test_empty_jql(self):
        result = validate_jql_query(jql="")
        assert result["valid"] is False

    def test_none_jql(self):
        result = validate_jql_query(jql=None)
        assert result["valid"] is False

    def test_sql_injection_drop(self):
        result = validate_jql_query(jql="DROP TABLE issues")
        assert result["valid"] is False
        assert any("forbidden" in i.lower() for i in result["issues"])

    def test_sql_injection_delete(self):
        result = validate_jql_query(jql='DELETE FROM issues WHERE 1=1')
        assert result["valid"] is False

    def test_long_jql(self):
        result = validate_jql_query(jql="x" * 5000)
        assert result["valid"] is False
        assert any("length" in i.lower() for i in result["issues"])