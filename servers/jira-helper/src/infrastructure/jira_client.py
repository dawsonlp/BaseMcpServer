"""
Jira client implementation for the Jira Helper.

This module implements the JiraRepository port using the Jira Python library,
handling all interactions with the Jira REST API.
"""

import logging
from typing import Any

from jira import JIRA

from domain.exceptions import (
    InvalidJQLError,
    InvalidTimeFormatError,
    JiraAssigneeError,
    JiraAuthenticationError,
    JiraCommentError,
    JiraConnectionError,
    JiraCustomFieldError,
    JiraInstanceNotFound,
    JiraIssueNotFound,
    JiraPermissionError,
    JiraProjectNotFound,
    JiraSearchError,
    JiraTimeoutError,
    JiraTransitionNotAvailable,
    JiraWorkflowError,
    TimeTrackingError,
)
from domain.models import (
    AssigneeChangeRequest,
    CommentAddRequest,
    CustomFieldMapping,
    IssueCreateRequest,
    IssueLink,
    IssueLinkResult,
    IssueTransitionRequest,
    IssueUpdate,
    IssueUpdateResult,
    JiraComment,
    JiraIssue,
    JiraProject,
    SearchQuery,
    SearchResult,
    TimeEstimateResult,
    TimeEstimateUpdate,
    TimeTrackingInfo,
    WorkflowTransition,
    WorkLog,
    WorkLogRequest,
    WorkLogResult,
)
from domain.ports import (
    ConfigurationProvider,
    IssueLinkPort,
    IssueSearchPort,
    IssueUpdatePort,
    JiraClientFactory,
    JiraRepository,
    TimeFormatValidator,
    TimeTrackingPort,
)

logger = logging.getLogger(__name__)


class JiraClientFactoryImpl(JiraClientFactory):
    """Factory for creating Jira clients."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._clients: dict[str, JIRA] = {}

    def create_client(self, instance_name: str | None = None) -> JIRA:
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

    async def get_projects(self, instance_name: str | None = None) -> list[JiraProject]:
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

    async def get_issue(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
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

    async def get_issue_with_comments(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
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

    async def create_issue(self, request: IssueCreateRequest, instance_name: str | None = None) -> JiraIssue:
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

    async def add_comment(self, request: CommentAddRequest, instance_name: str | None = None) -> JiraComment:
        """Add a comment to an issue."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Verify issue exists
            client.issue(request.issue_key)

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

    async def get_available_transitions(self, issue_key: str, instance_name: str | None = None) -> list[WorkflowTransition]:
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

    async def transition_issue(self, request: IssueTransitionRequest, instance_name: str | None = None) -> JiraIssue:
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

    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: str | None = None) -> JiraIssue:
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
        status: str | None = None,
        issue_type: str | None = None,
        max_results: int = 50,
        instance_name: str | None = None
    ) -> list[JiraIssue]:
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

    async def get_custom_field_mappings(self, reverse: bool = False, instance_name: str | None = None) -> list[CustomFieldMapping]:
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

    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: str | None = None) -> dict[str, Any]:
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


