"""
Use cases for the Jira Helper application.

This module contains use case implementations that orchestrate domain services
to fulfill specific business requirements. Each use case represents a single
business operation that can be performed by the application.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from domain.models import (
    JiraInstance, JiraProject, JiraIssue, JiraComment, WorkflowTransition,
    CustomFieldMapping, IssueCreateRequest, IssueTransitionRequest,
    AssigneeChangeRequest, CommentAddRequest, IssueUpdate, IssueLink,
    SearchQuery, WorkLogRequest, TimeEstimateUpdate, IssueCreateWithLinksRequest
)
from domain.services import (
    IssueService, WorkflowService, ProjectService, VisualizationService,
    InstanceService, IssueUpdateService, IssueLinkService, SearchService,
    TimeTrackingService
)
from domain.exceptions import JiraValidationError


@dataclass
class UseCaseResult:
    """Base result class for use cases."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ListProjectsUseCase:
    """Use case for listing projects in a Jira instance."""

    def __init__(self, project_service: ProjectService):
        self._project_service = project_service

    async def execute(self, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the list projects use case."""
        try:
            projects = await self._project_service.get_projects(instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "projects": [
                        {
                            "key": project.key,
                            "name": project.name,
                            "id": project.id,
                            "lead_name": project.lead_name,
                            "lead_email": project.lead_email,
                            "url": project.url
                        }
                        for project in projects
                    ],
                    "count": len(projects),
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"instance_name": instance_name}
            )


class GetIssueDetailsUseCase:
    """Use case for getting issue details."""

    def __init__(self, issue_service: IssueService):
        self._issue_service = issue_service

    async def execute(self, issue_key: str, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the get issue details use case."""
        try:
            issue = await self._issue_service.get_issue(issue_key, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "issue": {
                        "key": issue.key,
                        "id": issue.id,
                        "summary": issue.summary,
                        "description": issue.description,
                        "status": issue.status,
                        "issue_type": issue.issue_type,
                        "priority": issue.priority,
                        "assignee": issue.assignee,
                        "reporter": issue.reporter,
                        "created": issue.created,
                        "updated": issue.updated,
                        "components": issue.components,
                        "labels": issue.labels,
                        "url": issue.url
                    },
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "instance_name": instance_name}
            )


class GetFullIssueDetailsUseCase:
    """Use case for getting full issue details with comments."""

    def __init__(self, issue_service: IssueService):
        self._issue_service = issue_service

    async def execute(
        self, 
        issue_key: str, 
        raw_data: bool = False, 
        format: str = "formatted",
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the get full issue details use case."""
        try:
            issue = await self._issue_service.get_issue_with_comments(issue_key, instance_name)
            
            # Format comments
            formatted_comments = [
                {
                    "id": comment.id,
                    "author_name": comment.author_name,
                    "author_key": comment.author_key,
                    "body": comment.body,
                    "created": comment.created,
                    "updated": comment.updated
                }
                for comment in issue.comments
            ]
            
            if raw_data:
                return UseCaseResult(
                    success=True,
                    data={
                        "issue": issue.__dict__,
                        "comments": formatted_comments,
                        "comment_count": len(formatted_comments)
                    }
                )
            
            if format == "summary":
                return UseCaseResult(
                    success=True,
                    data={
                        "issue": {
                            "key": issue.key,
                            "id": issue.id,
                            "summary": issue.summary,
                            "status": issue.status,
                            "priority": issue.priority,
                            "assignee": issue.assignee,
                            "reporter": issue.reporter,
                            "created": issue.created,
                            "updated": issue.updated
                        },
                        "description": issue.description,
                        "components": issue.components,
                        "labels": issue.labels,
                        "comments": formatted_comments,
                        "comment_count": len(formatted_comments)
                    }
                )
            else:  # formatted
                return UseCaseResult(
                    success=True,
                    data={
                        "issue": {
                            "key": issue.key,
                            "id": issue.id,
                            "summary": issue.summary,
                            "status": issue.status,
                            "priority": issue.priority,
                            "assignee": issue.assignee,
                            "reporter": issue.reporter,
                            "created": issue.created,
                            "updated": issue.updated
                        },
                        "description": issue.description,
                        "custom_fields": issue.custom_fields,
                        "components": issue.components,
                        "labels": issue.labels,
                        "comments": formatted_comments,
                        "comment_count": len(formatted_comments)
                    }
                )
                
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "instance_name": instance_name}
            )


class CreateIssueUseCase:
    """Use case for creating a new issue."""

    def __init__(self, issue_service: IssueService):
        self._issue_service = issue_service

    async def execute(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Story",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the create issue use case."""
        try:
            request = IssueCreateRequest(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                priority=priority,
                assignee=assignee,
                labels=labels or []
            )
            
            issue = await self._issue_service.create_issue(request, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "created": True,
                    "key": issue.key,
                    "id": issue.id,
                    "url": issue.url
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "project_key": project_key,
                    "summary": summary,
                    "instance_name": instance_name
                }
            )


