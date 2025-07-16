"""
Jira API Repository implementation using BaseJiraAdapter.

This module implements the JiraRepository port using the base adapter pattern,
eliminating massive boilerplate while maintaining all functionality.
"""

import logging
from typing import Any

from domain.exceptions import (
    JiraAssigneeError,
    JiraCommentError,
    JiraIssueNotFound,
    JiraPermissionError,
    JiraProjectNotFound,
    JiraTransitionNotAvailable,
    JiraWorkflowError,
)
from domain.models import (
    AssigneeChangeRequest,
    CommentAddRequest,
    CustomFieldMapping,
    IssueCreateRequest,
    IssueTransitionRequest,
    JiraComment,
    JiraIssue,
    JiraProject,
    WorkflowTransition,
)
from domain.ports import ConfigurationProvider, JiraClientFactory, JiraRepository
from infrastructure.base_adapter import BaseJiraAdapter

logger = logging.getLogger(__name__)


class JiraApiRepository(BaseJiraAdapter, JiraRepository):
    """Repository implementation using Jira REST API with base adapter pattern."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        super().__init__(client_factory, config_provider)

    async def get_projects(self, instance_name: str | None = None) -> list[JiraProject]:
        """Get all projects from a Jira instance."""
        async def operation(client):
            projects = client.projects()
            return [self._convert_project_to_domain(project, instance_name) for project in projects]

        return await self._execute_jira_operation("get_projects", operation, instance_name)

    async def get_issue(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
        """Get a specific issue by key."""
        async def operation(client):
            issue = client.issue(issue_key)
            return self._convert_issue_to_domain(issue, instance_name)

        error_mappings = {
            "does not exist": JiraIssueNotFound(issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(issue_key, instance_name or "default")
        }

        return await self._execute_jira_operation("get_issue", operation, instance_name, error_mappings)

    async def get_issue_with_comments(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
        """Get a specific issue with all its comments."""
        async def operation(client):
            issue = client.issue(issue_key, expand='comments')
            jira_issue = self._convert_issue_to_domain(issue, instance_name)

            # Get and convert comments
            comments = client.comments(issue_key)
            for comment in comments:
                jira_comment = self._convert_comment_to_domain(comment)
                jira_issue.add_comment(jira_comment)

            # Sort comments by creation date (newest first)
            jira_issue.comments.sort(key=lambda c: c.created, reverse=True)
            return jira_issue

        error_mappings = {
            "does not exist": JiraIssueNotFound(issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(issue_key, instance_name or "default")
        }

        return await self._execute_jira_operation("get_issue_with_comments", operation, instance_name, error_mappings)

    async def create_issue(self, request: IssueCreateRequest, instance_name: str | None = None) -> JiraIssue:
        """Create a new issue."""
        async def operation(client):
            issue_dict = self._build_issue_dict(request)
            new_issue = client.create_issue(fields=issue_dict)
            return self._convert_issue_to_domain(new_issue, instance_name)

        error_mappings = {
            "permission": JiraPermissionError("create_issue", f"project {request.project_key}", instance_name or "default"),
            "forbidden": JiraPermissionError("create_issue", f"project {request.project_key}", instance_name or "default"),
            "project": JiraProjectNotFound(request.project_key, instance_name or "default")
        }

        return await self._execute_jira_operation("create_issue", operation, instance_name, error_mappings)

    async def add_comment(self, request: CommentAddRequest, instance_name: str | None = None) -> JiraComment:
        """Add a comment to an issue."""
        async def operation(client):
            # Verify issue exists
            client.issue(request.issue_key)
            # Add comment
            comment_obj = client.add_comment(request.issue_key, request.comment)
            return self._convert_comment_to_domain(comment_obj)

        error_mappings = {
            "does not exist": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "permission": JiraPermissionError("add_comment", f"issue {request.issue_key}", instance_name or "default"),
            "forbidden": JiraPermissionError("add_comment", f"issue {request.issue_key}", instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("add_comment", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound | JiraPermissionError):
                raise JiraCommentError(str(e), request.issue_key)
            raise

    async def get_available_transitions(self, issue_key: str, instance_name: str | None = None) -> list[WorkflowTransition]:
        """Get available transitions for an issue."""
        async def operation(client):
            issue = client.issue(issue_key)
            transitions = client.transitions(issue)

            return [
                WorkflowTransition(
                    id=transition['id'],
                    name=transition['name'],
                    to_status=transition['to']['name'] if 'to' in transition else "Unknown",
                    from_status=issue.fields.status.name
                )
                for transition in transitions
            ]

        error_mappings = {
            "does not exist": JiraIssueNotFound(issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(issue_key, instance_name or "default")
        }

        return await self._execute_jira_operation("get_available_transitions", operation, instance_name, error_mappings)

    async def transition_issue(self, request: IssueTransitionRequest, instance_name: str | None = None) -> JiraIssue:
        """Transition an issue through workflow."""
        async def operation(client):
            issue = client.issue(request.issue_key)
            transitions = client.transitions(issue)

            # Find the matching transition
            target_transition = None
            for transition in transitions:
                if transition['name'].lower() == request.transition_name.lower():
                    target_transition = transition
                    break

            if not target_transition:
                available_transitions = [t['name'] for t in transitions]
                raise JiraTransitionNotAvailable(request.issue_key, request.transition_name, available_transitions)

            # Prepare transition data
            transition_data = {}
            if request.comment:
                transition_data['comment'] = [{'add': {'body': request.comment}}]

            # Execute transition
            client.transition_issue(issue, target_transition['id'], **transition_data)

            # Get updated issue
            updated_issue = client.issue(request.issue_key)
            return self._convert_issue_to_domain(updated_issue, instance_name)

        error_mappings = {
            "does not exist": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "permission": JiraPermissionError("transition_issue", f"issue {request.issue_key}", instance_name or "default"),
            "forbidden": JiraPermissionError("transition_issue", f"issue {request.issue_key}", instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("transition_issue", operation, instance_name, error_mappings)
        except JiraTransitionNotAvailable:
            raise
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound | JiraPermissionError):
                raise JiraWorkflowError(str(e), request.issue_key)
            raise

    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: str | None = None) -> JiraIssue:
        """Change the assignee of an issue."""
        async def operation(client):
            issue = client.issue(request.issue_key)
            client.assign_issue(issue, request.assignee)

            # Get updated issue
            updated_issue = client.issue(request.issue_key)
            return self._convert_issue_to_domain(updated_issue, instance_name)

        error_mappings = {
            "does not exist": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(request.issue_key, instance_name or "default"),
            "permission": JiraPermissionError("change_assignee", f"issue {request.issue_key}", instance_name or "default"),
            "forbidden": JiraPermissionError("change_assignee", f"issue {request.issue_key}", instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("change_assignee", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound | JiraPermissionError):
                raise JiraAssigneeError(str(e), request.issue_key, request.assignee)
            raise

    async def search_issues(
        self,
        project_key: str,
        status: str | None = None,
        issue_type: str | None = None,
        max_results: int = 50,
        instance_name: str | None = None
    ) -> list[JiraIssue]:
        """Search for issues in a project with filters."""
        async def operation(client):
            jql = self._build_search_jql(project_key, status, issue_type)
            issues = client.search_issues(jql, maxResults=max_results)
            return [self._convert_issue_to_domain(issue, instance_name) for issue in issues]

        return await self._execute_jira_operation("search_issues", operation, instance_name)

    async def get_custom_field_mappings(self, reverse: bool = False, instance_name: str | None = None) -> list[CustomFieldMapping]:
        """Get custom field mappings."""
        async def operation(client):
            fields = client.fields()
            custom_fields = [field for field in fields if field['id'].startswith('customfield_')]

            return [
                CustomFieldMapping(
                    field_id=field['id'],
                    name=field['name'],
                    description=field.get('description', "")
                )
                for field in custom_fields
            ]

        return await self._execute_jira_operation("get_custom_field_mappings", operation, instance_name)

    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: str | None = None) -> dict[str, Any]:
        """Get workflow data for a project and issue type."""
        async def operation(client):
            project = client.project(project_key)

            # Try to get workflow information
            try:
                workflow_data = client._get_json(f"project/{project.id}/statuses")
                return {
                    "project_id": project.id,
                    "project_key": project_key,
                    "issue_type": issue_type,
                    "workflow_data": workflow_data
                }
            except Exception:
                # Fallback: get a sample issue to analyze workflow
                return self._get_workflow_fallback_data(client, project, project_key, issue_type)

        error_mappings = {
            "project": JiraProjectNotFound(project_key, instance_name or "default"),
            "not found": JiraProjectNotFound(project_key, instance_name or "default")
        }

        return await self._execute_jira_operation("get_workflow_data", operation, instance_name, error_mappings)

    # Helper methods for domain conversion and data building
    def _convert_project_to_domain(self, project, instance_name: str | None = None) -> JiraProject:
        """Convert Jira project to domain model."""
        # Get project lead information if available
        lead_name = None
        lead_email = None
        if hasattr(project, 'lead'):
            lead = project.lead
            lead_name = getattr(lead, 'displayName', None)
            lead_email = getattr(lead, 'emailAddress', None)

        # Get instance URL for project URL
        instance = self._config_provider.get_instance(instance_name)
        project_url = f"{instance.url}/projects/{project.key}" if instance else None

        return JiraProject(
            key=project.key,
            name=project.name,
            id=project.id,
            lead_name=lead_name,
            lead_email=lead_email,
            url=project_url
        )

    def _convert_issue_to_domain(self, issue, instance_name: str | None = None) -> JiraIssue:
        """Convert Jira API issue to domain model."""
        fields = issue.fields

        # Get instance URL for issue URL
        instance = self._config_provider.get_instance(instance_name)
        issue_url = f"{instance.url}/browse/{issue.key}" if instance else None

        # Extract custom fields
        custom_fields = {}
        for field_name in dir(fields):
            if field_name.startswith('customfield_'):
                value = getattr(fields, field_name)
                if value is not None:
                    custom_fields[field_name] = value

        return JiraIssue(
            key=issue.key,
            id=issue.id,
            summary=fields.summary,
            description=fields.description or "",
            status=fields.status.name,
            issue_type=fields.issuetype.name,
            priority=getattr(fields.priority, 'name', 'None') if hasattr(fields, 'priority') and fields.priority else 'None',
            assignee=getattr(fields.assignee, 'displayName', None) if fields.assignee else None,
            reporter=getattr(fields.reporter, 'displayName', None) if fields.reporter else None,
            created=fields.created,
            updated=fields.updated,
            components=[c.name for c in fields.components] if fields.components else [],
            labels=fields.labels if fields.labels else [],
            custom_fields=custom_fields,
            url=issue_url
        )

    def _convert_comment_to_domain(self, comment) -> JiraComment:
        """Convert Jira comment to domain model."""
        return JiraComment(
            id=comment.id,
            author_name=getattr(comment.author, 'displayName', str(comment.author)),
            author_key=getattr(comment.author, 'key', None),
            body=comment.body,
            created=comment.created,
            updated=getattr(comment, 'updated', None)
        )

    def _build_issue_dict(self, request: IssueCreateRequest) -> dict[str, Any]:
        """Build issue dictionary for creation."""
        issue_dict = {
            'project': {'key': request.project_key},
            'summary': request.summary,
            'description': request.description,
            'issuetype': {'name': request.issue_type},
        }

        # Add optional fields
        if request.priority:
            issue_dict['priority'] = {'name': request.priority}
        if request.assignee:
            issue_dict['assignee'] = {'name': request.assignee}
        if request.labels:
            issue_dict['labels'] = request.labels

        return issue_dict

    def _build_search_jql(self, project_key: str, status: str | None = None, issue_type: str | None = None) -> str:
        """Build JQL query for search."""
        jql = f"project = {project_key}"

        if status:
            jql += f" AND status = '{status}'"

        if issue_type:
            jql += f" AND issuetype = '{issue_type}'"

        jql += " ORDER BY created DESC"
        return jql

    def _get_workflow_fallback_data(self, client, project, project_key: str, issue_type: str) -> dict[str, Any]:
        """Get workflow data using fallback method."""
        jql = f"project = {project_key} AND issuetype = '{issue_type}'"
        issues = client.search_issues(jql, maxResults=1)

        if issues:
            sample_issue = issues[0]
            transitions = client.transitions(sample_issue)
            return {
                "project_id": project.id,
                "project_key": project_key,
                "issue_type": issue_type,
                "sample_issue": sample_issue.key,
                "current_status": sample_issue.fields.status.name,
                "available_transitions": transitions
            }
        else:
            return {
                "project_id": project.id,
                "project_key": project_key,
                "issue_type": issue_type,
                "error": f"No issues of type '{issue_type}' found"
            }