class JiraTimeTrackingAdapter(TimeTrackingPort):
    """Adapter for time tracking operations."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider

    async def log_work(self, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Log work on an issue."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Prepare work log data
            work_log_data = {
                'timeSpent': work_log_request.time_spent,
                'comment': work_log_request.comment
            }

            if work_log_request.started:
                work_log_data['started'] = work_log_request.started

            # Handle estimate adjustment
            if work_log_request.adjust_estimate == "new" and work_log_request.new_estimate:
                work_log_data['newEstimate'] = work_log_request.new_estimate
            elif work_log_request.adjust_estimate == "manual" and work_log_request.reduce_by:
                work_log_data['reduceBy'] = work_log_request.reduce_by

            # Log the work using Jira API
            response = client._session.post(
                f"{client._options['server']}/rest/api/2/issue/{work_log_request.issue_key}/worklog",
                json=work_log_data,
                params={'adjustEstimate': work_log_request.adjust_estimate}
            )

            if response.status_code == 201:
                work_log_response = response.json()

                # Get updated issue to check remaining estimate
                updated_issue = client.issue(work_log_request.issue_key)
                remaining_estimate = None
                if hasattr(updated_issue.fields, 'timetracking'):
                    remaining_estimate = getattr(updated_issue.fields.timetracking, 'remainingEstimate', None)

                return WorkLogResult(
                    issue_key=work_log_request.issue_key,
                    work_log_id=work_log_response.get('id'),
                    logged=True,
                    time_spent=work_log_response.get('timeSpent', work_log_request.time_spent),
                    time_spent_seconds=work_log_response.get('timeSpentSeconds', 0),
                    new_remaining_estimate=remaining_estimate
                )
            else:
                error_msg = f"Failed to log work: HTTP {response.status_code}"
                return WorkLogResult(
                    issue_key=work_log_request.issue_key,
                    logged=False,
                    error=error_msg
                )

        except Exception as e:
            logger.error(f"Failed to log work on issue {work_log_request.issue_key}: {str(e)}")
            return WorkLogResult(
                issue_key=work_log_request.issue_key,
                logged=False,
                error=str(e)
            )

    async def get_work_logs(self, issue_key: str, instance_name: str | None = None) -> list[WorkLog]:
        """Get all work logs for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Get work logs from Jira
            response = client._session.get(
                f"{client._options['server']}/rest/api/2/issue/{issue_key}/worklog"
            )

            if response.status_code == 200:
                work_logs_data = response.json()
                work_logs = []

                for wl_data in work_logs_data.get('worklogs', []):
                    work_log = WorkLog(
                        id=wl_data.get('id'),
                        author=wl_data.get('author', {}).get('displayName'),
                        time_spent=wl_data.get('timeSpent', ''),
                        time_spent_seconds=wl_data.get('timeSpentSeconds', 0),
                        comment=wl_data.get('comment', ''),
                        started=wl_data.get('started'),
                        created=wl_data.get('created'),
                        updated=wl_data.get('updated')
                    )
                    work_logs.append(work_log)

                return work_logs
            else:
                logger.error(f"Failed to get work logs for {issue_key}: HTTP {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Failed to get work logs for issue {issue_key}: {str(e)}")
            return []

    async def update_work_log(self, work_log_id: str, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Update an existing work log."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Prepare update data
            update_data = {
                'timeSpent': work_log_request.time_spent,
                'comment': work_log_request.comment
            }

            if work_log_request.started:
                update_data['started'] = work_log_request.started

            # Update the work log
            response = client._session.put(
                f"{client._options['server']}/rest/api/2/issue/{work_log_request.issue_key}/worklog/{work_log_id}",
                json=update_data,
                params={'adjustEstimate': work_log_request.adjust_estimate}
            )

            if response.status_code == 200:
                work_log_response = response.json()
                return WorkLogResult(
                    issue_key=work_log_request.issue_key,
                    work_log_id=work_log_id,
                    logged=True,
                    time_spent=work_log_response.get('timeSpent', work_log_request.time_spent),
                    time_spent_seconds=work_log_response.get('timeSpentSeconds', 0)
                )
            else:
                error_msg = f"Failed to update work log: HTTP {response.status_code}"
                return WorkLogResult(
                    issue_key=work_log_request.issue_key,
                    work_log_id=work_log_id,
                    logged=False,
                    error=error_msg
                )

        except Exception as e:
            logger.error(f"Failed to update work log {work_log_id}: {str(e)}")
            return WorkLogResult(
                issue_key=work_log_request.issue_key,
                work_log_id=work_log_id,
                logged=False,
                error=str(e)
            )

    async def delete_work_log(self, issue_key: str, work_log_id: str, instance_name: str | None = None) -> bool:
        """Delete a work log entry."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Delete the work log
            response = client._session.delete(
                f"{client._options['server']}/rest/api/2/issue/{issue_key}/worklog/{work_log_id}"
            )

            return response.status_code == 204

        except Exception as e:
            logger.error(f"Failed to delete work log {work_log_id}: {str(e)}")
            return False

    async def get_time_tracking_info(self, issue_key: str, instance_name: str | None = None) -> TimeTrackingInfo:
        """Get time tracking information for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(issue_key)

            # Extract time tracking information
            time_tracking = TimeTrackingInfo()

            if hasattr(issue.fields, 'timetracking') and issue.fields.timetracking:
                tt = issue.fields.timetracking
                time_tracking.original_estimate = getattr(tt, 'originalEstimate', None)
                time_tracking.remaining_estimate = getattr(tt, 'remainingEstimate', None)
                time_tracking.time_spent = getattr(tt, 'timeSpent', None)
                time_tracking.original_estimate_seconds = getattr(tt, 'originalEstimateSeconds', 0)
                time_tracking.remaining_estimate_seconds = getattr(tt, 'remainingEstimateSeconds', 0)
                time_tracking.time_spent_seconds = getattr(tt, 'timeSpentSeconds', 0)

            return time_tracking

        except Exception as e:
            logger.error(f"Failed to get time tracking info for issue {issue_key}: {str(e)}")
            raise TimeTrackingError(issue_key, str(e))

    async def update_time_estimates(self, estimate_update: TimeEstimateUpdate, instance_name: str | None = None) -> TimeEstimateResult:
        """Update time estimates for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(estimate_update.issue_key)

            # Prepare update fields
            update_fields = {}
            if estimate_update.original_estimate:
                update_fields['originalEstimate'] = estimate_update.original_estimate
            if estimate_update.remaining_estimate:
                update_fields['remainingEstimate'] = estimate_update.remaining_estimate

            # Update the issue with new time estimates
            if update_fields:
                issue.update(fields={'timetracking': update_fields})

            return TimeEstimateResult(
                issue_key=estimate_update.issue_key,
                updated=True,
                original_estimate=estimate_update.original_estimate,
                remaining_estimate=estimate_update.remaining_estimate
            )

        except Exception as e:
            logger.error(f"Failed to update time estimates for issue {estimate_update.issue_key}: {str(e)}")
            return TimeEstimateResult(
                issue_key=estimate_update.issue_key,
                updated=False,
                error=str(e)
            )

    async def validate_time_format(self, time_string: str) -> list[str]:
        """Validate time format (e.g., '2h 30m', '1d')."""
        # Basic validation for Jira time format
        validation_errors = []

        if not time_string or not time_string.strip():
            validation_errors.append("Time string cannot be empty")
            return validation_errors

        # Check for valid time units
        valid_units = ['w', 'd', 'h', 'm']
        time_parts = time_string.strip().split()

        for part in time_parts:
            if not part:
                continue

            # Check if part ends with a valid unit
            if not any(part.endswith(unit) for unit in valid_units):
                validation_errors.append(f"Invalid time unit in '{part}'. Valid units: w, d, h, m")
                continue

            # Check if the numeric part is valid
            numeric_part = part[:-1]
            try:
                float(numeric_part)
            except ValueError:
                validation_errors.append(f"Invalid numeric value in '{part}'")

        return validation_errors

    async def is_time_tracking_enabled(self, project_key: str, issue_type: str = None, instance_name: str | None = None) -> bool:
        """Check if time tracking is enabled for a project/issue type."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Get a sample issue from the project to check time tracking
            jql = f"project = {project_key}"
            if issue_type:
                jql += f" AND issuetype = '{issue_type}'"
            jql += " ORDER BY created DESC"

            issues = client.search_issues(jql, maxResults=1)

            if issues:
                issue = issues[0]
                # Check if the issue has time tracking fields
                return hasattr(issue.fields, 'timetracking')
            else:
                # No issues found, assume time tracking is available
                return True

        except Exception as e:
            logger.error(f"Failed to check time tracking status for {project_key}: {str(e)}")
            # Default to True if we can't determine
            return True


class JiraTimeFormatValidator(TimeFormatValidator):
    """Validator for Jira time format strings."""

    def validate_time_format(self, time_string: str) -> list[str]:
        """Validate time format. Returns list of validation errors."""
        validation_errors = []

        if not time_string or not time_string.strip():
            validation_errors.append("Time string cannot be empty")
            return validation_errors

        # Check for valid time units
        valid_units = ['w', 'd', 'h', 'm']
        time_parts = time_string.strip().split()

        if not time_parts:
            validation_errors.append("Time string cannot be empty")
            return validation_errors

        for part in time_parts:
            if not part:
                continue

            # Check if part ends with a valid unit
            if not any(part.endswith(unit) for unit in valid_units):
                validation_errors.append(f"Invalid time unit in '{part}'. Valid units: w, d, h, m")
                continue

            # Check if the numeric part is valid
            numeric_part = part[:-1]
            try:
                value = float(numeric_part)
                if value < 0:
                    validation_errors.append(f"Time value cannot be negative in '{part}'")
            except ValueError:
                validation_errors.append(f"Invalid numeric value in '{part}'")

        return validation_errors

    def parse_time_to_seconds(self, time_string: str) -> int:
        """Parse time string to seconds."""
        # First validate
        errors = self.validate_time_format(time_string)
        if errors:
            raise InvalidTimeFormatError(time_string, "; ".join(errors))

        total_seconds = 0
        time_parts = time_string.strip().split()

        # Time unit conversions (assuming 8-hour days, 5-day weeks)
        unit_to_seconds = {
            'm': 60,           # minutes
            'h': 3600,         # hours
            'd': 8 * 3600,     # days (8 hours)
            'w': 5 * 8 * 3600  # weeks (5 days * 8 hours)
        }

        for part in time_parts:
            if not part:
                continue

            unit = part[-1]
            numeric_part = part[:-1]

            try:
                value = float(numeric_part)
                total_seconds += int(value * unit_to_seconds[unit])
            except (ValueError, KeyError):
                raise InvalidTimeFormatError(time_string, f"Invalid time part: {part}")

        return total_seconds

    def format_seconds_to_time(self, seconds: int) -> str:
        """Format seconds to Jira time format."""
        if seconds < 0:
            raise ValueError("Seconds cannot be negative")

        if seconds == 0:
            return "0m"

        # Convert to time units (assuming 8-hour days, 5-day weeks)
        weeks = seconds // (5 * 8 * 3600)
        seconds %= (5 * 8 * 3600)

        days = seconds // (8 * 3600)
        seconds %= (8 * 3600)

        hours = seconds // 3600
        seconds %= 3600

        minutes = seconds // 60

        parts = []
        if weeks > 0:
            parts.append(f"{weeks}w")
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")

        return " ".join(parts) if parts else "0m"

    def get_supported_time_units(self) -> list[str]:
        """Get list of supported time units."""
        return ['m', 'h', 'd', 'w']

    def normalize_time_format(self, time_string: str) -> str:
        """Normalize time format to standard Jira format."""
        # Parse to seconds and format back
        try:
            seconds = self.parse_time_to_seconds(time_string)
            return self.format_seconds_to_time(seconds)
        except Exception:
            # If parsing fails, return original string
            return time_string


class JiraLinkTypeMapper:
    """Maps domain link types to Jira link types."""

    def __init__(self, client_factory: JiraClientFactory):
        self._client_factory = client_factory
        self._link_type_cache = {}

    def map_to_jira_link_type(self, domain_link_type: str, instance_name: str | None = None) -> str:
        """Map a domain link type to the corresponding Jira link type."""
        # Default mapping
        mapping = {
            'Epic-Story': 'Epic-Story',
            'Parent-Child': 'Subtask',
            'Blocks': 'Blocks',
            'Clones': 'Cloners',
            'Duplicates': 'Duplicate',
            'Relates': 'Relates'
        }

        return mapping.get(domain_link_type, 'Relates')

    def map_from_jira_link_type(self, jira_link_type: str, instance_name: str | None = None) -> str:
        """Map a Jira link type to the corresponding domain link type."""
        # Reverse mapping
        reverse_mapping = {
            'Epic-Story': 'Epic-Story',
            'Subtask': 'Parent-Child',
            'Blocks': 'Blocks',
            'Cloners': 'Clones',
            'Duplicate': 'Duplicates',
            'Relates': 'Relates'
        }

        return reverse_mapping.get(jira_link_type, 'Relates')

    def get_supported_link_types(self, instance_name: str | None = None) -> dict[str, str]:
        """Get mapping of supported link types (domain -> jira)."""
        return {
            'Epic-Story': 'Epic-Story',
            'Parent-Child': 'Subtask',
            'Blocks': 'Blocks',
            'Clones': 'Cloners',
            'Duplicates': 'Duplicate',
            'Relates': 'Relates'
        }


class JiraJQLValidator:
    """Validates JQL queries for syntax and security."""

    def validate_syntax(self, jql: str) -> list[str]:
        """Validate JQL syntax. Returns list of syntax errors."""
        errors = []

        if not jql or not jql.strip():
            errors.append("JQL query cannot be empty")
            return errors

        # Basic syntax checks
        jql = jql.strip()

        # Check for balanced quotes
        single_quotes = jql.count("'")
        double_quotes = jql.count('"')

        if single_quotes % 2 != 0:
            errors.append("Unmatched single quotes in JQL")

        if double_quotes % 2 != 0:
            errors.append("Unmatched double quotes in JQL")

        # Check for balanced parentheses
        open_parens = jql.count("(")
        close_parens = jql.count(")")

        if open_parens != close_parens:
            errors.append("Unmatched parentheses in JQL")

        return errors

    def check_security(self, jql: str) -> list[str]:
        """Check JQL for security issues. Returns list of security concerns."""
        security_issues = []

        jql_lower = jql.lower()

        # Check for potentially dangerous functions or keywords
        dangerous_patterns = [
            'javascript:',
            '<script',
            'eval(',
            'exec(',
            'system(',
            'cmd(',
            'shell('
        ]

        for pattern in dangerous_patterns:
            if pattern in jql_lower:
                security_issues.append(f"Potentially unsafe pattern detected: {pattern}")

        # Check for excessively broad queries that might impact performance
        if 'order by' not in jql_lower and 'limit' not in jql_lower:
            if not any(field in jql_lower for field in ['project =', 'key =', 'id =']):
                security_issues.append("Query may be too broad - consider adding project or key filters")

        return security_issues

    def sanitize_jql(self, jql: str) -> str:
        """Sanitize JQL query to remove potentially harmful content."""
        if not jql:
            return ""

        # Remove potentially dangerous patterns
        dangerous_patterns = [
            'javascript:',
            '<script',
            '</script>',
            'eval(',
            'exec(',
            'system(',
            'cmd(',
            'shell('
        ]

        sanitized = jql
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, '')

        return sanitized.strip()

    def validate_limits(self, max_results: int, start_at: int) -> list[str]:
        """Validate search limits. Returns list of limit violations."""
        errors = []

        if max_results <= 0:
            errors.append("Max results must be greater than 0")

        if max_results > 1000:
            errors.append("Max results cannot exceed 1000")

        if start_at < 0:
            errors.append("Start at cannot be negative")

        return errors