class AddCommentUseCase:
    """Use case for adding a comment to an issue."""

    def __init__(self, issue_service: IssueService):
        self._issue_service = issue_service

    async def execute(self, issue_key: str, comment: str, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the add comment use case."""
        try:
            request = CommentAddRequest(issue_key=issue_key, comment=comment)
            comment_obj = await self._issue_service.add_comment(request, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "added": True,
                    "issue_key": issue_key,
                    "comment_id": comment_obj.id,
                    "comment_author": comment_obj.author_name,
                    "comment_body": comment_obj.body
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "instance_name": instance_name}
            )


class TransitionIssueUseCase:
    """Use case for transitioning an issue through workflow."""

    def __init__(self, workflow_service: WorkflowService):
        self._workflow_service = workflow_service

    async def execute(
        self,
        issue_key: str,
        transition_name: str,
        comment: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the transition issue use case."""
        try:
            request = IssueTransitionRequest(
                issue_key=issue_key,
                transition_name=transition_name,
                comment=comment
            )
            
            updated_issue = await self._workflow_service.transition_issue(request, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "success": True,
                    "issue_key": issue_key,
                    "transition_executed": transition_name,
                    "new_status": updated_issue.status,
                    "comment_added": bool(comment),
                    "url": updated_issue.url,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "issue_key": issue_key,
                    "transition_name": transition_name,
                    "instance_name": instance_name
                }
            )


