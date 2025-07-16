"""
Tests for IssueLinkService domain service.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from domain.exceptions import (
    CircularLinkError,
    EpicLinkError,
    InvalidLinkTypeError,
    IssueLinkError,
    LinkNotFoundError,
)
from domain.models import IssueLink, IssueLinkResult, LinkDirection, LinkType
from domain.services import IssueLinkService


class TestIssueLinkService:
    """Test cases for IssueLinkService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_link_port = Mock()
        self.mock_config = Mock()
        self.mock_logger = Mock()

        self.service = IssueLinkService(
            link_port=self.mock_link_port,
            config_provider=self.mock_config,
            logger=self.mock_logger
        )

    @pytest.mark.asyncio
    async def test_create_valid_link(self):
        """Test creating a valid issue link."""
        # Arrange
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS,
            direction=LinkDirection.OUTWARD
        )

        expected_result = IssueLinkResult(
            success=True,
            link_id="12345",
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type="Blocks"
        )

        self.mock_link_port.create_link = AsyncMock(return_value=expected_result)
        self.mock_link_port.validate_link = AsyncMock(return_value=True)

        # Act
        result = await self.service.create_link(link)

        # Assert
        assert result.success is True
        assert result.source_issue == "PROJ-123"
        assert result.target_issue == "PROJ-456"
        self.mock_link_port.validate_link.assert_called_once_with(link)
        self.mock_link_port.create_link.assert_called_once_with(link)

    @pytest.mark.asyncio
    async def test_prevent_self_linking(self):
        """Test that self-linking is prevented."""
        # Arrange
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-123",
            link_type=LinkType.BLOCKS,
            direction=LinkDirection.OUTWARD
        )

        # Act & Assert
        with pytest.raises(CircularLinkError):
            await self.service.create_link(link)

    @pytest.mark.asyncio
    async def test_validate_link_type(self):
        """Test link type validation."""
        # Arrange
        valid_link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.RELATES,
            direction=LinkDirection.OUTWARD
        )

        self.mock_link_port.validate_link = AsyncMock(return_value=True)
        self.mock_link_port.create_link = AsyncMock(return_value=IssueLinkResult(success=True))

        # Act
        result = await self.service.create_link(valid_link)

        # Assert
        assert result.success is True
        self.mock_link_port.validate_link.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_link_type_rejection(self):
        """Test rejection of invalid link types."""
        # Arrange
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS,
            direction=LinkDirection.OUTWARD
        )

        self.mock_link_port.validate_link = AsyncMock(side_effect=InvalidLinkTypeError("Invalid link type"))

        # Act & Assert
        with pytest.raises(InvalidLinkTypeError):
            await self.service.create_link(link)

    @pytest.mark.asyncio
    async def test_create_epic_story_link(self):
        """Test creating Epic-Story link."""
        # Arrange
        epic_key = "EPIC-1"
        story_key = "STORY-1"

        expected_result = IssueLinkResult(
            success=True,
            link_id="12345",
            source_issue=epic_key,
            target_issue=story_key,
            link_type="Epic-Story"
        )

        self.mock_link_port.create_epic_story_link = AsyncMock(return_value=expected_result)
        self.mock_link_port.validate_epic_story_link = AsyncMock(return_value=True)

        # Act
        result = await self.service.create_epic_story_link(epic_key, story_key)

        # Assert
        assert result.success is True
        assert result.source_issue == epic_key
        assert result.target_issue == story_key
        assert result.link_type == "Epic-Story"
        self.mock_link_port.validate_epic_story_link.assert_called_once_with(epic_key, story_key)
        self.mock_link_port.create_epic_story_link.assert_called_once_with(epic_key, story_key)

    @pytest.mark.asyncio
    async def test_epic_story_link_validation_failure(self):
        """Test Epic-Story link validation failure."""
        # Arrange
        epic_key = "STORY-1"  # Wrong issue type
        story_key = "STORY-2"

        self.mock_link_port.validate_epic_story_link = AsyncMock(
            side_effect=EpicLinkError("Source issue must be an Epic")
        )

        # Act & Assert
        with pytest.raises(EpicLinkError):
            await self.service.create_epic_story_link(epic_key, story_key)

    @pytest.mark.asyncio
    async def test_get_issue_links(self):
        """Test getting all links for an issue."""
        # Arrange
        issue_key = "PROJ-123"
        expected_links = [
            IssueLink(
                source_issue="PROJ-123",
                target_issue="PROJ-456",
                link_type=LinkType.BLOCKS,
                direction=LinkDirection.OUTWARD
            ),
            IssueLink(
                source_issue="PROJ-789",
                target_issue="PROJ-123",
                link_type=LinkType.RELATES,
                direction=LinkDirection.INWARD
            )
        ]

        self.mock_link_port.get_links = AsyncMock(return_value=expected_links)

        # Act
        links = await self.service.get_issue_links(issue_key)

        # Assert
        assert len(links) == 2
        assert links[0].source_issue == "PROJ-123"
        assert links[1].target_issue == "PROJ-123"
        self.mock_link_port.get_links.assert_called_once_with(issue_key)

    @pytest.mark.asyncio
    async def test_get_links_for_nonexistent_issue(self):
        """Test getting links for non-existent issue."""
        # Arrange
        issue_key = "NONEXISTENT-123"
        self.mock_link_port.get_links = AsyncMock(side_effect=LinkNotFoundError("Issue not found"))

        # Act & Assert
        with pytest.raises(LinkNotFoundError):
            await self.service.get_issue_links(issue_key)

    @pytest.mark.asyncio
    async def test_remove_link(self):
        """Test removing an issue link."""
        # Arrange
        link_id = "12345"
        self.mock_link_port.remove_link = AsyncMock(return_value=True)

        # Act
        result = await self.service.remove_link(link_id)

        # Assert
        assert result is True
        self.mock_link_port.remove_link.assert_called_once_with(link_id)

    @pytest.mark.asyncio
    async def test_remove_nonexistent_link(self):
        """Test removing non-existent link."""
        # Arrange
        link_id = "nonexistent"
        self.mock_link_port.remove_link = AsyncMock(return_value=False)

        # Act
        result = await self.service.remove_link(link_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_get_available_link_types(self):
        """Test getting available link types."""
        # Arrange
        expected_types = ["Blocks", "Relates", "Epic-Story", "Parent-Child"]
        self.mock_link_port.get_available_link_types = AsyncMock(return_value=expected_types)

        # Act
        link_types = await self.service.get_available_link_types()

        # Assert
        assert link_types == expected_types
        self.mock_link_port.get_available_link_types.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_bidirectional_relationship(self):
        """Test validation of bidirectional relationships."""
        # Arrange
        outward_link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS,
            direction=LinkDirection.OUTWARD
        )

        # Mock that the reverse link doesn't exist
        self.mock_link_port.get_links = AsyncMock(return_value=[])
        self.mock_link_port.validate_link = AsyncMock(return_value=True)
        self.mock_link_port.create_link = AsyncMock(return_value=IssueLinkResult(success=True))

        # Act
        result = await self.service.create_link(outward_link)

        # Assert
        assert result.success is True

    @pytest.mark.asyncio
    async def test_prevent_duplicate_links(self):
        """Test prevention of duplicate links."""
        # Arrange
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS,
            direction=LinkDirection.OUTWARD
        )

        # Mock that the link already exists
        existing_links = [link]
        self.mock_link_port.get_links = AsyncMock(return_value=existing_links)

        # Act & Assert
        with pytest.raises(IssueLinkError, match="Link already exists"):
            await self.service.create_link(link)

    @pytest.mark.asyncio
    async def test_create_parent_child_link(self):
        """Test creating Parent-Child link."""
        # Arrange
        parent_key = "PARENT-1"
        child_key = "CHILD-1"

        expected_result = IssueLinkResult(
            success=True,
            link_id="12345",
            source_issue=parent_key,
            target_issue=child_key,
            link_type="Parent-Child"
        )

        self.mock_link_port.create_parent_child_link = AsyncMock(return_value=expected_result)
        self.mock_link_port.validate_parent_child_link = AsyncMock(return_value=True)

        # Act
        result = await self.service.create_parent_child_link(parent_key, child_key)

        # Assert
        assert result.success is True
        assert result.source_issue == parent_key
        assert result.target_issue == child_key
        assert result.link_type == "Parent-Child"

    @pytest.mark.asyncio
    async def test_detect_circular_dependencies(self):
        """Test detection of circular dependencies."""
        # Arrange
        # Create a scenario where A -> B -> C -> A would create a cycle
        link = IssueLink(
            source_issue="PROJ-A",
            target_issue="PROJ-C",  # This would complete the cycle
            link_type=LinkType.BLOCKS,
            direction=LinkDirection.OUTWARD
        )

        # Mock existing links that would create a cycle
        existing_links = [
            IssueLink("PROJ-A", "PROJ-B", LinkType.BLOCKS, LinkDirection.OUTWARD),
            IssueLink("PROJ-B", "PROJ-C", LinkType.BLOCKS, LinkDirection.OUTWARD)
        ]

        self.mock_link_port.get_links = AsyncMock(return_value=existing_links)

        # Act & Assert
        with pytest.raises(CircularLinkError):
            await self.service.create_link(link)

    @pytest.mark.asyncio
    async def test_link_type_compatibility(self):
        """Test link type compatibility validation."""
        # Arrange
        link = IssueLink(
            source_issue="EPIC-1",
            target_issue="TASK-1",  # Epic should link to Story, not Task
            link_type=LinkType.EPIC_STORY,
            direction=LinkDirection.OUTWARD
        )

        self.mock_link_port.validate_link = AsyncMock(
            side_effect=InvalidLinkTypeError("Epic can only link to Story issues")
        )

        # Act & Assert
        with pytest.raises(InvalidLinkTypeError):
            await self.service.create_link(link)

    @pytest.mark.asyncio
    async def test_get_outward_links(self):
        """Test getting only outward links for an issue."""
        # Arrange
        issue_key = "PROJ-123"
        all_links = [
            IssueLink("PROJ-123", "PROJ-456", LinkType.BLOCKS, LinkDirection.OUTWARD),
            IssueLink("PROJ-789", "PROJ-123", LinkType.RELATES, LinkDirection.INWARD)
        ]

        self.mock_link_port.get_links = AsyncMock(return_value=all_links)

        # Act
        outward_links = await self.service.get_outward_links(issue_key)

        # Assert
        assert len(outward_links) == 1
        assert outward_links[0].direction == LinkDirection.OUTWARD
        assert outward_links[0].source_issue == issue_key

    @pytest.mark.asyncio
    async def test_get_inward_links(self):
        """Test getting only inward links for an issue."""
        # Arrange
        issue_key = "PROJ-123"
        all_links = [
            IssueLink("PROJ-123", "PROJ-456", LinkType.BLOCKS, LinkDirection.OUTWARD),
            IssueLink("PROJ-789", "PROJ-123", LinkType.RELATES, LinkDirection.INWARD)
        ]

        self.mock_link_port.get_links = AsyncMock(return_value=all_links)

        # Act
        inward_links = await self.service.get_inward_links(issue_key)

        # Assert
        assert len(inward_links) == 1
        assert inward_links[0].direction == LinkDirection.INWARD
        assert inward_links[0].target_issue == issue_key

    @pytest.mark.asyncio
    async def test_get_links_by_type(self):
        """Test getting links filtered by type."""
        # Arrange
        issue_key = "PROJ-123"
        all_links = [
            IssueLink("PROJ-123", "PROJ-456", LinkType.BLOCKS, LinkDirection.OUTWARD),
            IssueLink("PROJ-123", "PROJ-789", LinkType.RELATES, LinkDirection.OUTWARD)
        ]

        self.mock_link_port.get_links = AsyncMock(return_value=all_links)

        # Act
        blocks_links = await self.service.get_links_by_type(issue_key, LinkType.BLOCKS)

        # Assert
        assert len(blocks_links) == 1
        assert blocks_links[0].link_type == LinkType.BLOCKS

    @pytest.mark.asyncio
    async def test_error_handling_and_logging(self):
        """Test error handling and logging."""
        # Arrange
        link = IssueLink(
            source_issue="PROJ-123",
            target_issue="PROJ-456",
            link_type=LinkType.BLOCKS,
            direction=LinkDirection.OUTWARD
        )

        self.mock_link_port.validate_link = AsyncMock(return_value=True)
        self.mock_link_port.create_link = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        # Act & Assert
        with pytest.raises(IssueLinkError):
            await self.service.create_link(link)

        # Verify logging
        self.mock_logger.error.assert_called()
