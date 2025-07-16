"""
Tests for IssueUpdate domain model.
"""

import pytest

from domain.exceptions import IssueFieldUpdateError
from domain.models import IssueUpdate, IssueUpdateResult


class TestIssueUpdate:
    """Test cases for IssueUpdate model."""

    def test_create_valid_issue_update(self):
        """Test creating a valid issue update."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={
                "summary": "Updated summary",
                "description": "Updated description",
                "priority": "High"
            }
        )

        assert update.issue_key == "PROJ-123"
        assert update.fields["summary"] == "Updated summary"
        assert update.fields["description"] == "Updated description"
        assert update.fields["priority"] == "High"

    def test_create_update_with_single_field(self):
        """Test creating update with single field."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"summary": "New summary"}
        )

        assert len(update.fields) == 1
        assert update.fields["summary"] == "New summary"

    def test_invalid_issue_key_format(self):
        """Test validation of issue key format."""
        with pytest.raises(ValueError):
            IssueUpdate(
                issue_key="invalid-key",
                fields={"summary": "Test"}
            )

    def test_empty_fields_validation(self):
        """Test that empty fields are rejected."""
        with pytest.raises(ValueError):
            IssueUpdate(
                issue_key="PROJ-123",
                fields={}
            )

    def test_validate_updatable_fields(self):
        """Test validation of updatable fields."""
        # Valid fields
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={
                "summary": "Test",
                "description": "Test description",
                "priority": "High",
                "assignee": "user@example.com",
                "labels": ["bug", "urgent"]
            }
        )

        assert update.validate_fields()

    def test_invalid_field_names(self):
        """Test rejection of invalid field names."""
        with pytest.raises(IssueFieldUpdateError):
            IssueUpdate(
                issue_key="PROJ-123",
                fields={"invalid_field": "value"}
            )

    def test_field_value_validation(self):
        """Test validation of field values."""
        # Valid string field
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"summary": "Valid summary"}
        )
        assert update.validate_field_value("summary", "Valid summary")

        # Invalid empty summary
        with pytest.raises(IssueFieldUpdateError):
            IssueUpdate(
                issue_key="PROJ-123",
                fields={"summary": ""}
            )

    def test_labels_field_validation(self):
        """Test validation of labels field."""
        # Valid labels
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"labels": ["bug", "feature", "urgent"]}
        )
        assert update.validate_field_value("labels", ["bug", "feature", "urgent"])

        # Invalid labels (not a list)
        with pytest.raises(IssueFieldUpdateError):
            IssueUpdate(
                issue_key="PROJ-123",
                fields={"labels": "not-a-list"}
            )

    def test_priority_field_validation(self):
        """Test validation of priority field."""
        valid_priorities = ["Highest", "High", "Medium", "Low", "Lowest"]

        for priority in valid_priorities:
            update = IssueUpdate(
                issue_key="PROJ-123",
                fields={"priority": priority}
            )
            assert update.validate_field_value("priority", priority)

        # Invalid priority
        with pytest.raises(IssueFieldUpdateError):
            IssueUpdate(
                issue_key="PROJ-123",
                fields={"priority": "Invalid"}
            )

    def test_assignee_field_validation(self):
        """Test validation of assignee field."""
        # Valid assignee
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"assignee": "user@example.com"}
        )
        assert update.validate_field_value("assignee", "user@example.com")

        # Unassign (None or empty string)
        update_unassign = IssueUpdate(
            issue_key="PROJ-123",
            fields={"assignee": None}
        )
        assert update_unassign.validate_field_value("assignee", None)

    def test_to_dict(self):
        """Test converting update to dictionary."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={
                "summary": "Test summary",
                "priority": "High"
            }
        )

        update_dict = update.to_dict()

        expected = {
            "issue_key": "PROJ-123",
            "fields": {
                "summary": "Test summary",
                "priority": "High"
            }
        }

        assert update_dict == expected

    def test_from_dict(self):
        """Test creating update from dictionary."""
        update_dict = {
            "issue_key": "PROJ-123",
            "fields": {
                "summary": "Test summary",
                "priority": "High"
            }
        }

        update = IssueUpdate.from_dict(update_dict)

        assert update.issue_key == "PROJ-123"
        assert update.fields["summary"] == "Test summary"
        assert update.fields["priority"] == "High"

    def test_get_changed_fields(self):
        """Test getting list of changed fields."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={
                "summary": "New summary",
                "description": "New description",
                "priority": "High"
            }
        )

        changed_fields = update.get_changed_fields()
        expected_fields = ["summary", "description", "priority"]

        assert set(changed_fields) == set(expected_fields)

    def test_has_field(self):
        """Test checking if update has specific field."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"summary": "Test", "priority": "High"}
        )

        assert update.has_field("summary")
        assert update.has_field("priority")
        assert not update.has_field("description")

    def test_get_field_value(self):
        """Test getting field value."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"summary": "Test summary"}
        )

        assert update.get_field_value("summary") == "Test summary"
        assert update.get_field_value("nonexistent") is None

    def test_add_field(self):
        """Test adding field to update."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"summary": "Test"}
        )

        update.add_field("priority", "High")

        assert update.has_field("priority")
        assert update.get_field_value("priority") == "High"

    def test_remove_field(self):
        """Test removing field from update."""
        update = IssueUpdate(
            issue_key="PROJ-123",
            fields={"summary": "Test", "priority": "High"}
        )

        update.remove_field("priority")

        assert not update.has_field("priority")
        assert update.has_field("summary")


class TestIssueUpdateResult:
    """Test cases for IssueUpdateResult model."""

    def test_create_successful_result(self):
        """Test creating successful update result."""
        result = IssueUpdateResult(
            success=True,
            issue_key="PROJ-123",
            updated_fields=["summary", "priority"],
            message="Issue updated successfully"
        )

        assert result.success is True
        assert result.issue_key == "PROJ-123"
        assert result.updated_fields == ["summary", "priority"]
        assert result.message == "Issue updated successfully"

    def test_create_failed_result(self):
        """Test creating failed update result."""
        result = IssueUpdateResult(
            success=False,
            issue_key="PROJ-123",
            error="Permission denied",
            failed_fields=["assignee"]
        )

        assert result.success is False
        assert result.issue_key == "PROJ-123"
        assert result.error == "Permission denied"
        assert result.failed_fields == ["assignee"]

    def test_result_with_warnings(self):
        """Test result with warnings."""
        result = IssueUpdateResult(
            success=True,
            issue_key="PROJ-123",
            updated_fields=["summary"],
            warnings=["Priority field was ignored due to workflow restrictions"]
        )

        assert result.success is True
        assert len(result.warnings) == 1
        assert "Priority field was ignored" in result.warnings[0]

    def test_partial_success_result(self):
        """Test partial success result."""
        result = IssueUpdateResult(
            success=True,
            issue_key="PROJ-123",
            updated_fields=["summary", "description"],
            failed_fields=["assignee"],
            warnings=["Could not update assignee: user not found"]
        )

        assert result.success is True
        assert len(result.updated_fields) == 2
        assert len(result.failed_fields) == 1
        assert len(result.warnings) == 1

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = IssueUpdateResult(
            success=True,
            issue_key="PROJ-123",
            updated_fields=["summary"],
            message="Success"
        )

        result_dict = result.to_dict()

        expected = {
            "success": True,
            "issue_key": "PROJ-123",
            "updated_fields": ["summary"],
            "failed_fields": [],
            "message": "Success",
            "error": None,
            "warnings": []
        }

        assert result_dict == expected

    def test_result_from_dict(self):
        """Test creating result from dictionary."""
        result_dict = {
            "success": True,
            "issue_key": "PROJ-123",
            "updated_fields": ["summary"],
            "message": "Success"
        }

        result = IssueUpdateResult.from_dict(result_dict)

        assert result.success is True
        assert result.issue_key == "PROJ-123"
        assert result.updated_fields == ["summary"]
        assert result.message == "Success"

    def test_has_warnings(self):
        """Test checking if result has warnings."""
        result_with_warnings = IssueUpdateResult(
            success=True,
            issue_key="PROJ-123",
            warnings=["Warning message"]
        )

        result_without_warnings = IssueUpdateResult(
            success=True,
            issue_key="PROJ-123"
        )

        assert result_with_warnings.has_warnings()
        assert not result_without_warnings.has_warnings()

    def test_has_failures(self):
        """Test checking if result has failures."""
        result_with_failures = IssueUpdateResult(
            success=False,
            issue_key="PROJ-123",
            failed_fields=["assignee"]
        )

        result_without_failures = IssueUpdateResult(
            success=True,
            issue_key="PROJ-123"
        )

        assert result_with_failures.has_failures()
        assert not result_without_failures.has_failures()