class GetIssueTransitionsUseCase:
    """Use case for getting available transitions for an issue."""

    def __init__(self, workflow_service: WorkflowService):
        self._workflow_service = workflow_service

    async def execute(self, issue_key: str, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the get issue transitions use case."""
        try:
            transitions = await self._workflow_service.get_available_transitions(issue_key, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "issue_key": issue_key,
                    "available_transitions": [
                        {
                            "id": transition.id,
                            "name": transition.name,
                            "to_status": transition.to_status
                        }
                        for transition in transitions
                    ],
                    "transition_count": len(transitions),
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "instance_name": instance_name}
            )


class ChangeAssigneeUseCase:
    """Use case for changing an issue's assignee."""

    def __init__(self, workflow_service: WorkflowService):
        self._workflow_service = workflow_service

    async def execute(
        self,
        issue_key: str,
        assignee: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the change assignee use case."""
        try:
            request = AssigneeChangeRequest(issue_key=issue_key, assignee=assignee)
            updated_issue = await self._workflow_service.change_assignee(request, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "success": True,
                    "issue_key": issue_key,
                    "new_assignee": updated_issue.assignee,
                    "url": updated_issue.url,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "assignee": assignee, "instance_name": instance_name}
            )


class ListProjectTicketsUseCase:
    """Use case for listing tickets in a project."""

    def __init__(self, issue_service: IssueService):
        self._issue_service = issue_service

    async def execute(
        self,
        project_key: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the list project tickets use case."""
        try:
            issues = await self._issue_service.search_issues(
                project_key, status, issue_type, max_results, instance_name
            )
            
            return UseCaseResult(
                success=True,
                data={
                    "project": project_key,
                    "issues_count": len(issues),
                    "issues": [
                        {
                            "key": issue.key,
                            "summary": issue.summary,
                            "status": issue.status,
                            "issue_type": issue.issue_type,
                            "priority": issue.priority,
                            "assignee": issue.assignee,
                            "created": issue.created,
                            "updated": issue.updated,
                            "url": issue.url
                        }
                        for issue in issues
                    ],
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "project_key": project_key,
                    "status": status,
                    "issue_type": issue_type,
                    "instance_name": instance_name
                }
            )


class GetCustomFieldMappingsUseCase:
    """Use case for getting custom field mappings."""

    def __init__(self, project_service: ProjectService):
        self._project_service = project_service

    async def execute(self, reverse: bool = False, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the get custom field mappings use case."""
        try:
            mappings = await self._project_service.get_custom_field_mappings(reverse, instance_name)
            
            if reverse:
                # name -> [field_id, description]
                mappings_dict = {
                    mapping.name: [mapping.field_id, mapping.description]
                    for mapping in mappings
                }
                mapping_direction = "name_to_id"
            else:
                # field_id -> [name, description]
                mappings_dict = {
                    mapping.field_id: [mapping.name, mapping.description]
                    for mapping in mappings
                }
                mapping_direction = "id_to_name"
            
            return UseCaseResult(
                success=True,
                data={
                    "mappings": mappings_dict,
                    "count": len(mappings_dict),
                    "mapping_direction": mapping_direction
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"reverse": reverse, "instance_name": instance_name}
            )


class GenerateWorkflowGraphUseCase:
    """Use case for generating workflow graphs."""

    def __init__(self, visualization_service: VisualizationService):
        self._visualization_service = visualization_service

    async def execute(
        self,
        project_key: str,
        issue_type: str = "Story",
        format: str = "svg",
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the generate workflow graph use case."""
        try:
            result = await self._visualization_service.generate_workflow_graph(
                project_key, issue_type, format, instance_name
            )
            
            return UseCaseResult(success=True, data=result)
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "project_key": project_key,
                    "issue_type": issue_type,
                    "format": format,
                    "instance_name": instance_name
                }
            )


class ListInstancesUseCase:
    """Use case for listing all configured Jira instances."""

    def __init__(self, instance_service: InstanceService):
        self._instance_service = instance_service

    async def execute(self) -> UseCaseResult:
        """Execute the list instances use case."""
        try:
            instances = self._instance_service.get_instances()
            default_instance = self._instance_service.get_default_instance()
            
            return UseCaseResult(
                success=True,
                data={
                    "instances": [
                        {
                            "name": instance.name,
                            "url": instance.url,
                            "user": instance.user,
                            "description": instance.description,
                            "is_default": instance.is_default
                        }
                        for instance in instances
                    ],
                    "count": len(instances),
                    "default_instance": default_instance.name if default_instance else None
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e)
            )


class UpdateIssueUseCase:
    """Use case for updating an existing issue."""

    def __init__(self, issue_update_service: IssueUpdateService):
        self._issue_update_service = issue_update_service

    async def execute(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the update issue use case."""
        try:
            update_request = IssueUpdate(
                issue_key=issue_key,
                summary=summary,
                description=description,
                priority=priority,
                assignee=assignee,
                labels=labels
            )
            
            result = await self._issue_update_service.update_issue(update_request, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "updated": result.updated,
                    "issue_key": result.issue_key,
                    "updated_fields": result.updated_fields,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "issue_key": issue_key,
                    "instance_name": instance_name
                }
            )


class CreateIssueLinkUseCase:
    """Use case for creating links between issues."""

    def __init__(self, issue_link_service: IssueLinkService):
        self._issue_link_service = issue_link_service

    async def execute(
        self,
        source_issue: str,
        target_issue: str,
        link_type: str,
        direction: str = "outward",
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the create issue link use case."""
        try:
            issue_link = IssueLink(
                link_type=link_type,
                source_issue=source_issue,
                target_issue=target_issue,
                direction=direction
            )
            
            result = await self._issue_link_service.create_link(issue_link, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "created": result.created,
                    "source_issue": result.source_issue,
                    "target_issue": result.target_issue,
                    "link_type": result.link_type,
                    "link_id": result.link_id,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "source_issue": source_issue,
                    "target_issue": target_issue,
                    "link_type": link_type,
                    "instance_name": instance_name
                }
            )


class CreateEpicStoryLinkUseCase:
    """Use case for creating Epic-Story links."""

    def __init__(self, issue_link_service: IssueLinkService):
        self._issue_link_service = issue_link_service

    async def execute(
        self,
        epic_key: str,
        story_key: str,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the create Epic-Story link use case."""
        try:
            result = await self._issue_link_service.create_epic_story_link(epic_key, story_key, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "created": result.created,
                    "epic_key": epic_key,
                    "story_key": story_key,
                    "link_type": result.link_type,
                    "link_id": result.link_id,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "epic_key": epic_key,
                    "story_key": story_key,
                    "instance_name": instance_name
                }
            )


class GetIssueLinksUseCase:
    """Use case for getting all links for an issue."""

    def __init__(self, issue_link_service: IssueLinkService):
        self._issue_link_service = issue_link_service

    async def execute(self, issue_key: str, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the get issue links use case."""
        try:
            links = await self._issue_link_service.get_issue_links(issue_key, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "issue_key": issue_key,
                    "links": [
                        {
                            "link_id": link.link_id,
                            "link_type": link.link_type,
                            "source_issue": link.source_issue,
                            "target_issue": link.target_issue,
                            "direction": link.direction
                        }
                        for link in links
                    ],
                    "link_count": len(links),
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "instance_name": instance_name}
            )


class SearchIssuesUseCase:
    """Use case for executing JQL searches."""

    def __init__(self, search_service: SearchService):
        self._search_service = search_service

    async def execute(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        fields: Optional[List[str]] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the search issues use case."""
        try:
            search_query = SearchQuery(
                jql=jql,
                max_results=max_results,
                start_at=start_at,
                fields=fields
            )
            
            result = await self._search_service.search_issues(search_query, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "jql": result.jql,
                    "total_results": result.total_results,
                    "start_at": result.start_at,
                    "max_results": result.max_results,
                    "returned_results": len(result.issues),
                    "has_more": result.has_more_results(),
                    "issues": [
                        {
                            "key": issue.key,
                            "id": issue.id,
                            "summary": issue.summary,
                            "status": issue.status,
                            "issue_type": issue.issue_type,
                            "priority": issue.priority,
                            "assignee": issue.assignee,
                            "reporter": issue.reporter,
                            "created": issue.created,
                            "updated": issue.updated,
                            "url": issue.url
                        }
                        for issue in result.issues
                    ],
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "jql": jql,
                    "max_results": max_results,
                    "start_at": start_at,
                    "instance_name": instance_name
                }
            )


class LogWorkUseCase:
    """Use case for logging work on an issue."""

    def __init__(self, time_tracking_service: TimeTrackingService):
        self._time_tracking_service = time_tracking_service

    async def execute(
        self,
        issue_key: str,
        time_spent: str,
        comment: str = "",
        started: Optional[str] = None,
        adjust_estimate: str = "auto",
        new_estimate: Optional[str] = None,
        reduce_by: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the log work use case."""
        try:
            work_log_request = WorkLogRequest(
                issue_key=issue_key,
                time_spent=time_spent,
                comment=comment,
                started=started,
                adjust_estimate=adjust_estimate,
                new_estimate=new_estimate,
                reduce_by=reduce_by
            )
            
            result = await self._time_tracking_service.log_work(work_log_request, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "logged": result.logged,
                    "issue_key": result.issue_key,
                    "work_log_id": result.work_log_id,
                    "time_spent": result.time_spent,
                    "time_spent_seconds": result.time_spent_seconds,
                    "time_spent_hours": result.get_time_in_hours(),
                    "new_remaining_estimate": result.new_remaining_estimate,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "issue_key": issue_key,
                    "time_spent": time_spent,
                    "instance_name": instance_name
                }
            )


class GetWorkLogsUseCase:
    """Use case for getting work logs for an issue."""

    def __init__(self, time_tracking_service: TimeTrackingService):
        self._time_tracking_service = time_tracking_service

    async def execute(self, issue_key: str, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the get work logs use case."""
        try:
            work_logs = await self._time_tracking_service.get_work_logs(issue_key, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "issue_key": issue_key,
                    "work_logs": [
                        {
                            "id": log.id,
                            "author": log.author,
                            "time_spent": log.time_spent,
                            "time_spent_seconds": log.time_spent_seconds,
                            "time_spent_hours": log.get_time_in_hours(),
                            "time_spent_minutes": log.get_time_in_minutes(),
                            "comment": log.comment,
                            "started": log.started,
                            "created": log.created,
                            "updated": log.updated
                        }
                        for log in work_logs
                    ],
                    "work_log_count": len(work_logs),
                    "total_time_seconds": sum(log.time_spent_seconds for log in work_logs),
                    "total_time_hours": sum(log.get_time_in_hours() for log in work_logs),
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "instance_name": instance_name}
            )


class GetTimeTrackingInfoUseCase:
    """Use case for getting time tracking information for an issue."""

    def __init__(self, time_tracking_service: TimeTrackingService):
        self._time_tracking_service = time_tracking_service

    async def execute(self, issue_key: str, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the get time tracking info use case."""
        try:
            time_info = await self._time_tracking_service.get_time_tracking_info(issue_key, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "issue_key": issue_key,
                    "original_estimate": time_info.original_estimate,
                    "remaining_estimate": time_info.remaining_estimate,
                    "time_spent": time_info.time_spent,
                    "original_estimate_seconds": time_info.original_estimate_seconds,
                    "remaining_estimate_seconds": time_info.remaining_estimate_seconds,
                    "time_spent_seconds": time_info.time_spent_seconds,
                    "progress_percentage": time_info.get_progress_percentage(),
                    "is_over_estimate": time_info.is_over_estimate(),
                    "remaining_hours": time_info.get_remaining_hours(),
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"issue_key": issue_key, "instance_name": instance_name}
            )


class UpdateTimeEstimatesUseCase:
    """Use case for updating time estimates on an issue."""

    def __init__(self, time_tracking_service: TimeTrackingService):
        self._time_tracking_service = time_tracking_service

    async def execute(
        self,
        issue_key: str,
        original_estimate: Optional[str] = None,
        remaining_estimate: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the update time estimates use case."""
        try:
            estimate_update = TimeEstimateUpdate(
                issue_key=issue_key,
                original_estimate=original_estimate,
                remaining_estimate=remaining_estimate
            )
            
            result = await self._time_tracking_service.update_time_estimates(estimate_update, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "updated": result.updated,
                    "issue_key": result.issue_key,
                    "original_estimate": result.original_estimate,
                    "remaining_estimate": result.remaining_estimate,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "issue_key": issue_key,
                    "original_estimate": original_estimate,
                    "remaining_estimate": remaining_estimate,
                    "instance_name": instance_name
                }
            )


class CreateIssueWithLinksUseCase:
    """Use case for creating an issue with links."""

    def __init__(self, issue_service: IssueService, issue_link_service: IssueLinkService):
        self._issue_service = issue_service
        self._issue_link_service = issue_link_service

    async def execute(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Story",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        links: Optional[List[Dict[str, str]]] = None,
        instance_name: Optional[str] = None
    ) -> UseCaseResult:
        """Execute the create issue with links use case."""
        try:
            # First create the issue
            create_request = IssueCreateRequest(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                priority=priority,
                assignee=assignee,
                labels=labels or []
            )
            
            issue = await self._issue_service.create_issue(create_request, instance_name)
            
            # Then create any links
            created_links = []
            if links:
                for link_data in links:
                    try:
                        issue_link = IssueLink(
                            link_type=link_data.get("link_type", "Relates"),
                            source_issue=link_data.get("source_issue", issue.key),
                            target_issue=link_data.get("target_issue", issue.key),
                            direction=link_data.get("direction", "outward")
                        )
                        
                        # Ensure we're not linking to ourselves
                        if issue_link.source_issue != issue_link.target_issue:
                            link_result = await self._issue_link_service.create_link(issue_link, instance_name)
                            if link_result.created:
                                created_links.append({
                                    "link_type": link_result.link_type,
                                    "source_issue": link_result.source_issue,
                                    "target_issue": link_result.target_issue,
                                    "link_id": link_result.link_id
                                })
                    except Exception as link_error:
                        # Log link creation error but don't fail the whole operation
                        pass
            
            return UseCaseResult(
                success=True,
                data={
                    "created": True,
                    "key": issue.key,
                    "id": issue.id,
                    "url": issue.url,
                    "links_created": len(created_links),
                    "links": created_links,
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={
                    "project_key": project_key,
                    "summary": summary,
                    "instance_name": instance_name
                }
            )


class ValidateJQLUseCase:
    """Use case for validating JQL syntax."""

    def __init__(self, search_service: SearchService):
        self._search_service = search_service

    async def execute(self, jql: str, instance_name: Optional[str] = None) -> UseCaseResult:
        """Execute the validate JQL use case."""
        try:
            validation_errors = await self._search_service.validate_jql_syntax(jql, instance_name)
            
            return UseCaseResult(
                success=True,
                data={
                    "jql": jql,
                    "is_valid": len(validation_errors) == 0,
                    "validation_errors": validation_errors,
                    "error_count": len(validation_errors),
                    "instance": instance_name
                }
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"jql": jql, "instance_name": instance_name}
            )
