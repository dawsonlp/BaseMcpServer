"""
Atlassian API Search Adapter implementation.

This module contains the search operations using the atlassian-python-api library.
"""

import asyncio
import logging

from domain.ports import ConfigurationProvider, JiraClientFactory
from .converters import JiraIssueConverter

logger = logging.getLogger(__name__)


class AtlassianJQLValidator:
    """JQL query validator using atlassian-python-api."""

    def validate_jql(self, jql: str) -> bool:
        """Validate JQL syntax."""
        # Basic validation - can be enhanced later
        return isinstance(jql, str) and len(jql.strip()) > 0

    def validate_syntax(self, jql: str) -> tuple[bool, list[str]]:
        """Validate JQL syntax and return validation result with errors."""
        if not isinstance(jql, str) or len(jql.strip()) == 0:
            return False, ["JQL query cannot be empty"]
        
        # Basic validation - can be enhanced later with actual JQL parsing
        return True, []

    def check_security(self, jql: str) -> list[str]:
        """Check JQL for security issues."""
        errors = []
        
        # Basic security checks - can be enhanced later
        jql_lower = jql.lower()
        
        # Check for potentially dangerous SQL-like operations (word boundaries)
        import re
        dangerous_patterns = [
            r'\bdelete\b',
            r'\bdrop\b', 
            r'\btruncate\b',
            r'\balter\b',
            r'\binsert\b',
            r'\bupdate\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, jql_lower):
                # Extract the matched word for the error message
                match = re.search(pattern, jql_lower)
                if match:
                    errors.append(f"Potentially dangerous operation detected: {match.group()}")
        
        return errors

    def validate_limits(self, max_results: int, start_at: int) -> list[str]:
        """Validate query limits."""
        errors = []
        
        if max_results <= 0:
            errors.append("Max results must be greater than 0")
        
        if max_results > 1000:
            errors.append("Max results cannot exceed 1000")
        
        if start_at < 0:
            errors.append("Start at must be non-negative")
        
        return errors


class AtlassianSearchAdapter:
    """Adapter for search operations using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider, client_factory: JiraClientFactory):
        self._config_provider = config_provider
        self._client_factory = client_factory
        self._converter = JiraIssueConverter(config_provider)

    async def search_issues(self, query, instance_name: str):
        """Search for issues using JQL."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Extract parameters from query object
            jql = query.jql
            max_results = getattr(query, 'max_results', 50)
            start_at = getattr(query, 'start_at', 0)
            fields = getattr(query, 'fields', None)
            
            # Build JQL with pagination if needed
            paginated_jql = jql
            if max_results and max_results < 1000:
                # Note: atlassian-python-api jql() method doesn't support pagination parameters
                # We'll get all results and slice them manually for now
                pass
            
            # Use JQL search with atlassian-python-api (simple call)
            search_results = await asyncio.to_thread(client.jql, jql)
            
            # Handle pagination manually since the API doesn't support it directly
            all_issues = search_results.get('issues', [])
            total_results = len(all_issues)
            
            # Apply manual pagination
            end_at = start_at + max_results
            paginated_issues = all_issues[start_at:end_at]
            
            # Convert results to domain models
            issues = []
            for issue_data in paginated_issues:
                jira_issue = self._converter.convert_issue_to_domain(issue_data, instance_name)
                issues.append(jira_issue)
            
            # Create SearchResult object
            from domain.models import SearchResult
            return SearchResult(
                jql=jql,
                total_results=total_results,
                start_at=start_at,
                max_results=max_results,
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Failed to search issues with JQL '{jql}': {str(e)}")
            raise

    async def validate_jql(self, jql: str, instance_name: str) -> list[str]:
        """Validate JQL query with Jira instance."""
        # For now, return empty list (no errors) for basic validation
        # This can be enhanced later to actually validate with Jira API
        return []

    async def get_search_suggestions(self, partial_jql: str, instance_name: str) -> list[str]:
        """Get JQL completion suggestions."""
        # Basic suggestions - can be enhanced later
        return []
