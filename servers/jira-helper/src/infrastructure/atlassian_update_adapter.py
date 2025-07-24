"""
Atlassian API Update Adapter implementation.

This module contains the issue update operations using the atlassian-python-api library.
"""

import asyncio
import logging

from domain.ports import ConfigurationProvider
from infrastructure.converters import JiraIssueConverter

logger = logging.getLogger(__name__)


class AtlassianIssueUpdateAdapter:
    """Adapter for issue update operations using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._converter = JiraIssueConverter(config_provider)

    async def update_issue(self, update_request, instance_name: str):
        """Update an issue with new field values."""
        try:
            from infrastructure.atlassian_repository import AtlassianApiJiraClientFactory
            client_factory = AtlassianApiJiraClientFactory(self._config_provider)
            client = client_factory.create_client(instance_name)

            # Build the fields dictionary for the update
            fields = {}
            if update_request.summary:
                fields["summary"] = update_request.summary
            if update_request.description:
                fields["description"] = update_request.description
            if update_request.priority:
                fields["priority"] = {"name": update_request.priority}
            if update_request.assignee:
                fields["assignee"] = {"name": update_request.assignee}
            if update_request.labels is not None:
                fields["labels"] = update_request.labels

            # Update the issue
            await asyncio.to_thread(
                client.issue_update,
                update_request.issue_key,
                fields=fields
            )

            # Fetch the updated issue to return
            updated_issue_data = await asyncio.to_thread(client.issue, update_request.issue_key)
            updated_issue = self._converter.convert_issue_to_domain(updated_issue_data, instance_name)

            from domain.models import IssueUpdateResult
            return IssueUpdateResult(
                issue_key=update_request.issue_key,
                updated=True,
                updated_fields=list(fields.keys())
            )

        except Exception as e:
            logger.error(f"Failed to update issue {update_request.issue_key}: {str(e)}")
            from domain.models import IssueUpdateResult
            return IssueUpdateResult(
                issue_key=update_request.issue_key,
                updated=False,
                error=str(e)
            )

    async def validate_update_fields(self, issue_key: str, fields: dict, instance_name: str) -> list[str]:
        """Validate that fields can be updated."""
        # Basic validation - can be enhanced with actual Jira field validation
        errors = []
        
        # Check if issue exists
        try:
            from infrastructure.atlassian_repository import AtlassianApiJiraClientFactory
            client_factory = AtlassianApiJiraClientFactory(self._config_provider)
            client = client_factory.create_client(instance_name)
            await asyncio.to_thread(client.issue, issue_key)
        except Exception:
            errors.append(f"Issue {issue_key} not found or not accessible")
        
        return errors

    async def get_updatable_fields(self, issue_key: str, instance_name: str) -> list[str]:
        """Get list of fields that can be updated for the issue."""
        try:
            from infrastructure.atlassian_repository import AtlassianApiJiraClientFactory
            client_factory = AtlassianApiJiraClientFactory(self._config_provider)
            client = client_factory.create_client(instance_name)
            
            # Get edit metadata for the issue
            edit_meta = await asyncio.to_thread(client.issue_editmeta, issue_key)
            
            # Extract field names from metadata
            fields = list(edit_meta.get("fields", {}).keys())
            return fields
            
        except Exception as e:
            logger.error(f"Failed to get updatable fields for {issue_key}: {str(e)}")
            # Return common updatable fields as fallback
            return ["summary", "description", "priority", "assignee", "labels"]
