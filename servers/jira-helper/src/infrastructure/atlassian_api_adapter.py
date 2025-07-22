"""
Jira client implementation using the atlassian-python-api library.
"""

import asyncio
import logging
from typing import Any

from atlassian import Jira

from domain.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraInstanceNotFound,
    JiraIssueNotFound,
    JiraTimeoutError,
)
from domain.models import CommentAddRequest, IssueCreateRequest, JiraIssue, JiraProject, JiraComment
from domain.ports import ConfigurationProvider, JiraClientFactory, JiraRepository
from .converters import JiraIssueConverter

logger = logging.getLogger(__name__)


class AtlassianApiJiraClientFactory(JiraClientFactory):
    """Factory for creating Jira clients using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._clients: dict[str, Jira] = {}

    def create_client(self, instance_name: str | None = None) -> Jira:
        """Create a Jira client for the specified instance."""
        if instance_name is None:
            instance_name = self._config_provider.get_default_instance_name()
            if instance_name is None:
                available_instances = list(self._config_provider.get_instances().keys())
                raise JiraInstanceNotFound("default", available_instances)

        if instance_name in self._clients:
            return self._clients[instance_name]

        instance = self._config_provider.get_instance(instance_name)
        if instance is None:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound(instance_name, available_instances)

        try:
            is_cloud = ".atlassian.net" in instance.url
            client = Jira(
                url=instance.url,
                username=instance.user,
                password=instance.token,
                cloud=is_cloud,
                timeout=30,
            )
            self._clients[instance_name] = client
            logger.info(f"Created Jira client for instance: {instance_name} using atlassian-python-api")
            return client
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "unauthorized" in error_msg:
                raise JiraAuthenticationError(instance_name, str(e))
            elif "timeout" in error_msg:
                raise JiraTimeoutError("client_creation", instance_name, 30)
            else:
                raise JiraConnectionError(instance_name, str(e))

    def validate_instance(self, instance_name: str) -> bool:
        """Validate that an instance exists and is properly configured."""
        try:
            client = self.create_client(instance_name)
            client.myself()
            return True
        except Exception:
            return False


class AtlassianApiRepository(JiraRepository):
    """Repository implementation using atlassian-python-api."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider
        self._converter = JiraIssueConverter(config_provider)

    async def get_issue(self, issue_key: str, instance_name: str) -> JiraIssue:
        """Get a specific issue by key."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue_data = await asyncio.to_thread(client.issue, issue_key)
            return self._converter.convert_issue_to_domain(issue_data, instance_name)
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(issue_key, instance_name or "default")
            logger.error(f"Failed to get issue {issue_key}: {str(e)}")
            raise


    async def get_projects(self, instance_name: str) -> list[JiraProject]:
        """Get all projects from a Jira instance."""
        try:
            client = self._client_factory.create_client(instance_name)
            projects_data = await asyncio.to_thread(client.projects)
            
            result = []
            for project_data in projects_data:
                lead_data = project_data.get("lead", {})
                instance = self._config_provider.get_instance(instance_name)
                project_url = f"{instance.url}/projects/{project_data['key']}" if instance else None

                jira_project = JiraProject(
                    key=project_data["key"],
                    name=project_data["name"],
                    id=project_data["id"],
                    lead_name=lead_data.get("displayName"),
                    lead_email=lead_data.get("emailAddress"),
                    url=project_url,
                )
                result.append(jira_project)
            return result
        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}")
            raise

    async def get_issue_with_comments(self, issue_key: str, instance_name: str) -> JiraIssue:
        """Get a specific issue with all its comments."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Get issue and comments in parallel
            issue_data, comments_data = await asyncio.gather(
                asyncio.to_thread(client.issue, issue_key),
                asyncio.to_thread(client.issue_get_comments, issue_key)
            )

            jira_issue = self._converter.convert_issue_to_domain(issue_data, instance_name)

            for comment_data in comments_data.get("comments", []):
                comment = JiraComment(
                    id=comment_data["id"],
                    author_name=comment_data.get("author", {}).get("displayName"),
                    author_key=comment_data.get("author", {}).get("key"),
                    body=comment_data.get("body"),
                    created=comment_data.get("created"),
                    updated=comment_data.get("updated"),
                )
                jira_issue.add_comment(comment)

            jira_issue.comments.sort(key=lambda c: c.created, reverse=True)
            return jira_issue

        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(issue_key, instance_name or "default")
            logger.error(f"Failed to get issue with comments {issue_key}: {str(e)}")
            raise

    async def create_issue(self, request: IssueCreateRequest, instance_name: str) -> JiraIssue:
        """Create a new issue."""
        try:
            client = self._client_factory.create_client(instance_name)

            issue_dict = {
                "project": {"key": request.project_key},
                "summary": request.summary,
                "description": request.description,
                "issuetype": {"name": request.issue_type},
            }
            if request.priority:
                issue_dict["priority"] = {"name": request.priority}
            if request.assignee:
                issue_dict["assignee"] = {"name": request.assignee}
            if request.labels:
                issue_dict["labels"] = request.labels

            created_issue_data = await asyncio.to_thread(
                client.issue_create, fields=issue_dict
            )

            # Fetch the full issue details to get all fields
            full_issue_data = await asyncio.to_thread(
                client.issue, created_issue_data["key"]
            )

            return self._converter.convert_issue_to_domain(full_issue_data, instance_name)
        except Exception as e:
            logger.error(f"Failed to create issue: {str(e)}")
            raise

    async def add_comment(self, request: CommentAddRequest, instance_name: str) -> JiraComment:
        """Add a comment to an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            comment_data = await asyncio.to_thread(
                client.issue_add_comment, request.issue_key, request.comment
            )

            return JiraComment(
                id=comment_data["id"],
                author_name=comment_data.get("author", {}).get("displayName"),
                author_key=comment_data.get("author", {}).get("key"),
                body=comment_data.get("body"),
                created=comment_data.get("created"),
                updated=comment_data.get("updated"),
            )
        except Exception as e:
            logger.error(f"Failed to add comment to {request.issue_key}: {str(e)}")
            raise

    async def get_available_transitions(self, issue_key: str, instance_name: str) -> list[Any]:
        """Get available transitions for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            transitions_data = await asyncio.to_thread(client.get_issue_transitions, issue_key)
            
            from domain.models import WorkflowTransition
            result = []
            # transitions_data is a list directly, not a dict with "transitions" key
            for transition_data in transitions_data:
                # Handle "to" field which can be a string or dict
                to_field = transition_data.get("to", "Unknown")
                if isinstance(to_field, dict):
                    to_status = to_field.get("name", "Unknown")
                else:
                    to_status = str(to_field)
                
                transition = WorkflowTransition(
                    id=transition_data["id"],
                    name=transition_data["name"],
                    to_status=to_status
                )
                result.append(transition)
            return result
        except Exception as e:
            logger.error(f"Failed to get transitions for issue {issue_key}: {str(e)}")
            raise

    async def transition_issue(self, request, instance_name: str) -> JiraIssue:
        """Transition an issue through workflow."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get available transitions to find the transition ID
            transitions_data = await asyncio.to_thread(client.get_issue_transitions, request.issue_key)
            
            # Find the transition ID by name
            transition_id = None
            for transition in transitions_data:
                if transition["name"] == request.transition_name:
                    transition_id = transition["id"]
                    break
            
            if transition_id is None:
                available_transitions = [t["name"] for t in transitions_data]
                raise ValueError(f"Transition '{request.transition_name}' not available. Available: {available_transitions}")
            
            # Execute the transition
            transition_data = {"transition": {"id": transition_id}}
            
            # Add comment if provided
            if request.comment:
                transition_data["update"] = {
                    "comment": [{"add": {"body": request.comment}}]
                }
            
            await asyncio.to_thread(
                client.set_issue_status_by_transition_id,
                request.issue_key,
                transition_id
            )
            
            # Fetch the updated issue to return
            updated_issue_data = await asyncio.to_thread(client.issue, request.issue_key)
            return self._converter.convert_issue_to_domain(updated_issue_data, instance_name)
            
        except Exception as e:
            logger.error(f"Failed to transition issue {request.issue_key}: {str(e)}")
            raise

    async def change_assignee(self, request, instance_name: str) -> JiraIssue:
        """Change the assignee of an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Build the assignee field update
            if request.assignee is None:
                # Unassign the issue
                assignee_field = {"assignee": None}
            else:
                # Assign to specific user
                assignee_field = {"assignee": {"name": request.assignee}}
            
            # Update the issue with new assignee
            await asyncio.to_thread(
                client.issue_update,
                request.issue_key,
                fields=assignee_field
            )
            
            # Fetch the updated issue to return
            updated_issue_data = await asyncio.to_thread(client.issue, request.issue_key)
            return self._converter.convert_issue_to_domain(updated_issue_data, instance_name)
            
        except Exception as e:
            logger.error(f"Failed to change assignee for issue {request.issue_key}: {str(e)}")
            raise

    async def search_issues(
        self,
        project_key: str,
        status: str | None,
        issue_type: str | None,
        max_results: int,
        instance_name: str
    ) -> list[JiraIssue]:
        raise NotImplementedError

    async def get_custom_field_mappings(self, reverse: bool, instance_name: str) -> list[Any]:
        raise NotImplementedError

    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: str) -> dict[str, Any]:
        raise NotImplementedError


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


