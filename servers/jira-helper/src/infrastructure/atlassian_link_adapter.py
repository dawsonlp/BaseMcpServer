"""
Atlassian API Link Adapter implementation.

This module contains the issue linking operations using the atlassian-python-api library.
"""

import asyncio
import logging

from domain.ports import ConfigurationProvider, JiraClientFactory

logger = logging.getLogger(__name__)


class AtlassianIssueLinkAdapter:
    """Adapter for issue linking operations using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider, client_factory: JiraClientFactory):
        self._config_provider = config_provider
        self._client_factory = client_factory

    async def create_link(self, issue_link, instance_name: str):
        """Create a link between two issues."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Build link data structure according to atlassian-python-api docs
            link_data = {
                "type": {"name": issue_link.link_type},
                "inwardIssue": {"key": issue_link.target_issue},
                "outwardIssue": {"key": issue_link.source_issue}
            }
            
            # Add comment if provided
            if hasattr(issue_link, 'comment') and issue_link.comment:
                link_data["comment"] = {
                    "body": issue_link.comment,
                    "visibility": {"type": "group", "value": "jira-users"}
                }
            
            # Create the link using the correct API method
            await asyncio.to_thread(client.create_issue_link, link_data)
            
            from domain.models import IssueLinkResult
            return IssueLinkResult(
                source_issue=issue_link.source_issue,
                target_issue=issue_link.target_issue,
                link_type=issue_link.link_type,
                created=True,
                link_id=None  # API doesn't return link ID directly
            )
            
        except Exception as e:
            logger.error(f"Failed to create link between {issue_link.source_issue} and {issue_link.target_issue}: {str(e)}")
            from domain.models import IssueLinkResult
            return IssueLinkResult(
                source_issue=issue_link.source_issue,
                target_issue=issue_link.target_issue,
                link_type=issue_link.link_type,
                created=False,
                error=str(e)
            )

    async def get_links(self, issue_key: str, instance_name: str):
        """Get all links for a specific issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get issue with link information
            issue_data = await asyncio.to_thread(client.issue, issue_key, expand="issuelinks")
            
            links = []
            issue_links = issue_data.get("fields", {}).get("issuelinks", [])
            
            from domain.models import IssueLink, LinkDirection
            
            for link_data in issue_links:
                link_type = link_data.get("type", {}).get("name", "Unknown")
                
                # Handle outward links (this issue links to another)
                if "outwardIssue" in link_data:
                    target_issue = link_data["outwardIssue"]["key"]
                    link = IssueLink(
                        link_type=link_type,
                        source_issue=issue_key,
                        target_issue=target_issue,
                        direction=LinkDirection.OUTWARD.value,
                        link_id=str(link_data.get("id", ""))
                    )
                    links.append(link)
                
                # Handle inward links (another issue links to this one)
                if "inwardIssue" in link_data:
                    source_issue = link_data["inwardIssue"]["key"]
                    link = IssueLink(
                        link_type=link_type,
                        source_issue=source_issue,
                        target_issue=issue_key,
                        direction=LinkDirection.INWARD.value,
                        link_id=str(link_data.get("id", ""))
                    )
                    links.append(link)
            
            return links
            
        except Exception as e:
            logger.error(f"Failed to get links for issue {issue_key}: {str(e)}")
            raise

    async def remove_link(self, link_id: str, instance_name: str) -> bool:
        """Remove a link between issues."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Remove the issue link using the correct API method
            await asyncio.to_thread(client.remove_issue_link, link_id)
            
            logger.info(f"Successfully removed link {link_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove link {link_id}: {str(e)}")
            return False

    async def get_available_link_types(self, instance_name: str) -> list[str]:
        """Get available link types for the Jira instance."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get issue link types using the correct API method
            link_types_data = await asyncio.to_thread(client.get_issue_link_types)
            
            link_types = []
            for link_type_data in link_types_data.get("issueLinkTypes", []):
                link_types.append(link_type_data.get("name", "Unknown"))
            
            return link_types
            
        except Exception as e:
            logger.error(f"Failed to get available link types: {str(e)}")
            # Return common link types as fallback
            return ["Blocks", "Clones", "Duplicates", "Relates", "Epic-Story"]
