"""
Simplified use cases using BaseUseCase pattern.

This module demonstrates the massive code reduction achieved by using
the BaseUseCase pattern to eliminate boilerplate in application layer.
"""

from typing import Any

from application.base_use_case import BaseCommandUseCase, BaseQueryUseCase
from domain.models import (
    AssigneeChangeRequest,
    CommentAddRequest,
    IssueCreateRequest,
    IssueTransitionRequest,
    SearchFilters,
)


class ListProjectsUseCase(BaseQueryUseCase):
    """Simplified use case for listing projects."""

    async def execute(self, instance_name: str):
        """Execute the list projects use case."""
        def result_mapper(projects):
            return {
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

        return await self.execute_query(
            lambda: self._project_service.get_projects(instance_name),
            result_mapper,
            instance_name=instance_name
        )


class GetIssueDetailsUseCase(BaseQueryUseCase):
    """Simplified use case for getting issue details."""

    async def execute(self, issue_key: str, instance_name: str):
        """Execute the get issue details use case."""
        self._validate_required_params(issue_key=issue_key)

        def result_mapper(issue):
            return {
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

        return await self.execute_query(
            lambda: self._issue_service.get_issue(issue_key, instance_name),
            result_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class GetFullIssueDetailsUseCase(BaseQueryUseCase):
    """Simplified use case for getting full issue details with comments."""

    async def execute(
        self,
        issue_key: str,
        raw_data: bool,
        format: str,
        instance_name: str
    ):
        """Execute the get full issue details use case."""
        self._validate_required_params(issue_key=issue_key)

        def result_mapper(issue):
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
                return {
                    "issue": issue.__dict__,
                    "comments": formatted_comments,
                    "comment_count": len(formatted_comments)
                }

            base_issue = {
                "key": issue.key,
                "id": issue.id,
                "summary": issue.summary,
                "status": issue.status,
                "priority": issue.priority,
                "assignee": issue.assignee,
                "reporter": issue.reporter,
                "created": issue.created,
                "updated": issue.updated
            }

            if format == "summary":
                return {
                    "issue": base_issue,
                    "description": issue.description,
                    "components": issue.components,
                    "labels": issue.labels,
                    "comments": formatted_comments,
                    "comment_count": len(formatted_comments)
                }
            else:  # formatted
                return {
                    "issue": base_issue,
                    "description": issue.description,
                    "custom_fields": issue.custom_fields,
                    "components": issue.components,
                    "labels": issue.labels,
                    "comments": formatted_comments,
                    "comment_count": len(formatted_comments)
                }

        return await self.execute_query(
            lambda: self._issue_service.get_issue_with_comments(issue_key, instance_name),
            result_mapper,
            issue_key=issue_key,
            raw_data=raw_data,
            format=format,
            instance_name=instance_name
        )


class CreateIssueUseCase(BaseCommandUseCase):
    """Simplified use case for creating a new issue."""

    async def execute(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str,
        priority: str | None,
        assignee: str | None,
        labels: list[str] | None,
        custom_fields: dict[str, Any] | None,
        instance_name: str
    ):
        """Execute the create issue use case."""
        self._validate_required_params(
            project_key=project_key,
            summary=summary,
            description=description
        )

        def create_operation():
            request = IssueCreateRequest(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                priority=priority,
                assignee=assignee,
                labels=labels or [],
                custom_fields=custom_fields or {}
            )
            return self._issue_service.create_issue(request, instance_name)

        def success_mapper(issue):
            return {
                "created": True,
                "key": issue.key,
                "id": issue.id,
                "url": issue.url,
                "custom_fields_applied": len(custom_fields) if custom_fields else 0
            }

        return await self.execute_command(
            create_operation,
            success_mapper,
            project_key=project_key,
            summary=summary,
            instance_name=instance_name
        )


class AddCommentUseCase(BaseCommandUseCase):
    """Simplified use case for adding a comment to an issue."""

    async def execute(self, issue_key: str, comment: str, instance_name: str):
        """Execute the add comment use case."""
        self._validate_required_params(issue_key=issue_key, comment=comment)

        def add_comment_operation():
            request = CommentAddRequest(issue_key=issue_key, comment=comment)
            return self._comment_service.add_comment(request, instance_name)

        def success_mapper(comment_obj):
            return {
                "added": True,
                "issue_key": issue_key,
                "comment_id": comment_obj.id,
                "comment_author": comment_obj.author_name,
                "comment_body": comment_obj.body
            }

        return await self.execute_command(
            add_comment_operation,
            success_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class TransitionIssueUseCase(BaseCommandUseCase):
    """Simplified use case for transitioning an issue through workflow."""

    async def execute(
        self,
        issue_key: str,
        transition_name: str,
        comment: str | None,
        instance_name: str
    ):
        """Execute the transition issue use case."""
        self._validate_required_params(issue_key=issue_key, transition_name=transition_name)

        def transition_operation():
            request = IssueTransitionRequest(
                issue_key=issue_key,
                transition_name=transition_name,
                comment=comment
            )
            return self._workflow_service.transition_issue(request, instance_name)

        def success_mapper(updated_issue):
            return {
                "success": True,
                "issue_key": issue_key,
                "transition_executed": transition_name,
                "new_status": updated_issue.status,
                "comment_added": bool(comment),
                "url": updated_issue.url,
                "instance": instance_name
            }

        return await self.execute_command(
            transition_operation,
            success_mapper,
            issue_key=issue_key,
            transition_name=transition_name,
            instance_name=instance_name
        )


class GetIssueTransitionsUseCase(BaseQueryUseCase):
    """Simplified use case for getting available transitions for an issue."""

    async def execute(self, issue_key: str, instance_name: str):
        """Execute the get issue transitions use case."""
        self._validate_required_params(issue_key=issue_key)

        def result_mapper(transitions):
            return {
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

        return await self.execute_query(
            lambda: self._workflow_service.get_available_transitions(issue_key, instance_name),
            result_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class ChangeAssigneeUseCase(BaseCommandUseCase):
    """Simplified use case for changing an issue's assignee."""

    async def execute(
        self,
        issue_key: str,
        assignee: str | None,
        instance_name: str
    ):
        """Execute the change assignee use case."""
        self._validate_required_params(issue_key=issue_key)

        def change_assignee_operation():
            request = AssigneeChangeRequest(issue_key=issue_key, assignee=assignee)
            return self._workflow_service.change_assignee(request, instance_name)

        def success_mapper(updated_issue):
            return {
                "success": True,
                "issue_key": issue_key,
                "new_assignee": updated_issue.assignee,
                "url": updated_issue.url,
                "instance": instance_name
            }

        return await self.execute_command(
            change_assignee_operation,
            success_mapper,
            issue_key=issue_key,
            assignee=assignee,
            instance_name=instance_name
        )


class ListProjectTicketsUseCase(BaseQueryUseCase):
    """Simplified use case for listing tickets in a project using SearchService."""

    async def execute(
        self,
        project_key: str,
        status: str | None,
        issue_type: str | None,
        max_results: int,
        instance_name: str
    ):
        """Execute the list project tickets use case."""
        self._validate_required_params(project_key=project_key)

        def result_mapper(search_result):
            return {
                "project": project_key,
                "issues_count": len(search_result.issues),
                "total_results": search_result.total_results,
                "start_at": search_result.start_at,
                "max_results": search_result.max_results,
                "has_more": search_result.has_more_results(),
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
                    for issue in search_result.issues
                ],
                "instance": instance_name
            }

        # Create SearchFilters from parameters
        search_filters = SearchFilters(
            project_key=project_key,
            status=status,
            issue_type=issue_type,
            max_results=max_results,
            start_at=0  # Always start from beginning for this use case
        )

        return await self.execute_query(
            lambda: self._search_service.search_with_filters(search_filters, instance_name),
            result_mapper,
            project_key=project_key,
            status=status,
            issue_type=issue_type,
            instance_name=instance_name
        )


class ListInstancesUseCase(BaseQueryUseCase):
    """Simplified use case for listing all configured Jira instances."""

    async def execute(self):
        """Execute the list instances use case."""
        def result_mapper(data):
            instances, default_instance = data
            return {
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

        async def get_instances_data():
            instances = self._config_service.get_instances()
            default_instance = self._config_service.get_default_instance()
            return instances, default_instance

        return await self.execute_query(get_instances_data, result_mapper)


class GetCustomFieldMappingsUseCase(BaseQueryUseCase):
    """Simplified use case for getting custom field mappings."""

    async def execute(self, reverse: bool, instance_name: str):
        """Execute the get custom field mappings use case."""
        def result_mapper(mappings):
            return {
                "field_mappings": mappings,
                "count": len(mappings),
                "reverse": reverse,
                "instance": instance_name
            }

        return await self.execute_query(
            lambda: self._field_service.get_custom_field_mappings(reverse, instance_name),
            result_mapper,
            reverse=reverse,
            instance_name=instance_name
        )


class GenerateWorkflowGraphUseCase(BaseQueryUseCase):
    """Simplified use case for generating workflow graphs."""

    async def execute(
        self,
        project_key: str,
        issue_type: str,
        format: str,
        instance_name: str
    ):
        """Execute the generate workflow graph use case."""
        self._validate_required_params(project_key=project_key)

        def result_mapper(graph_data):
            return {
                "project_key": project_key,
                "issue_type": issue_type,
                "format": format,
                "graph_data": graph_data,
                "instance": instance_name
            }

        return await self.execute_query(
            lambda: self._workflow_service.generate_workflow_graph(
                project_key, issue_type, format, instance_name
            ),
            result_mapper,
            project_key=project_key,
            issue_type=issue_type,
            instance_name=instance_name
        )


class UpdateIssueUseCase(BaseCommandUseCase):
    """Simplified use case for updating an existing issue."""

    async def execute(
        self,
        issue_key: str,
        summary: str | None,
        description: str | None,
        priority: str | None,
        assignee: str | None,
        labels: list[str] | None,
        instance_name: str
    ):
        """Execute the update issue use case."""
        self._validate_required_params(issue_key=issue_key)

        def update_operation():
            from domain.models import IssueUpdate
            update_request = IssueUpdate(
                issue_key=issue_key,
                summary=summary,
                description=description,
                priority=priority,
                assignee=assignee,
                labels=labels
            )
            return self._issue_update_service.update_issue(update_request, instance_name)

        def success_mapper(updated_issue):
            return {
                "updated": True,
                "issue_key": issue_key,
                "summary": updated_issue.summary,
                "description": updated_issue.description,
                "priority": updated_issue.priority,
                "assignee": updated_issue.assignee,
                "labels": updated_issue.labels,
                "url": updated_issue.url,
                "instance": instance_name
            }

        return await self.execute_command(
            update_operation,
            success_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class SearchIssuesUseCase(BaseQueryUseCase):
    """Simplified use case for searching issues with JQL."""

    async def execute(
        self,
        jql: str,
        max_results: int,
        start_at: int,
        fields: list[str] | None,
        instance_name: str
    ):
        """Execute the search issues use case."""
        import logging
        import time
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        logger.info(f"🎯 SearchIssuesUseCase.execute() ENTRY - JQL: {jql[:100]}... | Instance: {instance_name} | Max Results: {max_results}")
        
        self._validate_required_params(jql=jql)

        def result_mapper(search_result):
            mapping_start = time.time()
            result = {
                "jql": jql,
                "total": search_result.total_results,
                "start_at": search_result.start_at,
                "max_results": search_result.max_results,
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
                    for issue in search_result.issues
                ],
                "instance": instance_name
            }
            mapping_elapsed = time.time() - mapping_start
            logger.info(f"📋 Result mapping took {mapping_elapsed:.3f}s for {len(search_result.issues)} issues")
            return result

        # Create SearchQuery from parameters
        from domain.models import SearchQuery
        query_start = time.time()
        search_query = SearchQuery(
            jql=jql,
            max_results=max_results,
            start_at=start_at,
            fields=fields
        )
        query_elapsed = time.time() - query_start
        logger.info(f"🔧 SearchQuery creation took {query_elapsed:.3f}s")

        logger.info(f"🔄 Calling search_service.search_issues()...")
        result = await self.execute_query(
            lambda: self._search_service.search_issues(search_query, instance_name),
            result_mapper,
            jql=jql,
            max_results=max_results,
            instance_name=instance_name
        )
        
        total_elapsed = time.time() - start_time
        logger.info(f"🎯 SearchIssuesUseCase.execute() COMPLETE - Total time: {total_elapsed:.3f}s")
        
        return result


class ValidateJqlUseCase(BaseQueryUseCase):
    """Simplified use case for validating JQL syntax."""

    async def execute(self, jql: str, instance_name: str):
        """Execute the validate JQL use case."""
        self._validate_required_params(jql=jql)

        def result_mapper(validation_result):
            # validation_result is already a dict from SearchService.validate_jql()
            return {
                "jql": jql,
                "valid": validation_result.get("valid", False),
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "instance": instance_name
            }

        return await self.execute_query(
            lambda: self._search_service.validate_jql(jql, instance_name),
            result_mapper,
            jql=jql,
            instance_name=instance_name
        )


class CreateIssueLinkUseCase(BaseCommandUseCase):
    """Simplified use case for creating links between issues."""

    async def execute(
        self,
        source_issue: str,
        target_issue: str,
        link_type: str,
        direction: str,
        instance_name: str
    ):
        """Execute the create issue link use case."""
        self._validate_required_params(
            source_issue=source_issue,
            target_issue=target_issue,
            link_type=link_type
        )

        def create_link_operation():
            from domain.models import IssueLink
            issue_link = IssueLink(
                link_type=link_type,
                source_issue=source_issue,
                target_issue=target_issue,
                direction=direction
            )
            return self._issue_link_service.create_link(issue_link, instance_name)

        def success_mapper(result):
            return {
                "created": result.created,
                "source_issue": result.source_issue,
                "target_issue": result.target_issue,
                "link_type": result.link_type,
                "link_id": result.link_id,
                "instance": instance_name
            }

        return await self.execute_command(
            create_link_operation,
            success_mapper,
            source_issue=source_issue,
            target_issue=target_issue,
            link_type=link_type,
            instance_name=instance_name
        )


class CreateEpicStoryLinkUseCase(BaseCommandUseCase):
    """Simplified use case for creating Epic-Story links."""

    async def execute(
        self,
        epic_key: str,
        story_key: str,
        instance_name: str
    ):
        """Execute the create Epic-Story link use case."""
        self._validate_required_params(epic_key=epic_key, story_key=story_key)

        def create_epic_link_operation():
            return self._issue_link_service.create_epic_story_link(epic_key, story_key, instance_name)

        def success_mapper(result):
            return {
                "created": result.created,
                "epic_key": epic_key,
                "story_key": story_key,
                "link_type": result.link_type,
                "link_id": result.link_id,
                "instance": instance_name
            }

        return await self.execute_command(
            create_epic_link_operation,
            success_mapper,
            epic_key=epic_key,
            story_key=story_key,
            instance_name=instance_name
        )


class GetIssueLinksUseCase(BaseQueryUseCase):
    """Simplified use case for getting all links for an issue."""

    async def execute(self, issue_key: str, instance_name: str):
        """Execute the get issue links use case."""
        self._validate_required_params(issue_key=issue_key)

        def result_mapper(links):
            return {
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

        return await self.execute_query(
            lambda: self._issue_link_service.get_issue_links(issue_key, instance_name),
            result_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class LogWorkUseCase(BaseCommandUseCase):
    """Simplified use case for logging work on an issue."""

    async def execute(
        self,
        issue_key: str,
        time_spent: str,
        comment: str,
        started: str | None,
        adjust_estimate: str,
        new_estimate: str | None,
        reduce_by: str | None,
        instance_name: str
    ):
        """Execute the log work use case."""
        self._validate_required_params(issue_key=issue_key, time_spent=time_spent)

        def log_work_operation():
            from domain.models import WorkLogRequest
            work_log_request = WorkLogRequest(
                issue_key=issue_key,
                time_spent=time_spent,
                comment=comment,
                started=started,
                adjust_estimate=adjust_estimate,
                new_estimate=new_estimate,
                reduce_by=reduce_by
            )
            return self._time_tracking_service.log_work(work_log_request, instance_name)

        def success_mapper(result):
            return {
                "logged": result.logged,
                "issue_key": result.issue_key,
                "work_log_id": result.work_log_id,
                "time_spent": result.time_spent,
                "time_spent_seconds": result.time_spent_seconds,
                "time_spent_hours": result.get_time_in_hours(),
                "new_remaining_estimate": result.new_remaining_estimate,
                "instance": instance_name
            }

        return await self.execute_command(
            log_work_operation,
            success_mapper,
            issue_key=issue_key,
            time_spent=time_spent,
            instance_name=instance_name
        )


class GetWorkLogsUseCase(BaseQueryUseCase):
    """Simplified use case for getting work logs for an issue."""

    async def execute(self, issue_key: str, instance_name: str):
        """Execute the get work logs use case."""
        self._validate_required_params(issue_key=issue_key)

        def result_mapper(work_logs):
            return {
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

        return await self.execute_query(
            lambda: self._time_tracking_service.get_work_logs(issue_key, instance_name),
            result_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class GetTimeTrackingInfoUseCase(BaseQueryUseCase):
    """Simplified use case for getting time tracking information for an issue."""

    async def execute(self, issue_key: str, instance_name: str):
        """Execute the get time tracking info use case."""
        self._validate_required_params(issue_key=issue_key)

        def result_mapper(time_info):
            return {
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

        return await self.execute_query(
            lambda: self._time_tracking_service.get_time_tracking_info(issue_key, instance_name),
            result_mapper,
            issue_key=issue_key,
            instance_name=instance_name
        )


class UpdateTimeEstimatesUseCase(BaseCommandUseCase):
    """Simplified use case for updating time estimates on an issue."""

    async def execute(
        self,
        issue_key: str,
        original_estimate: str | None,
        remaining_estimate: str | None,
        instance_name: str
    ):
        """Execute the update time estimates use case."""
        self._validate_required_params(issue_key=issue_key)

        def update_estimates_operation():
            from domain.models import TimeEstimateUpdate
            estimate_update = TimeEstimateUpdate(
                issue_key=issue_key,
                original_estimate=original_estimate,
                remaining_estimate=remaining_estimate
            )
            return self._time_tracking_service.update_time_estimates(estimate_update, instance_name)

        def success_mapper(result):
            return {
                "updated": result.updated,
                "issue_key": result.issue_key,
                "original_estimate": result.original_estimate,
                "remaining_estimate": result.remaining_estimate,
                "instance": instance_name
            }

        return await self.execute_command(
            update_estimates_operation,
            success_mapper,
            issue_key=issue_key,
            original_estimate=original_estimate,
            remaining_estimate=remaining_estimate,
            instance_name=instance_name
        )


class CreateIssueWithLinksUseCase(BaseCommandUseCase):
    """Simplified use case for creating an issue with links."""

    async def execute(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str,
        priority: str | None,
        assignee: str | None,
        labels: list[str] | None,
        custom_fields: dict[str, Any] | None,
        links: list[dict[str, str]] | None,
        instance_name: str
    ):
        """Execute the create issue with links use case."""
        self._validate_required_params(
            project_key=project_key,
            summary=summary,
            description=description
        )

        async def create_with_links_operation():
            # First create the issue
            create_request = IssueCreateRequest(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                priority=priority,
                assignee=assignee,
                labels=labels or [],
                custom_fields=custom_fields or {}
            )

            issue = await self._issue_service.create_issue(create_request, instance_name)

            # Then create any links
            created_links = []
            if links:
                for link_data in links:
                    try:
                        from domain.models import IssueLink
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
                    except Exception:
                        # Log link creation error but don't fail the whole operation
                        pass

            return {
                "issue": issue,
                "created_links": created_links
            }

        def success_mapper(result):
            issue = result["issue"]
            created_links = result["created_links"]
            return {
                "created": True,
                "key": issue.key,
                "id": issue.id,
                "url": issue.url,
                "links_created": len(created_links),
                "links": created_links,
                "custom_fields_applied": len(custom_fields) if custom_fields else 0,
                "instance": instance_name
            }

        return await self.execute_command(
            create_with_links_operation,
            success_mapper,
            project_key=project_key,
            summary=summary,
            instance_name=instance_name
        )


class GetProjectWorkflowSchemeUseCase(BaseQueryUseCase):
    """Simplified use case for getting comprehensive project workflow scheme data."""

    async def execute(self, project_key: str, instance_name: str):
        """Execute the get project workflow scheme use case."""
        self._validate_required_params(project_key=project_key)

        def result_mapper(workflow_scheme_data):
            return {
                "project_key": project_key,
                "project": workflow_scheme_data["project"],
                "workflow_scheme": workflow_scheme_data["workflow_scheme"], 
                "issue_type_workflows": workflow_scheme_data["issue_type_workflows"],
                "workflow_count": len(workflow_scheme_data["issue_type_workflows"]),
                "issue_types": list(workflow_scheme_data["issue_type_workflows"].keys()),
                "instance": instance_name
            }

        return await self.execute_query(
            lambda: self._workflow_service.get_project_workflow_scheme(project_key, instance_name),
            result_mapper,
            project_key=project_key,
            instance_name=instance_name
        )
