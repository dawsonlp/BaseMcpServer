"""
Atlassian API Repository implementation.

This module contains the core repository implementation for Jira operations
using the atlassian-python-api library.
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
from infrastructure.converters import JiraIssueConverter

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
        """Search for issues in a project with filters."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Build JQL query from parameters
            jql_parts = [f"project = {project_key}"]
            
            if status:
                jql_parts.append(f"status = \"{status}\"")
            
            if issue_type:
                jql_parts.append(f"issuetype = \"{issue_type}\"")
            
            jql_parts.append("ORDER BY created DESC")
            jql = " AND ".join(jql_parts)
            
            # Execute search
            search_results = await asyncio.to_thread(
                client.jql,
                jql,
                limit=max_results
            )
            
            # Convert results to domain objects
            issues = []
            for issue_data in search_results.get("issues", []):
                issue = self._converter.convert_issue_to_domain(issue_data, instance_name)
                issues.append(issue)
            
            logger.info(f"Found {len(issues)} issues for project {project_key}")
            return issues
            
        except Exception as e:
            logger.error(f"Failed to search issues in project {project_key}: {str(e)}")
            raise

    async def get_custom_field_mappings(self, reverse: bool, instance_name: str) -> list[Any]:
        """Get custom field mappings."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get all fields from Jira
            fields_data = await asyncio.to_thread(client.get_all_fields)
            
            from domain.models import CustomFieldMapping
            mappings = []
            
            for field_data in fields_data:
                # Only include custom fields (they start with 'customfield_')
                if field_data.get("id", "").startswith("customfield_"):
                    if reverse:
                        # Map from name to ID
                        mapping = CustomFieldMapping(
                            name=field_data.get("name", ""),
                            field_id=field_data.get("id", ""),
                            description=field_data.get("description", "")
                        )
                    else:
                        # Map from ID to name (default)
                        mapping = CustomFieldMapping(
                            field_id=field_data.get("id", ""),
                            name=field_data.get("name", ""),
                            description=field_data.get("description", "")
                        )
                    mappings.append(mapping)
            
            logger.info(f"Retrieved {len(mappings)} custom field mappings")
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to get custom field mappings: {str(e)}")
            raise

    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: str) -> dict[str, Any]:
        """Get workflow data for a project and issue type."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get project information
            project_data = await asyncio.to_thread(client.project, project_key)
            
            # Get issue type schemes for the project
            issue_type_schemes = await asyncio.to_thread(
                client.get_project_issue_type_scheme,
                project_key
            )
            
            # Get workflow scheme for the project
            workflow_schemes = await asyncio.to_thread(
                client.get_project_workflow_scheme,
                project_key
            )
            
            # Combine the data
            workflow_data = {
                "project": {
                    "key": project_data.get("key"),
                    "name": project_data.get("name"),
                    "id": project_data.get("id")
                },
                "issue_type": issue_type,
                "issue_type_schemes": issue_type_schemes,
                "workflow_schemes": workflow_schemes,
                "statuses": [],
                "transitions": []
            }
            
            # Try to get statuses for the project
            try:
                statuses_data = await asyncio.to_thread(client.get_project_statuses, project_key)
                workflow_data["statuses"] = statuses_data
            except Exception as e:
                logger.warning(f"Could not get statuses for project {project_key}: {str(e)}")
            
            logger.info(f"Retrieved workflow data for project {project_key}, issue type {issue_type}")
            return workflow_data
            
        except Exception as e:
            logger.error(f"Failed to get workflow data for project {project_key}: {str(e)}")
            raise