class AtlassianIssueUpdateAdapter:
    """Adapter for issue update operations using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._converter = JiraIssueConverter(config_provider)

    async def update_issue(self, update_request, instance_name: str):
        """Update an issue with new field values."""
        try:
            from infrastructure.atlassian_api_adapter import AtlassianApiJiraClientFactory
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
            from infrastructure.atlassian_api_adapter import AtlassianApiJiraClientFactory
            client_factory = AtlassianApiJiraClientFactory(self._config_provider)
            client = client_factory.create_client(instance_name)
            await asyncio.to_thread(client.issue, issue_key)
        except Exception:
            errors.append(f"Issue {issue_key} not found or not accessible")
        
        return errors

    async def get_updatable_fields(self, issue_key: str, instance_name: str) -> list[str]:
        """Get list of fields that can be updated for the issue."""
        try:
            from infrastructure.atlassian_api_adapter import AtlassianApiJiraClientFactory
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


class AtlassianTimeFormatValidator:
    """Time format validator for Jira time tracking."""

    def validate_time_format(self, time_str: str) -> bool:
        """Validate time format (e.g., '2h 30m', '1d 4h')."""
        # Basic validation - can be enhanced later
        return isinstance(time_str, str) and len(time_str.strip()) > 0


class AtlassianTimeTrackingAdapter:
    """Adapter for time tracking operations using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider, client_factory: JiraClientFactory):
        self._config_provider = config_provider
        self._client_factory = client_factory

    async def log_work(self, work_log_request, instance_name: str):
        """Log work on an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Convert time string to seconds
            time_seconds = self._parse_time_to_seconds(work_log_request.time_spent)
            
            # Use current time if not specified
            from datetime import datetime
            started = work_log_request.started if hasattr(work_log_request, 'started') and work_log_request.started else datetime.now().isoformat()
            
            # Log work using atlassian-python-api
            result = await asyncio.to_thread(
                client.issue_worklog,
                work_log_request.issue_key,
                started,
                time_seconds
            )
            
            from domain.models import WorkLogResult
            return WorkLogResult(
                issue_key=work_log_request.issue_key,
                work_log_id=str(result.get("id")) if result and isinstance(result, dict) else None,
                logged=True,
                time_spent=work_log_request.time_spent,
                time_spent_seconds=time_seconds
            )
            
        except Exception as e:
            logger.error(f"Failed to log work on issue {work_log_request.issue_key}: {str(e)}")
            from domain.models import WorkLogResult
            return WorkLogResult(
                issue_key=work_log_request.issue_key,
                logged=False,
                error=str(e)
            )

    async def get_work_logs(self, issue_key: str, instance_name: str):
        """Get all work logs for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get work logs for the issue
            work_logs_data = await asyncio.to_thread(client.issue_get_worklog, issue_key)
            
            work_logs = []
            from domain.models import WorkLog
            
            for work_log_data in work_logs_data.get("worklogs", []):
                work_log = WorkLog(
                    id=work_log_data.get("id"),
                    author=work_log_data.get("author", {}).get("displayName"),
                    time_spent=work_log_data.get("timeSpent", ""),
                    time_spent_seconds=work_log_data.get("timeSpentSeconds", 0),
                    comment=work_log_data.get("comment", ""),
                    started=work_log_data.get("started"),
                    created=work_log_data.get("created"),
                    updated=work_log_data.get("updated")
                )
                work_logs.append(work_log)
            
            return work_logs
            
        except Exception as e:
            logger.error(f"Failed to get work logs for issue {issue_key}: {str(e)}")
            raise

    async def update_work_log(self, work_log_id: str, work_log_request, instance_name: str):
        """Update an existing work log."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Convert time string to seconds
            time_seconds = self._parse_time_to_seconds(work_log_request.time_spent)
            
            # Build update data
            update_data = {
                "timeSpentSeconds": time_seconds,
                "comment": work_log_request.comment if hasattr(work_log_request, 'comment') else ""
            }
            
            # Update work log (note: atlassian-python-api may not have direct support)
            # We'll use a custom approach with the REST API
            result = await asyncio.to_thread(
                self._update_work_log_via_api,
                client,
                work_log_request.issue_key,
                work_log_id,
                update_data
            )
            
            from domain.models import WorkLogResult
            return WorkLogResult(
                issue_key=work_log_request.issue_key,
                work_log_id=work_log_id,
                logged=True,
                time_spent=work_log_request.time_spent,
                time_spent_seconds=time_seconds
            )
            
        except Exception as e:
            logger.error(f"Failed to update work log {work_log_id}: {str(e)}")
            from domain.models import WorkLogResult
            return WorkLogResult(
                issue_key=work_log_request.issue_key,
                work_log_id=work_log_id,
                logged=False,
                error=str(e)
            )

    async def delete_work_log(self, issue_key: str, work_log_id: str, instance_name: str) -> bool:
        """Delete a work log entry."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Delete work log using REST API
            await asyncio.to_thread(
                self._delete_work_log_via_api,
                client,
                issue_key,
                work_log_id
            )
            
            logger.info(f"Successfully deleted work log {work_log_id} from issue {issue_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete work log {work_log_id}: {str(e)}")
            return False

    async def get_time_tracking_info(self, issue_key: str, instance_name: str):
        """Get time tracking information for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get issue with time tracking fields
            issue_data = await asyncio.to_thread(client.issue, issue_key, fields="timetracking,timespent,timeoriginalestimate")
            
            time_tracking = issue_data.get("fields", {}).get("timetracking", {})
            
            from domain.models import TimeTrackingInfo
            return TimeTrackingInfo(
                original_estimate=time_tracking.get("originalEstimate"),
                remaining_estimate=time_tracking.get("remainingEstimate"),
                time_spent=time_tracking.get("timeSpent"),
                original_estimate_seconds=time_tracking.get("originalEstimateSeconds", 0),
                remaining_estimate_seconds=time_tracking.get("remainingEstimateSeconds", 0),
                time_spent_seconds=time_tracking.get("timeSpentSeconds", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get time tracking info for issue {issue_key}: {str(e)}")
            raise

    async def update_time_estimates(self, estimate_update, instance_name: str):
        """Update time estimates for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Build time tracking update
            time_tracking = {}
            if estimate_update.original_estimate:
                time_tracking["originalEstimate"] = estimate_update.original_estimate
            if estimate_update.remaining_estimate:
                time_tracking["remainingEstimate"] = estimate_update.remaining_estimate
            
            # Update the issue with new time estimates
            await asyncio.to_thread(
                client.issue_update,
                estimate_update.issue_key,
                fields={"timetracking": time_tracking}
            )
            
            from domain.models import TimeEstimateResult
            return TimeEstimateResult(
                issue_key=estimate_update.issue_key,
                updated=True,
                original_estimate=estimate_update.original_estimate,
                remaining_estimate=estimate_update.remaining_estimate
            )
            
        except Exception as e:
            logger.error(f"Failed to update time estimates for issue {estimate_update.issue_key}: {str(e)}")
            from domain.models import TimeEstimateResult
            return TimeEstimateResult(
                issue_key=estimate_update.issue_key,
                updated=False,
                error=str(e)
            )

    async def is_time_tracking_enabled(self, project_key: str, issue_type: str, instance_name: str) -> bool:
        """Check if time tracking is enabled for the project/issue type."""
        try:
            # For now, assume time tracking is enabled
            # This can be enhanced later to check actual project configuration
            return True
        except Exception as e:
            logger.error(f"Failed to check time tracking status: {str(e)}")
            return False

    def _parse_time_to_seconds(self, time_str: str) -> int:
        """Parse Jira time format to seconds."""
        import re
        
        # Handle common Jira time formats: 1d 2h 30m, 2h 30m, 45m, etc.
        time_str = time_str.lower().strip()
        
        # Extract days, hours, minutes
        days = 0
        hours = 0
        minutes = 0
        
        # Match patterns like 1d, 2h, 30m
        day_match = re.search(r'(\d+)d', time_str)
        hour_match = re.search(r'(\d+)h', time_str)
        minute_match = re.search(r'(\d+)m', time_str)
        
        if day_match:
            days = int(day_match.group(1))
        if hour_match:
            hours = int(hour_match.group(1))
        if minute_match:
            minutes = int(minute_match.group(1))
        
        # Convert to seconds (assuming 8-hour work day)
        total_seconds = (days * 8 * 3600) + (hours * 3600) + (minutes * 60)
        
        return total_seconds

    def _update_work_log_via_api(self, client, issue_key: str, work_log_id: str, update_data: dict):
        """Update work log using REST API."""
        # Use the client's REST API capabilities
        url = f"rest/api/2/issue/{issue_key}/worklog/{work_log_id}"
        return client.put(url, data=update_data)

    def _delete_work_log_via_api(self, client, issue_key: str, work_log_id: str):
        """Delete work log using REST API."""
        # Use the client's REST API capabilities
        url = f"rest/api/2/issue/{issue_key}/worklog/{work_log_id}"
        return client.delete(url)
