"""
Atlassian API Time Tracking Adapter implementation.

This module contains the time tracking operations using the atlassian-python-api library.
"""

import asyncio
import logging
import re
from datetime import datetime

from domain.ports import ConfigurationProvider, JiraClientFactory

logger = logging.getLogger(__name__)


class AtlassianTimeFormatValidator:
    """Minimal time format validator - let Jira do the real validation."""

    def validate_time_format(self, time_str: str) -> list[str]:
        """Only validate obviously malformed input - let Jira validate the format."""
        errors = []
        
        if not isinstance(time_str, str) or not time_str.strip():
            errors.append("Time string cannot be empty")
        
        return errors

    def parse_time_to_seconds(self, time_str: str) -> int:
        """Parse Jira time format to seconds."""
        # Handle common Jira time formats: 1d 2h 30m, 2h 30m, 45m, etc.
        time_str = time_str.lower().strip()
        
        # Extract days, hours, minutes, weeks
        weeks = 0
        days = 0
        hours = 0
        minutes = 0
        
        # Match patterns like 1w, 1d, 2h, 30m
        week_match = re.search(r'(\d+)w', time_str)
        day_match = re.search(r'(\d+)d', time_str)
        hour_match = re.search(r'(\d+)h', time_str)
        minute_match = re.search(r'(\d+)m', time_str)
        
        if week_match:
            weeks = int(week_match.group(1))
        if day_match:
            days = int(day_match.group(1))
        if hour_match:
            hours = int(hour_match.group(1))
        if minute_match:
            minutes = int(minute_match.group(1))
        
        # Convert to seconds (assuming 8-hour work day, 5-day work week)
        total_seconds = (weeks * 5 * 8 * 3600) + (days * 8 * 3600) + (hours * 3600) + (minutes * 60)
        
        return total_seconds

    def format_seconds_to_time(self, seconds: int) -> str:
        """Format seconds to Jira time format."""
        if seconds <= 0:
            return "0m"
        
        # Convert seconds to time units (8-hour work day)
        weeks = seconds // (5 * 8 * 3600)
        remaining = seconds % (5 * 8 * 3600)
        
        days = remaining // (8 * 3600)
        remaining = remaining % (8 * 3600)
        
        hours = remaining // 3600
        remaining = remaining % 3600
        
        minutes = remaining // 60
        
        # Build time string
        parts = []
        if weeks > 0:
            parts.append(f"{weeks}w")
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        
        # Ensure we always have at least one part
        if not parts:
            return "0m"
        
        return " ".join(parts)


class AtlassianTimeTrackingAdapter:
    """Adapter for time tracking operations using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider, client_factory: JiraClientFactory):
        self._config_provider = config_provider
        self._client_factory = client_factory
        self._time_validator = AtlassianTimeFormatValidator()

    async def log_work(self, work_log_request, instance_name: str):
        """Log work on an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Convert time string to seconds
            time_seconds = self._time_validator.parse_time_to_seconds(work_log_request.time_spent)
            
            # Use current time if not specified, format for Jira API
            if hasattr(work_log_request, 'started') and work_log_request.started:
                started = work_log_request.started
            else:
                # Format: "yyyy-MM-dd'T'HH:mm:ss.SSSZ" (Jira expects this exact format)
                started = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")
            
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
            time_seconds = self._time_validator.parse_time_to_seconds(work_log_request.time_spent)
            
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
