"""
Jira client implementation for the Jira Helper.

This module implements the JiraRepository port using the Jira Python library,
handling all interactions with the Jira REST API.
"""

from typing import List, Optional, Dict, Any
import logging
from jira import JIRA

from domain.ports import JiraRepository, JiraClientFactory, ConfigurationProvider
from domain.models import (
    JiraProject, JiraIssue, JiraComment, WorkflowTransition, CustomFieldMapping,
    IssueCreateRequest, IssueTransitionRequest, AssigneeChangeRequest, CommentAddRequest
)

from domain.exceptions import (
    JiraConnectionError, JiraAuthenticationError, JiraInstanceNotFound,
    JiraIssueNotFound, JiraProjectNotFound, JiraTransitionNotAvailable,
    JiraWorkflowError, JiraAssigneeError, JiraCommentError, JiraCustomFieldError,
    JiraSearchError, JiraPermissionError, JiraRateLimitError, JiraTimeoutError
)

logger = logging.getLogger(__name__)


class JiraClientFactoryImpl(JiraClientFactory):
    """Factory for creating Jira clients."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._clients: Dict[str, JIRA] = {}

    def create_client(self, instance_name: Optional[str] = None) -> JIRA:
        """Create a Jira client for the specified instance."""
        # Resolve instance name
        if instance_name is None:
            instance_name = self._config_provider.get_default_instance_name()
            if instance_name is None:
                available_instances = list(self._config_provider.get_instances().keys())
                raise JiraInstanceNotFound("default", available_instances)

        # Check if client already exists
        if instance_name in self._clients:
            return self._clients[instance_name]

        # Get instance configuration
        instance = self._config_provider.get_instance(instance_name)
        if instance is None:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound(instance_name, available_instances)

        try:
            # Create Jira client
            client = JIRA(
                server=instance.url,
                basic_auth=(instance.user, instance.token),
                timeout=30  # 30 second timeout
            )
            
            # Cache the client
            self._clients[instance_name] = client
            logger.info(f"Created Jira client for instance: {instance_name}")
            
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
            # Try a simple API call to validate connection
            client.myself()
            return True
        except Exception:
            return False


class JiraApiRepository(JiraRepository):
    """Repository implementation using Jira REST API."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider

    async def get_projects(self, instance_name: Optional[str] = None) -> List[JiraProject]:
        """Get all projects from a Jira instance."""
        try:
            client = self._client_factory.create_client(instance_name)
            projects = client.projects()
            
            result = []
            for project in projects:
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
                
                jira_project = JiraProject(
                    key=project.key,
                    name=project.name,
                    id=project.id,
                    lead_name=lead_name,
                    lead_email=lead_email,
                    url=project_url
                )
                result.append(jira_project)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}")
            raise

    async def get_issue(self, issue_key: str, instance_name: Optional[str] = None) -> JiraIssue:
        """Get a specific issue by key."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(issue_key)
            
            return self._convert_issue_to_domain(issue, instance_name)
            
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(issue_key, instance_name or "default")
            logger.error(f"Failed to get issue {issue_key}: {str(e)}")
            raise

    async def get_issue_with_comments(self, issue_key: str, instance_name: Optional[str] = None) -> JiraIssue:
        """Get a specific issue with all its comments."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(issue_key, expand='comments')
            
            # Convert issue
            jira_issue = self._convert_issue_to_domain(issue, instance_name)
            
            # Get and convert comments
            comments = client.comments(issue_key)
            for comment in comments:
                jira_comment = JiraComment(
                    id=comment.id,
                    author_name=getattr(comment.author, 'displayName', str(comment.author)),
                    author_key=getattr(comment.author, 'key', None),
                    body=comment.body,
                    created=comment.created,
                    updated=getattr(comment, 'updated', None)
                )
                jira_issue.add_comment(jira_comment)
            
            # Sort comments by creation date (newest first)
            jira_issue.comments.sort(key=lambda c: c.created, reverse=True)
            
            return jira_issue
            
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(issue_key, instance_name or "default")
            logger.error(f"Failed to get issue with comments {issue_key}: {str(e)}")
            raise

    async def create_issue(self, request: IssueCreateRequest, instance_name: Optional[str] = None) -> JiraIssue:
        """Create a new issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Prepare issue fields
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
            
            # Create the issue
            new_issue = client.create_issue(fields=issue_dict)
            
            # Convert to domain model
            return self._convert_issue_to_domain(new_issue, instance_name)
            
        except Exception as e:
            error_msg = str(e).lower()
            if "permission" in error_msg or "forbidden" in error_msg:
                raise JiraPermissionError("create_issue", f"project {request.project_key}", instance_name or "default")
            elif "project" in error_msg and "not found" in error_msg:
                raise JiraProjectNotFound(request.project_key, instance_name or "default")
            logger.error(f"Failed to create issue: {str(e)}")
            raise

    async def add_comment(self, request: CommentAddRequest, instance_name: Optional[str] = None) -> JiraComment:
        """Add a comment to an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Verify issue exists
            issue = client.issue(request.issue_key)
            
            # Add comment
            comment_obj = client.add_comment(request.issue_key, request.comment)
            
            return JiraComment(
                id=comment_obj.id,
                author_name=getattr(comment_obj.author, 'displayName', str(comment_obj.author)),
                author_key=getattr(comment_obj.author, 'key', None),
                body=comment_obj.body,
                created=comment_obj.created,
                updated=getattr(comment_obj, 'updated', None)
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(request.issue_key, instance_name or "default")
            elif "permission" in error_msg or "forbidden" in error_msg:
                raise JiraPermissionError("add_comment", f"issue {request.issue_key}", instance_name or "default")
            logger.error(f"Failed to add comment to {request.issue_key}: {str(e)}")
            raise JiraCommentError(str(e), request.issue_key)

    async def get_available_transitions(self, issue_key: str, instance_name: Optional[str] = None) -> List[WorkflowTransition]:
        """Get available transitions for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(issue_key)
            transitions = client.transitions(issue)
            
            result = []
            for transition in transitions:
                workflow_transition = WorkflowTransition(
                    id=transition['id'],
                    name=transition['name'],
                    to_status=transition['to']['name'] if 'to' in transition else "Unknown",
                    from_status=issue.fields.status.name
                )
                result.append(workflow_transition)
            
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(issue_key, instance_name or "default")
            logger.error(f"Failed to get transitions for {issue_key}: {str(e)}")
            raise

    async def transition_issue(self, request: IssueTransitionRequest, instance_name: Optional[str] = None) -> JiraIssue:
        """Transition an issue through workflow."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(request.issue_key)
            
            # Get available transitions
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
            
        except JiraTransitionNotAvailable:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(request.issue_key, instance_name or "default")
            elif "permission" in error_msg or "forbidden" in error_msg:
                raise JiraPermissionError("transition_issue", f"issue {request.issue_key}", instance_name or "default")
            logger.error(f"Failed to transition issue {request.issue_key}: {str(e)}")
            raise JiraWorkflowError(str(e), request.issue_key)

    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: Optional[str] = None) -> JiraIssue:
        """Change the assignee of an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(request.issue_key)
            
            # Update assignee
            client.assign_issue(issue, request.assignee)
            
            # Get updated issue
            updated_issue = client.issue(request.issue_key)
            return self._convert_issue_to_domain(updated_issue, instance_name)
            
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(request.issue_key, instance_name or "default")
            elif "permission" in error_msg or "forbidden" in error_msg:
                raise JiraPermissionError("change_assignee", f"issue {request.issue_key}", instance_name or "default")
            logger.error(f"Failed to change assignee for {request.issue_key}: {str(e)}")
            raise JiraAssigneeError(str(e), request.issue_key, request.assignee)

    async def search_issues(
        self, 
        project_key: str, 
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50,
        instance_name: Optional[str] = None
    ) -> List[JiraIssue]:
        """Search for issues in a project with filters."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Build JQL query
            jql = f"project = {project_key}"
            
            if status:
                jql += f" AND status = '{status}'"
            
            if issue_type:
                jql += f" AND issuetype = '{issue_type}'"
            
            jql += " ORDER BY created DESC"
            
            # Execute search
            issues = client.search_issues(jql, maxResults=max_results)
            
            # Convert to domain models
            result = []
            for issue in issues:
                jira_issue = self._convert_issue_to_domain(issue, instance_name)
                result.append(jira_issue)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search issues in project {project_key}: {str(e)}")
            raise JiraSearchError(str(e), f"project = {project_key}")

    async def get_custom_field_mappings(self, reverse: bool = False, instance_name: Optional[str] = None) -> List[CustomFieldMapping]:
        """Get custom field mappings."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Fetch all fields
            fields = client.fields()
            
            # Filter for custom fields
            custom_fields = [field for field in fields if field['id'].startswith('customfield_')]
            
            # Convert to domain models
            result = []
            for field in custom_fields:
                mapping = CustomFieldMapping(
                    field_id=field['id'],
                    name=field['name'],
                    description=field.get('description', "")
                )
                result.append(mapping)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get custom field mappings: {str(e)}")
            raise JiraCustomFieldError(str(e))

    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow data for a project and issue type."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get project information
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
                    
        except Exception as e:
            error_msg = str(e).lower()
            if "project" in error_msg and "not found" in error_msg:
                raise JiraProjectNotFound(project_key, instance_name or "default")
            logger.error(f"Failed to get workflow data for {project_key}/{issue_type}: {str(e)}")
            raise

    def _convert_issue_to_domain(self, issue, instance_name: Optional[str] = None) -> JiraIssue:
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
