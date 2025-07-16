"""
Tests for IssueLink domain model.
"""

import pytest

from domain.models import IssueLink, LinkDirection, LinkType


class TestIssueLink:
    """Test cases for IssueLink model."""

    def test_create_valid_issue_link(self):
        """Test creating a valid issue link."""
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS.value,
            direction=LinkDirection.OUTWARD.value
        )

        assert link.source_issue == "PROJ-123"
        assert link.target_issue == "PROJ-456"
        assert link.link_type == LinkType.BLOCKS.value
        assert link.direction == LinkDirection.OUTWARD.value

    def test_create_epic_story_link(self):
        """Test creating an Epic-Story link."""
        link = IssueLink(
            source_issue="EPIC-1",
            target_issue="STORY-1",
            link_type=LinkType.EPIC_STORY.value,
            direction=LinkDirection.OUTWARD.value
        )

        assert link.link_type == LinkType.EPIC_STORY.value
        assert link.is_epic_link()

    def test_create_parent_child_link(self):
        """Test creating a Parent-Child link."""
        link = IssueLink(
            source_issue="PARENT-1",
            target_issue="CHILD-1",
            link_type=LinkType.PARENT_CHILD.value,
            direction=LinkDirection.OUTWARD.value
        )

        assert link.link_type == LinkType.PARENT_CHILD.value
        assert link.is_parent_child_link()

    def test_prevent_self_linking(self):
        """Test that self-linking is prevented."""
        with pytest.raises(ValueError, match="Cannot link an issue to itself"):
            IssueLink(
                source_issue="PROJ-123",
                target_issue="PROJ-123",
                link_type=LinkType.BLOCKS.value,
                direction=LinkDirection.OUTWARD.value
            )

    def test_invalid_issue_key_format(self):
        """Test validation of issue key format."""
        with pytest.raises(ValueError):
            IssueLink(
                source_issue="invalid-key",
                target_issue="PROJ-456",
                link_type=LinkType.BLOCKS,
                direction=LinkDirection.OUTWARD
            )

    def test_link_equality(self):
        """Test link equality comparison."""
        link1 = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS.value,
            direction=LinkDirection.OUTWARD.value
        )

        link2 = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS.value,
            direction=LinkDirection.OUTWARD.value
        )

        assert link1 == link2

    def test_link_inequality(self):
        """Test link inequality comparison."""
        link1 = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS.value,
            direction=LinkDirection.OUTWARD.value
        )

        link2 = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-789",
            link_type=LinkType.BLOCKS.value,
            direction=LinkDirection.OUTWARD.value
        )

        assert link1 != link2

    def test_reverse_direction(self):
        """Test getting reverse direction."""
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS.value,
            direction=LinkDirection.OUTWARD.value
        )

        reverse_direction = link.get_reverse_direction()
        assert reverse_direction == LinkDirection.INWARD.value

    def test_link_validation(self):
        """Test link validation."""
        # Valid link type
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.RELATES.value,
            direction=LinkDirection.OUTWARD.value
        )
        # Should not raise any exceptions
        assert link.source_issue == "PROJ-123"

    def test_invalid_direction(self):
        """Test invalid direction validation."""
        with pytest.raises(ValueError, match="Invalid link direction"):
            IssueLink(
                source_issue="PROJ-123",
                target_issue="PROJ-456",
                link_type=LinkType.BLOCKS.value,
                direction="invalid_direction"
            )

    def test_empty_fields_validation(self):
        """Test validation of empty fields."""
        # Empty link type
        with pytest.raises(ValueError, match="Link type cannot be empty"):
            IssueLink(
                source_issue="PROJ-123",
                target_issue="PROJ-456",
                link_type="",
                direction=LinkDirection.OUTWARD.value
            )

        # Empty source issue
        with pytest.raises(ValueError, match="Source issue cannot be empty"):
            IssueLink(
                source_issue="",
                target_issue="PROJ-456",
                link_type=LinkType.BLOCKS.value,
                direction=LinkDirection.OUTWARD.value
            )

        # Empty target issue
        with pytest.raises(ValueError, match="Target issue cannot be empty"):
            IssueLink(
                source_issue="PROJ-123",
                target_issue="",
                link_type=LinkType.BLOCKS.value,
                direction=LinkDirection.OUTWARD.value
            )


class TestLinkType:
    """Test cases for LinkType enum."""

    def test_all_link_types_defined(self):
        """Test that all expected link types are defined."""
        expected_types = [
            "BLOCKS", "RELATES", "EPIC_STORY", "PARENT_CHILD",
            "DUPLICATES", "CLONES", "CUSTOM"
        ]

        for link_type in expected_types:
            assert hasattr(LinkType, link_type)

    def test_link_type_string_values(self):
        """Test link type string representations."""
        assert LinkType.BLOCKS.value == "Blocks"
        assert LinkType.RELATES.value == "Relates"
        assert LinkType.EPIC_STORY.value == "Epic-Story"
        assert LinkType.PARENT_CHILD.value == "Parent-Child"
        assert LinkType.DUPLICATES.value == "Duplicates"
        assert LinkType.CLONES.value == "Clones"
        assert LinkType.CUSTOM.value == "Custom"

    def test_link_type_enum_access(self):
        """Test accessing link types through enum."""
        # Test that we can access all defined link types
        link_types = [
            LinkType.BLOCKS,
            LinkType.RELATES,
            LinkType.EPIC_STORY,
            LinkType.PARENT_CHILD,
            LinkType.DUPLICATES,
            LinkType.CLONES,
            LinkType.CUSTOM
        ]

        for link_type in link_types:
            assert isinstance(link_type.value, str)
            assert len(link_type.value) > 0


class TestLinkDirection:
    """Test cases for LinkDirection enum."""

    def test_direction_values(self):
        """Test direction enum values."""
        assert LinkDirection.OUTWARD.value == "outward"
        assert LinkDirection.INWARD.value == "inward"

    def test_direction_enum_access(self):
        """Test accessing directions through enum."""
        directions = [LinkDirection.OUTWARD, LinkDirection.INWARD]

        for direction in directions:
            assert isinstance(direction.value, str)
            assert direction.value in ["outward", "inward"]

    def test_direction_validation(self):
        """Test direction validation in IssueLink."""
        # Valid directions should work
        valid_directions = [LinkDirection.OUTWARD.value, LinkDirection.INWARD.value]

        for direction in valid_directions:
            link = IssueLink(
                source_issue="PROJ-123",
                target_issue="PROJ-456",
                link_type=LinkType.BLOCKS.value,
                direction=direction
            )
            assert link.direction == direction