class JiraIssueUpdateAdapter(IssueUpdatePort):
    """Adapter for issue update operations."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider

    async def update_issue(self, update_request: IssueUpdate, instance_name: str | None = None) -> IssueUpdateResult:
        """Update an existing issue with new field values."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(update_request.issue_key)

            # Prepare update fields
            update_fields = {}
            updated_field_names = []

            for field_name, field_value in update_request.fields.items():
                if field_name == 'summary':
                    update_fields['summary'] = field_value
                    updated_field_names.append('summary')
                elif field_name == 'description':
                    update_fields['description'] = field_value
                    updated_field_names.append('description')
                elif field_name == 'priority':
                    update_fields['priority'] = {'name': field_value}
                    updated_field_names.append('priority')
                elif field_name == 'assignee':
                    if field_value:
                        update_fields['assignee'] = {'name': field_value}
                    else:
                        update_fields['assignee'] = None
                    updated_field_names.append('assignee')
                elif field_name == 'labels':
                    update_fields['labels'] = field_value if field_value else []
                    updated_field_names.append('labels')

            # Update the issue
            issue.update(fields=update_fields)

            return IssueUpdateResult(
                issue_key=update_request.issue_key,
                updated=True,
                updated_fields=updated_field_names
            )

        except Exception as e:
            logger.error(f"Failed to update issue {update_request.issue_key}: {str(e)}")
            return IssueUpdateResult(
                issue_key=update_request.issue_key,
                updated=False,
                error=str(e)
            )

    async def validate_update_fields(self, issue_key: str, fields: dict[str, Any], instance_name: str | None = None) -> list[str]:
        """Validate that the specified fields can be updated."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(issue_key)

            # Get editable fields for this issue
            editable_fields = client.editmeta(issue)
            available_fields = set(editable_fields.get('fields', {}).keys())

            # Map domain field names to Jira field names
            field_mapping = {
                'summary': 'summary',
                'description': 'description',
                'priority': 'priority',
                'assignee': 'assignee',
                'labels': 'labels'
            }

            validation_errors = []
            for field_name in fields.keys():
                jira_field_name = field_mapping.get(field_name, field_name)
                if jira_field_name not in available_fields:
                    validation_errors.append(f"Field '{field_name}' cannot be updated for this issue")

            return validation_errors

        except Exception as e:
            logger.error(f"Failed to validate update fields for {issue_key}: {str(e)}")
            return [f"Could not validate fields: {str(e)}"]

    async def get_updatable_fields(self, issue_key: str, instance_name: str | None = None) -> list[str]:
        """Get list of fields that can be updated for the given issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(issue_key)

            # Get editable fields for this issue
            editable_fields = client.editmeta(issue)
            available_fields = list(editable_fields.get('fields', {}).keys())

            # Map Jira field names back to domain field names
            reverse_mapping = {
                'summary': 'summary',
                'description': 'description',
                'priority': 'priority',
                'assignee': 'assignee',
                'labels': 'labels'
            }

            domain_fields = []
            for jira_field in available_fields:
                domain_field = reverse_mapping.get(jira_field)
                if domain_field:
                    domain_fields.append(domain_field)

            return domain_fields

        except Exception as e:
            logger.error(f"Failed to get updatable fields for {issue_key}: {str(e)}")
            return []


