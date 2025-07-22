"""
Integration tests for the atlassian_api_adapter.
"""

import pytest
from infrastructure.atlassian_api_adapter import (
    AtlassianApiJiraClientFactory,
    AtlassianApiRepository,
)
from domain.models import CommentAddRequest, IssueCreateRequest, JiraIssue
from config import Settings


@pytest.fixture(scope="module")
def config_provider():
    """Fixture for the configuration provider."""
    return Settings()


@pytest.fixture(scope="module")
def atlassian_api_repository(config_provider):
    """Fixture for AtlassianApiRepository."""
    client_factory = AtlassianApiJiraClientFactory(config_provider)
    return AtlassianApiRepository(client_factory, config_provider)


@pytest.mark.asyncio
async def test_create_and_get_issue(atlassian_api_repository):
    """
    Test creating an issue and then retrieving it.
    This test also implicitly tests the get_issue method.
    """
    create_request = IssueCreateRequest(
        project_key="ATP",
        summary="Live Test Issue",
        description="This is a live test issue.",
        issue_type="Task",
    )

    created_issue = None
    try:
        created_issue = await atlassian_api_repository.create_issue(create_request, "personal")
        assert created_issue is not None
        assert created_issue.summary == "Live Test Issue"
        assert created_issue.issue_type == "Task"

        # Now, get the issue and verify its details
        retrieved_issue = await atlassian_api_repository.get_issue(created_issue.key, "personal")
        assert retrieved_issue is not None
        assert retrieved_issue.key == created_issue.key
        assert retrieved_issue.summary == "Live Test Issue"

    finally:
        if created_issue:
            # Clean up the created issue
            client = atlassian_api_repository._client_factory.create_client("personal")
            client.delete_issue(created_issue.key)


@pytest.mark.asyncio
async def test_get_projects(atlassian_api_repository):
    """Test retrieving all projects."""
    projects = await atlassian_api_repository.get_projects("personal")
    assert projects is not None
    assert len(projects) > 0
    # Check if the ATP project is in the list
    assert any(p.key == "ATP" for p in projects)


@pytest.mark.asyncio
async def test_add_and_get_comment(atlassian_api_repository):
    """
    Test adding a comment to an issue and then retrieving it.
    This test also implicitly tests the get_issue_with_comments method.
    """
    create_request = IssueCreateRequest(
        project_key="ATP",
        summary="Comment Test Issue",
        description="This is an issue for testing comments.",
        issue_type="Task",
    )

    created_issue = None
    try:
        created_issue = await atlassian_api_repository.create_issue(create_request, "personal")
        assert created_issue is not None

        # Add a comment
        comment_request = CommentAddRequest(
            issue_key=created_issue.key,
            comment="This is a live test comment.",
        )
        added_comment = await atlassian_api_repository.add_comment(comment_request, "personal")
        assert added_comment is not None
        assert added_comment.body == "This is a live test comment."

        # Get the issue with comments and verify
        issue_with_comments = await atlassian_api_repository.get_issue_with_comments(created_issue.key, "personal")
        assert issue_with_comments is not None
        assert len(issue_with_comments.comments) > 0
        assert any(c.body == "This is a live test comment." for c in issue_with_comments.comments)

    finally:
        if created_issue:
            # Clean up the created issue
            client = atlassian_api_repository._client_factory.create_client("personal")
            client.delete_issue(created_issue.key)
