"""
Integration tests for issue linking functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from application.use_cases import (
    CreateIssueLinkUseCase, CreateEpicStoryLinkUseCase, 
    GetIssueLinksUseCase, UpdateIssueUseCase
)
from domain.services import IssueLinkService, IssueUpdateService
from domain.models import IssueLink, LinkType, LinkDirection, IssueUpdate
from domain.exceptions import InvalidLinkTypeError, CircularLinkError


class TestIssueLinkingIntegration:
    """Integration tests for issue linking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock infrastructure dependencies
        self.mock_link_adapter = Mock()
        self.mock_update_adapter = Mock()
        self.mock_config = Mock()
        self.mock_logger = Mock()
        
        # Create domain services
        self.link_service = IssueLinkService(
            link_port=self.mock_link_adapter,
            config_provider=self.mock_config,
            logger=self.mock_logger
        )
        
        self.update_service = IssueUpdateService(
            update_port=self.mock_update_adapter,
            config_provider=self.mock_config,
            logger=self.mock_logger
        )
        
        # Create use cases
        self.create_link_use_case = CreateIssueLinkUseCase(self.link_service)
        self.create_epic_story_use_case = CreateEpicStoryLinkUseCase(self.link_service)
        self.get_links_use_case = GetIssueLinksUseCase(self.link_service)
        self.update_issue_use_case = UpdateIssueUseCase(self.update_service)

    @pytest.mark.asyncio
    async def test_complete_issue_linking_workflow(self):
        """Test complete workflow: create issue, update it, link to epic."""
        # Step 1: Mock issue creation (assume it exists)
        issue_key = "STORY-123"
        epic_key = "EPIC-1"
        
        # Step 2: Update the issue
        self.mock_update_adapter.update_issue = AsyncMock(return_value={
            "success": True,
            "issue_key": issue_key,
            "updated_fields": ["summary", "description"]
        })
        
        update_result = await self.update_issue_use_case.execute(
            issue_key=issue_key,
            summary="Updated story summary",
            description="Updated story description"
        )
        
        assert update_result.success is True
        assert update_result.data["issue_key"] == issue_key
        
        # Step 3: Link the story to an epic
        self.mock_link_adapter.create_epic_story_link = AsyncMock(return_value={
            "success": True,
            "link_id": "12345",
            "source_issue": epic_key,
            "target_issue": issue_key,
            "link_type": "Epic-Story"
        })
        self.mock_link_adapter.validate_epic_story_link = AsyncMock(return_value=True)
        
        link_result = await self.create_epic_story_use_case.execute(
            epic_key=epic_key,
            story_key=issue_key
        )
        
        assert link_result.success is True
        assert link_result.data["source_issue"] == epic_key
        assert link_result.data["target_issue"] == issue_key
        
        # Step 4: Verify the link exists
        self.mock_link_adapter.get_links = AsyncMock(return_value=[
            {
                "source_issue": epic_key,
                "target_issue": issue_key,
                "link_type": "Epic-Story",
                "direction": "outward"
            }
        ])
        
        links_result = await self.get_links_use_case.execute(issue_key)
        
        assert links_result.success is True
        assert len(links_result.data["links"]) == 1
        assert links_result.data["links"][0]["link_type"] == "Epic-Story"

    @pytest.mark.asyncio
    async def test_complex_linking_scenario(self):
        """Test complex linking scenario with multiple link types."""
        # Create a scenario with multiple issues and different link types
        epic_key = "EPIC-1"
        story1_key = "STORY-1"
        story2_key = "STORY-2"
        bug_key = "BUG-1"
        
        # Mock Epic-Story links
        self.mock_link_adapter.create_epic_story_link = AsyncMock(return_value={
            "success": True,
            "link_id": "12345",
            "source_issue": epic_key,
            "target_issue": story1_key,
            "link_type": "Epic-Story"
        })
        self.mock_link_adapter.validate_epic_story_link = AsyncMock(return_value=True)
        
        # Link Story 1 to Epic
        result1 = await self.create_epic_story_use_case.execute(epic_key, story1_key)
        assert result1.success is True
        
        # Mock second Epic-Story link
        self.mock_link_adapter.create_epic_story_link = AsyncMock(return_value={
            "success": True,
            "link_id": "12346",
            "source_issue": epic_key,
            "target_issue": story2_key,
            "link_type": "Epic-Story"
        })
        
        # Link Story 2 to Epic
        result2 = await self.create_epic_story_use_case.execute(epic_key, story2_key)
        assert result2.success is True
        
        # Mock generic link (Bug blocks Story)
        self.mock_link_adapter.create_link = AsyncMock(return_value={
            "success": True,
            "link_id": "12347",
            "source_issue": bug_key,
            "target_issue": story1_key,
            "link_type": "Blocks"
        })
        self.mock_link_adapter.validate_link = AsyncMock(return_value=True)
        
        # Create blocking relationship
        result3 = await self.create_link_use_case.execute(
            source_issue=bug_key,
            target_issue=story1_key,
            link_type="Blocks",
            direction="outward"
        )
        assert result3.success is True
        
        # Verify all links for Story 1
        self.mock_link_adapter.get_links = AsyncMock(return_value=[
            {
                "source_issue": epic_key,
                "target_issue": story1_key,
                "link_type": "Epic-Story",
                "direction": "inward"
            },
            {
                "source_issue": bug_key,
                "target_issue": story1_key,
                "link_type": "Blocks",
                "direction": "inward"
            }
        ])
        
        links_result = await self.get_links_use_case.execute(story1_key)
        assert links_result.success is True
        assert len(links_result.data["links"]) == 2

    @pytest.mark.asyncio
    async def test_error_handling_in_linking_workflow(self):
        """Test error handling throughout the linking workflow."""
        # Test invalid link type
        self.mock_link_adapter.validate_link = AsyncMock(
            side_effect=InvalidLinkTypeError("Invalid link type")
        )
        
        result = await self.create_link_use_case.execute(
            source_issue="PROJ-1",
            target_issue="PROJ-2",
            link_type="InvalidType",
            direction="outward"
        )
        
        assert result.success is False
        assert "Invalid link type" in result.error
        
        # Test circular dependency detection
        self.mock_link_adapter.validate_link = AsyncMock(
            side_effect=CircularLinkError("Circular dependency detected")
        )
        
        result = await self.create_link_use_case.execute(
            source_issue="PROJ-1",
            target_issue="PROJ-1",  # Self-link
            link_type="Blocks",
            direction="outward"
        )
        
        assert result.success is False
        assert "Circular dependency" in result.error

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent linking and updating operations."""
        import asyncio
        
        issue_key = "PROJ-123"
        
        # Mock concurrent operations
        self.mock_update_adapter.update_issue = AsyncMock(return_value={
            "success": True,
            "issue_key": issue_key,
            "updated_fields": ["summary"]
        })
        
        self.mock_link_adapter.create_link = AsyncMock(return_value={
            "success": True,
            "link_id": "12345",
            "source_issue": issue_key,
            "target_issue": "PROJ-456",
            "link_type": "Relates"
        })
        self.mock_link_adapter.validate_link = AsyncMock(return_value=True)
        
        # Execute operations concurrently
        update_task = self.update_issue_use_case.execute(
            issue_key=issue_key,
            summary="Updated summary"
        )
        
        link_task = self.create_link_use_case.execute(
            source_issue=issue_key,
            target_issue="PROJ-456",
            link_type="Relates",
            direction="outward"
        )
        
        update_result, link_result = await asyncio.gather(update_task, link_task)
        
        assert update_result.success is True
        assert link_result.success is True

    @pytest.mark.asyncio
    async def test_link_validation_with_real_scenarios(self):
        """Test link validation with realistic scenarios."""
        # Test Epic-Story validation
        self.mock_link_adapter.validate_epic_story_link = AsyncMock(return_value=True)
        self.mock_link_adapter.create_epic_story_link = AsyncMock(return_value={
            "success": True,
            "link_id": "12345",
            "source_issue": "EPIC-1",
            "target_issue": "STORY-1",
            "link_type": "Epic-Story"
        })
        
        # Valid Epic-Story link
        result = await self.create_epic_story_use_case.execute("EPIC-1", "STORY-1")
        assert result.success is True
        
        # Test invalid Epic-Story link (wrong issue types)
        from domain.exceptions import EpicLinkError
        self.mock_link_adapter.validate_epic_story_link = AsyncMock(
            side_effect=EpicLinkError("Source must be Epic, target must be Story")
        )
        
        result = await self.create_epic_story_use_case.execute("STORY-1", "EPIC-1")
        assert result.success is False
        assert "Epic" in result.error

    @pytest.mark.asyncio
    async def test_performance_with_many_links(self):
        """Test performance with many links."""
        issue_key = "PROJ-123"
        
        # Mock many links
        many_links = []
        for i in range(100):
            many_links.append({
                "source_issue": f"PROJ-{i}",
                "target_issue": issue_key,
                "link_type": "Relates",
                "direction": "inward"
            })
        
        self.mock_link_adapter.get_links = AsyncMock(return_value=many_links)
        
        import time
        start_time = time.time()
        
        result = await self.get_links_use_case.execute(issue_key)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.success is True
        assert len(result.data["links"]) == 100
        assert execution_time < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_transaction_rollback_simulation(self):
        """Test transaction rollback behavior."""
        # Simulate a scenario where link creation fails after issue update succeeds
        issue_key = "PROJ-123"
        
        # Mock successful update
        self.mock_update_adapter.update_issue = AsyncMock(return_value={
            "success": True,
            "issue_key": issue_key,
            "updated_fields": ["summary"]
        })
        
        # Mock failed link creation
        self.mock_link_adapter.validate_link = AsyncMock(return_value=True)
        self.mock_link_adapter.create_link = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        # Execute update successfully
        update_result = await self.update_issue_use_case.execute(
            issue_key=issue_key,
            summary="Updated summary"
        )
        assert update_result.success is True
        
        # Execute link creation (should fail)
        link_result = await self.create_link_use_case.execute(
            source_issue=issue_key,
            target_issue="PROJ-456",
            link_type="Relates",
            direction="outward"
        )
        assert link_result.success is False
        
        # In a real scenario, we might need to implement compensation logic
        # to rollback the update if the link creation fails

    @pytest.mark.asyncio
    async def test_link_type_compatibility_matrix(self):
        """Test link type compatibility across different issue types."""
        compatibility_tests = [
            # (source_type, target_type, link_type, should_succeed)
            ("Epic", "Story", "Epic-Story", True),
            ("Story", "Epic", "Epic-Story", False),  # Wrong direction
            ("Story", "Task", "Parent-Child", True),
            ("Bug", "Story", "Blocks", True),
            ("Story", "Story", "Relates", True),
            ("Epic", "Bug", "Epic-Story", False),  # Epic should only link to Stories
        ]
        
        for source_type, target_type, link_type, should_succeed in compatibility_tests:
            source_key = f"{source_type.upper()}-1"
            target_key = f"{target_type.upper()}-1"
            
            if should_succeed:
                self.mock_link_adapter.validate_link = AsyncMock(return_value=True)
                self.mock_link_adapter.create_link = AsyncMock(return_value={
                    "success": True,
                    "link_id": "12345",
                    "source_issue": source_key,
                    "target_issue": target_key,
                    "link_type": link_type
                })
            else:
                self.mock_link_adapter.validate_link = AsyncMock(
                    side_effect=InvalidLinkTypeError(f"Invalid link: {source_type} -> {target_type}")
                )
            
            result = await self.create_link_use_case.execute(
                source_issue=source_key,
                target_issue=target_key,
                link_type=link_type,
                direction="outward"
            )
            
            if should_succeed:
                assert result.success is True, f"Expected success for {source_type} -> {target_type} ({link_type})"
            else:
                assert result.success is False, f"Expected failure for {source_type} -> {target_type} ({link_type})"

    @pytest.mark.asyncio
    async def test_bulk_operations(self):
        """Test bulk linking operations."""
        epic_key = "EPIC-1"
        story_keys = ["STORY-1", "STORY-2", "STORY-3", "STORY-4", "STORY-5"]
        
        # Mock successful bulk Epic-Story linking
        self.mock_link_adapter.validate_epic_story_link = AsyncMock(return_value=True)
        
        results = []
        for i, story_key in enumerate(story_keys):
            self.mock_link_adapter.create_epic_story_link = AsyncMock(return_value={
                "success": True,
                "link_id": f"1234{i}",
                "source_issue": epic_key,
                "target_issue": story_key,
                "link_type": "Epic-Story"
            })
            
            result = await self.create_epic_story_use_case.execute(epic_key, story_key)
            results.append(result)
        
        # Verify all links were created successfully
        assert all(result.success for result in results)
        assert len(results) == 5
        
        # Verify all stories are linked to the epic
        for i, result in enumerate(results):
            assert result.data["source_issue"] == epic_key
            assert result.data["target_issue"] == story_keys[i]