class JiraIssueLinkAdapter(IssueLinkPort):
    """Adapter for issue linking operations."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider

    async def create_link(self, issue_link: IssueLink, instance_name: str | None = None) -> IssueLinkResult:
        """Create a link between two issues."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Map domain link types to Jira link types
            link_type_mapping = {
                'Epic-Story': 'Epic-Story',
                'Parent-Child': 'Subtask',
                'Blocks': 'Blocks',
                'Clones': 'Cloners',
                'Duplicates': 'Duplicate',
                'Relates': 'Relates'
            }

            jira_link_type = link_type_mapping.get(issue_link.link_type, 'Relates')

            # Create the link
            link_data = {
                'type': {'name': jira_link_type},
                'inwardIssue': {'key': issue_link.target_issue},
                'outwardIssue': {'key': issue_link.source_issue}
            }

            if issue_link.direction == 'inward':
                link_data['inwardIssue'], link_data['outwardIssue'] = link_data['outwardIssue'], link_data['inwardIssue']

            # Use the Jira client to create the link
            response = client._session.post(
                f"{client._options['server']}/rest/api/2/issueLink",
                json=link_data
            )

            if response.status_code == 201:
                # Link created successfully
                return IssueLinkResult(
                    source_issue=issue_link.source_issue,
                    target_issue=issue_link.target_issue,
                    link_type=issue_link.link_type,
                    created=True,
                    link_id=None  # Jira doesn't return link ID in create response
                )
            else:
                error_msg = f"Failed to create link: HTTP {response.status_code}"
                return IssueLinkResult(
                    source_issue=issue_link.source_issue,
                    target_issue=issue_link.target_issue,
                    link_type=issue_link.link_type,
                    created=False,
                    error=error_msg
                )

        except Exception as e:
            logger.error(f"Failed to create link between {issue_link.source_issue} and {issue_link.target_issue}: {str(e)}")
            return IssueLinkResult(
                source_issue=issue_link.source_issue,
                target_issue=issue_link.target_issue,
                link_type=issue_link.link_type,
                created=False,
                error=str(e)
            )

    async def get_links(self, issue_key: str, instance_name: str | None = None) -> list[IssueLink]:
        """Get all links for a specific issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue = client.issue(issue_key, expand='issuelinks')

            links = []
            if hasattr(issue.fields, 'issuelinks'):
                for link in issue.fields.issuelinks:
                    # Determine direction and related issue
                    if hasattr(link, 'outwardIssue'):
                        # This issue is the source
                        issue_link = IssueLink(
                            link_type=link.type.name,
                            source_issue=issue_key,
                            target_issue=link.outwardIssue.key,
                            direction='outward',
                            link_id=getattr(link, 'id', None)
                        )
                    elif hasattr(link, 'inwardIssue'):
                        # This issue is the target
                        issue_link = IssueLink(
                            link_type=link.type.name,
                            source_issue=link.inwardIssue.key,
                            target_issue=issue_key,
                            direction='inward',
                            link_id=getattr(link, 'id', None)
                        )
                    else:
                        continue

                    links.append(issue_link)

            return links

        except Exception as e:
            logger.error(f"Failed to get links for issue {issue_key}: {str(e)}")
            return []

    async def remove_link(self, link_id: str, instance_name: str | None = None) -> bool:
        """Remove a link between issues."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Use the Jira client to delete the link
            response = client._session.delete(
                f"{client._options['server']}/rest/api/2/issueLink/{link_id}"
            )

            return response.status_code == 204

        except Exception as e:
            logger.error(f"Failed to remove link {link_id}: {str(e)}")
            return False

    async def get_available_link_types(self, instance_name: str | None = None) -> list[str]:
        """Get available link types for the Jira instance."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Get link types from Jira
            response = client._session.get(
                f"{client._options['server']}/rest/api/2/issueLinkType"
            )

            if response.status_code == 200:
                link_types_data = response.json()
                link_types = [lt['name'] for lt in link_types_data.get('issueLinkTypes', [])]
                return link_types
            else:
                return ['Relates', 'Blocks', 'Cloners', 'Duplicate']  # Default types

        except Exception as e:
            logger.error(f"Failed to get available link types: {str(e)}")
            return ['Relates', 'Blocks', 'Cloners', 'Duplicate']  # Default types

    async def validate_link(self, issue_link: IssueLink, instance_name: str | None = None) -> list[str]:
        """Validate a link before creation."""
        validation_errors = []

        try:
            client = self._client_factory.create_client(instance_name)

            # Check if both issues exist
            try:
                client.issue(issue_link.source_issue)
            except Exception:
                validation_errors.append(f"Source issue '{issue_link.source_issue}' does not exist")

            try:
                client.issue(issue_link.target_issue)
            except Exception:
                validation_errors.append(f"Target issue '{issue_link.target_issue}' does not exist")

            # Check if link type is available
            available_types = await self.get_available_link_types(instance_name)
            if issue_link.link_type not in available_types:
                validation_errors.append(f"Link type '{issue_link.link_type}' is not available")

        except Exception as e:
            validation_errors.append(f"Could not validate link: {str(e)}")

        return validation_errors


class JiraSearchAdapter(IssueSearchPort):
    """Adapter for JQL search operations."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider

    async def search_issues(self, query: SearchQuery, instance_name: str | None = None) -> SearchResult:
        """Execute a JQL search query."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Execute the search
            issues = client.search_issues(
                query.jql,
                startAt=query.start_at,
                maxResults=query.max_results,
                fields=query.fields
            )

            # Convert issues to domain models
            domain_issues = []
            for issue in issues:
                domain_issue = self._convert_issue_to_domain(issue, instance_name)
                domain_issues.append(domain_issue)

            return SearchResult(
                jql=query.jql,
                total_results=issues.total,
                start_at=query.start_at,
                max_results=query.max_results,
                issues=domain_issues
            )

        except Exception as e:
            logger.error(f"Failed to execute JQL search: {str(e)}")
            raise InvalidJQLError(query.jql, str(e))

    async def validate_jql(self, jql: str, instance_name: str | None = None) -> list[str]:
        """Validate JQL syntax."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Try to parse the JQL by doing a search with maxResults=0
            client.search_issues(jql, maxResults=0)
            return []  # No errors

        except Exception as e:
            error_msg = str(e)
            if "JQL" in error_msg or "syntax" in error_msg.lower():
                return [f"JQL syntax error: {error_msg}"]
            else:
                return [f"JQL validation error: {error_msg}"]

    async def get_search_suggestions(self, partial_jql: str, instance_name: str | None = None) -> list[str]:
        """Get JQL completion suggestions for partial queries."""
        # This is a simplified implementation - Jira's autocomplete API is complex
        suggestions = []

        # Basic field suggestions
        if not partial_jql or partial_jql.endswith(' '):
            suggestions.extend([
                'project =', 'status =', 'assignee =', 'reporter =',
                'priority =', 'type =', 'created >=', 'updated >=',
                'summary ~', 'description ~'
            ])

        # Operator suggestions
        if any(field in partial_jql for field in ['project', 'status', 'assignee', 'priority', 'type']):
            if partial_jql.endswith('='):
                suggestions.append(' ')
            elif partial_jql.endswith(' '):
                suggestions.extend(['AND', 'OR', 'ORDER BY'])

        return suggestions[:10]  # Limit to 10 suggestions

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
