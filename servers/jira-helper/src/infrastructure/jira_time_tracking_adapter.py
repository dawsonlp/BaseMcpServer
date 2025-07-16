"""
Jira Time Tracking Adapter implementation using BaseJiraAdapter pattern.

This module implements time tracking operations with centralized error handling
and massive boilerplate reduction.
"""

import logging

from domain.exceptions import (
    JiraIssueNotFound,
    TimeTrackingError,
    WorkLogNotFoundError,
)
from domain.models import (
    TimeEstimateResult,
    TimeEstimateUpdate,
    TimeTrackingInfo,
    WorkLog,
    WorkLogRequest,
    WorkLogResult,
)
from domain.ports import ConfigurationProvider, JiraClientFactory, TimeTrackingPort
from infrastructure.base_adapter import BaseJiraAdapter

logger = logging.getLogger(__name__)


class JiraTimeTrackingAdapter(BaseJiraAdapter, TimeTrackingPort):
    """Adapter for time tracking operations using base adapter pattern."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
        super().__init__(client_factory, config_provider)

    async def log_work(self, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Log work on an issue."""
        async def operation(client):
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

        error_mappings = {
            "does not exist": JiraIssueNotFound(work_log_request.issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(work_log_request.issue_key, instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("log_work", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound):
                return WorkLogResult(
                    issue_key=work_log_request.issue_key,
                    logged=False,
                    error=str(e)
                )
            raise

    async def get_work_logs(self, issue_key: str, instance_name: str | None = None) -> list[WorkLog]:
        """Get all work logs for an issue."""
        async def operation(client):
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

        error_mappings = {
            "does not exist": JiraIssueNotFound(issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(issue_key, instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("get_work_logs", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound):
                logger.error(f"Failed to get work logs for issue {issue_key}: {str(e)}")
                return []
            raise

    async def update_work_log(self, work_log_id: str, work_log_request: WorkLogRequest, instance_name: str | None = None) -> WorkLogResult:
        """Update an existing work log."""
        async def operation(client):
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

        error_mappings = {
            "does not exist": JiraIssueNotFound(work_log_request.issue_key, instance_name or "default"),
            "not found": WorkLogNotFoundError(work_log_id, work_log_request.issue_key)
        }

        try:
            return await self._execute_jira_operation("update_work_log", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound | WorkLogNotFoundError):
                return WorkLogResult(
                    issue_key=work_log_request.issue_key,
                    work_log_id=work_log_id,
                    logged=False,
                    error=str(e)
                )
            raise

    async def delete_work_log(self, issue_key: str, work_log_id: str, instance_name: str | None = None) -> bool:
        """Delete a work log entry."""
        async def operation(client):
            # Delete the work log
            response = client._session.delete(
                f"{client._options['server']}/rest/api/2/issue/{issue_key}/worklog/{work_log_id}"
            )

            return response.status_code == 204

        error_mappings = {
            "does not exist": JiraIssueNotFound(issue_key, instance_name or "default"),
            "not found": WorkLogNotFoundError(work_log_id, issue_key)
        }

        try:
            return await self._execute_jira_operation("delete_work_log", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound | WorkLogNotFoundError):
                logger.error(f"Failed to delete work log {work_log_id}: {str(e)}")
                return False
            raise

    async def get_time_tracking_info(self, issue_key: str, instance_name: str | None = None) -> TimeTrackingInfo:
        """Get time tracking information for an issue."""
        async def operation(client):
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

        error_mappings = {
            "does not exist": JiraIssueNotFound(issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(issue_key, instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("get_time_tracking_info", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound):
                raise TimeTrackingError(issue_key, str(e))
            raise

    async def update_time_estimates(self, estimate_update: TimeEstimateUpdate, instance_name: str | None = None) -> TimeEstimateResult:
        """Update time estimates for an issue."""
        async def operation(client):
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

        error_mappings = {
            "does not exist": JiraIssueNotFound(estimate_update.issue_key, instance_name or "default"),
            "not found": JiraIssueNotFound(estimate_update.issue_key, instance_name or "default")
        }

        try:
            return await self._execute_jira_operation("update_time_estimates", operation, instance_name, error_mappings)
        except Exception as e:
            if not isinstance(e, JiraIssueNotFound):
                return TimeEstimateResult(
                    issue_key=estimate_update.issue_key,
                    updated=False,
                    error=str(e)
                )
            raise

    async def is_time_tracking_enabled(self, project_key: str, issue_type: str = None, instance_name: str | None = None) -> bool:
        """Check if time tracking is enabled for a project/issue type."""
        async def operation(client):
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

        try:
            return await self._execute_jira_operation("is_time_tracking_enabled", operation, instance_name)
        except Exception as e:
            logger.error(f"Failed to check time tracking status for {project_key}: {str(e)}")
            # Default to True if we can't determine
            return True
