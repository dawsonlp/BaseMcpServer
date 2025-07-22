"""
Debug script to test the get_projects method.
"""

import pytest
from infrastructure.atlassian_api_adapter import (
    AtlassianApiJiraClientFactory,
    AtlassianApiRepository,
)
from config import Settings


@pytest.mark.asyncio
async def test_debug_get_projects():
    """
    Tests the get_projects method against the live Jira instance.
    """
    config_provider = Settings()
    client_factory = AtlassianApiJiraClientFactory(config_provider)
    repository = AtlassianApiRepository(client_factory, config_provider)

    instance = config_provider.get_jira_instance("personal")
    print(f"JIRA_URL: {instance.url}")
    print(f"JIRA_USER: {instance.user}")
    print(f"JIRA_API_TOKEN: {instance.token}")

    projects = await repository.get_projects()
    
    print("\nRetrieved Projects:")
    for project in projects:
        print(f"- {project.key}: {project.name}")

    assert any(p.key == "ATP" for p in projects)
