"""
Centralized conversion utilities for Jira API responses to domain models.

This module eliminates code duplication by providing a single source of truth
for converting Jira API responses to domain objects.
"""

from domain.models import JiraIssue, JiraComment
from domain.ports import ConfigurationProvider


class JiraIssueConverter:
    """Centralized Jira API to domain model conversion."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider

    def convert_issue_to_domain(self, issue_data: dict, instance_name: str) -> JiraIssue:
        """Convert Jira API issue to domain model."""
        fields = issue_data.get("fields", {})
        instance = self._config_provider.get_instance(instance_name)
        issue_url = f"{instance.url}/browse/{issue_data['key']}" if instance else None

        custom_fields = {
            key: value
            for key, value in fields.items()
            if key.startswith("customfield_") and value is not None
        }

        # Ensure all required fields have non-empty values
        key = issue_data.get("key") or "UNKNOWN"
        issue_id = issue_data.get("id") or "0"
        summary = fields.get("summary") or "No Summary"
        status = fields.get("status", {}).get("name") or "Unknown"
        issue_type = fields.get("issuetype", {}).get("name") or "Unknown"
        priority = fields.get("priority", {}).get("name") or "Medium"

        return JiraIssue(
            key=key,
            id=issue_id,
            summary=summary,
            description=fields.get("description", ""),
            status=status,
            issue_type=issue_type,
            priority=priority,
            assignee=fields.get("assignee").get("displayName") if fields.get("assignee") else None,
            reporter=fields.get("reporter", {}).get("displayName"),
            created=fields.get("created"),
            updated=fields.get("updated"),
            components=[c.get("name") for c in fields.get("components", [])],
            labels=fields.get("labels", []),
            custom_fields=custom_fields,
            url=issue_url,
        )

    def convert_comment_to_domain(self, comment_data: dict) -> JiraComment:
        """Convert Jira API comment to domain model."""
        return JiraComment(
            id=comment_data["id"],
            author_name=comment_data.get("author", {}).get("displayName"),
            author_key=comment_data.get("author", {}).get("key"),
            body=comment_data.get("body"),
            created=comment_data.get("created"),
            updated=comment_data.get("updated"),
        )

    def convert_issues_to_domain(self, issues_data: list[dict], instance_name: str) -> list[JiraIssue]:
        """Convert multiple Jira API issues to domain models."""
        return [
            self.convert_issue_to_domain(issue_data, instance_name)
            for issue_data in issues_data
        ]

    def convert_comments_to_domain(self, comments_data: list[dict]) -> list[JiraComment]:
        """Convert multiple Jira API comments to domain models."""
        return [
            self.convert_comment_to_domain(comment_data)
            for comment_data in comments_data
        ]
