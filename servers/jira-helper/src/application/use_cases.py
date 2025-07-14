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
    AssigneeChangeRequest, CommentAddRequest
)
from domain.services import (
    IssueService, WorkflowService, ProjectService, VisualizationService,
    InstanceService
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
