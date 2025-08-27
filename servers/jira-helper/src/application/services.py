"""
Application Services Layer.

This module provides orchestration services that coordinate multiple use cases
and handle complex workflows that span across different domain services.
"""

import logging
from dataclasses import dataclass
from typing import Any

from application.base_use_case import UseCaseFactory, UseCaseResult
from application.use_cases import (
    AddCommentUseCase,
    CreateIssueUseCase,
    ListInstancesUseCase,
    ListProjectsUseCase,
    ListProjectTicketsUseCase,
    TransitionIssueUseCase,
)
from domain.exceptions import JiraValidationError

logger = logging.getLogger(__name__)


@dataclass
class WorkflowExecutionResult:
    """Result of a complex workflow execution."""
    success: bool
    steps_completed: list[str]
    final_result: Any
    errors: list[str]
    warnings: list[str]


class ValidationService:
    """
    Centralized input validation service.

    Provides basic sanity checks only. Lets Jira be the authoritative source
    for business rule validation (formats, constraints, etc).
    """

    @staticmethod
    def validate_issue_key(issue_key: str) -> None:
        """Basic validation for issue key - let Jira validate format specifics."""
        if not issue_key:
            raise JiraValidationError(["Issue key is required"])

        if not isinstance(issue_key, str):
            raise JiraValidationError(["Issue key must be a string"])

        if len(issue_key.strip()) == 0:
            raise JiraValidationError(["Issue key cannot be empty"])

        # Reasonable sanity limit - let Jira decide actual format rules
        if len(issue_key) > 100:
            raise JiraValidationError(["Issue key is unreasonably long"])

    @staticmethod
    def validate_project_key(project_key: str) -> None:
        """Basic validation for project key - let Jira validate format specifics."""
        if not project_key:
            raise JiraValidationError(["Project key is required"])

        if not isinstance(project_key, str):
            raise JiraValidationError(["Project key must be a string"])

        if len(project_key.strip()) == 0:
            raise JiraValidationError(["Project key cannot be empty"])

        # Reasonable sanity limit - let Jira decide actual format rules
        if len(project_key) > 50:
            raise JiraValidationError(["Project key is unreasonably long"])

    @staticmethod
    def validate_instance_name(instance_name: str | None) -> None:
        """Basic validation for instance name."""
        if instance_name is not None:
            if not isinstance(instance_name, str):
                raise JiraValidationError(["Instance name must be a string"])

            if len(instance_name.strip()) == 0:
                raise JiraValidationError(["Instance name cannot be empty"])

    @staticmethod
    def validate_summary(summary: str) -> None:
        """Basic validation for summary - let Jira validate length limits."""
        if not summary:
            raise JiraValidationError(["Summary is required"])

        if not isinstance(summary, str):
            raise JiraValidationError(["Summary must be a string"])

        if len(summary.strip()) == 0:
            raise JiraValidationError(["Summary cannot be empty"])

        # Very generous limit - let Jira decide actual constraints
        if len(summary) > 1000:
            raise JiraValidationError(["Summary is unreasonably long"])

    @staticmethod
    def validate_description(description: str) -> None:
        """Basic validation for description."""
        if not description:
            raise JiraValidationError(["Description is required"])

        if not isinstance(description, str):
            raise JiraValidationError(["Description must be a string"])

        if len(description.strip()) == 0:
            raise JiraValidationError(["Description cannot be empty"])

    @staticmethod
    def validate_comment(comment: str) -> None:
        """Basic validation for comment text."""
        if not comment:
            raise JiraValidationError(["Comment is required"])

        if not isinstance(comment, str):
            raise JiraValidationError(["Comment must be a string"])

        if len(comment.strip()) == 0:
            raise JiraValidationError(["Comment cannot be empty"])

    @staticmethod
    def validate_transition_name(transition_name: str) -> None:
        """Basic validation for transition name."""
        if not transition_name:
            raise JiraValidationError(["Transition name is required"])

        if not isinstance(transition_name, str):
            raise JiraValidationError(["Transition name must be a string"])

        if len(transition_name.strip()) == 0:
            raise JiraValidationError(["Transition name cannot be empty"])


class JiraApplicationService:
    """
    Application service that orchestrates complex Jira workflows.

    This service coordinates multiple use cases to handle complex business
    workflows that span across different domain services.
    """

    def __init__(self, use_case_factory: UseCaseFactory):
        """Initialize with use case factory for dependency injection."""
        self._factory = use_case_factory
        self._validation = ValidationService()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def create_issue_with_workflow(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Story",
        priority: str | None = None,
        assignee: str | None = None,
        labels: list[str] | None = None,
        initial_comment: str | None = None,
        auto_transition: str | None = None,
        instance_name: str | None = None
    ) -> WorkflowExecutionResult:
        """
        Create an issue and optionally add comment and transition it.

        This orchestrates multiple use cases to handle a complete issue creation workflow.
        """
        steps_completed = []
        errors = []
        warnings = []

        try:
            # Step 1: Validate all inputs
            self._validation.validate_project_key(project_key)
            self._validation.validate_summary(summary)
            self._validation.validate_description(description)
            self._validation.validate_instance_name(instance_name)

            if initial_comment:
                self._validation.validate_comment(initial_comment)

            if auto_transition:
                self._validation.validate_transition_name(auto_transition)

            steps_completed.append("Input validation")

            # Step 2: Create the issue
            create_use_case = self._factory.create_use_case(CreateIssueUseCase)
            create_result = await create_use_case.execute(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                priority=priority,
                assignee=assignee,
                labels=labels,
                instance_name=instance_name
            )

            if not create_result.success:
                errors.append(f"Issue creation failed: {create_result.error}")
                return WorkflowExecutionResult(
                    success=False,
                    steps_completed=steps_completed,
                    final_result=create_result,
                    errors=errors,
                    warnings=warnings
                )

            issue_key = create_result.data["key"]
            steps_completed.append(f"Issue created: {issue_key}")
            final_result = create_result

            # Step 3: Add initial comment if provided
            if initial_comment:
                comment_use_case = self._factory.create_use_case(AddCommentUseCase)
                comment_result = await comment_use_case.execute(
                    issue_key=issue_key,
                    comment=initial_comment,
                    instance_name=instance_name
                )

                if comment_result.success:
                    steps_completed.append("Initial comment added")
                else:
                    warnings.append(f"Failed to add initial comment: {comment_result.error}")

            # Step 4: Auto-transition if requested
            if auto_transition:
                transition_use_case = self._factory.create_use_case(TransitionIssueUseCase)
                transition_result = await transition_use_case.execute(
                    issue_key=issue_key,
                    transition_name=auto_transition,
                    instance_name=instance_name
                )

                if transition_result.success:
                    steps_completed.append(f"Transitioned to: {auto_transition}")
                    final_result = transition_result
                else:
                    warnings.append(f"Failed to transition: {transition_result.error}")

            return WorkflowExecutionResult(
                success=True,
                steps_completed=steps_completed,
                final_result=final_result,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            self._logger.error(f"Workflow execution failed: {e}")
            errors.append(str(e))
            return WorkflowExecutionResult(
                success=False,
                steps_completed=steps_completed,
                final_result=None,
                errors=errors,
                warnings=warnings
            )

    async def bulk_issue_transition(
        self,
        issue_keys: list[str],
        transition_name: str,
        comment: str | None = None,
        instance_name: str | None = None
    ) -> WorkflowExecutionResult:
        """
        Transition multiple issues through the same workflow step.

        This orchestrates multiple transition use cases for bulk operations.
        """
        steps_completed = []
        errors = []
        warnings = []
        successful_transitions = []
        failed_transitions = []

        try:
            # Validate inputs
            if not issue_keys:
                raise JiraValidationError(["At least one issue key is required"])

            for issue_key in issue_keys:
                self._validation.validate_issue_key(issue_key)

            self._validation.validate_transition_name(transition_name)
            self._validation.validate_instance_name(instance_name)

            if comment:
                self._validation.validate_comment(comment)

            steps_completed.append(f"Validated {len(issue_keys)} issue keys")

            # Process each issue
            transition_use_case = self._factory.create_use_case(TransitionIssueUseCase)

            for issue_key in issue_keys:
                try:
                    result = await transition_use_case.execute(
                        issue_key=issue_key,
                        transition_name=transition_name,
                        comment=comment,
                        instance_name=instance_name
                    )

                    if result.success:
                        successful_transitions.append(issue_key)
                        steps_completed.append(f"Transitioned {issue_key}")
                    else:
                        failed_transitions.append(issue_key)
                        warnings.append(f"Failed to transition {issue_key}: {result.error}")

                except Exception as e:
                    failed_transitions.append(issue_key)
                    warnings.append(f"Error transitioning {issue_key}: {str(e)}")

            final_result = {
                "successful_transitions": successful_transitions,
                "failed_transitions": failed_transitions,
                "total_processed": len(issue_keys),
                "success_count": len(successful_transitions),
                "failure_count": len(failed_transitions)
            }

            return WorkflowExecutionResult(
                success=len(successful_transitions) > 0,
                steps_completed=steps_completed,
                final_result=final_result,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            self._logger.error(f"Bulk transition workflow failed: {e}")
            errors.append(str(e))
            return WorkflowExecutionResult(
                success=False,
                steps_completed=steps_completed,
                final_result=None,
                errors=errors,
                warnings=warnings
            )

    async def get_project_overview(
        self,
        project_key: str,
        include_recent_issues: bool = True,
        max_issues: int = 10,
        instance_name: str | None = None
    ) -> UseCaseResult:
        """
        Get comprehensive project overview including project details and recent issues.

        This orchestrates multiple use cases to provide a complete project view.
        """
        try:
            # Validate inputs
            self._validation.validate_project_key(project_key)
            self._validation.validate_instance_name(instance_name)

            # Get project list to find our project
            projects_use_case = self._factory.create_use_case(ListProjectsUseCase)
            projects_result = await projects_use_case.execute(instance_name=instance_name)

            if not projects_result.success:
                return projects_result

            # Find the specific project
            target_project = None
            for project in projects_result.data["projects"]:
                if project["key"] == project_key:
                    target_project = project
                    break

            if not target_project:
                return UseCaseResult(
                    success=False,
                    error=f"Project {project_key} not found",
                    details={"project_key": project_key, "instance_name": instance_name}
                )

            overview_data = {
                "project": target_project,
                "instance": instance_name
            }

            # Get recent issues if requested
            if include_recent_issues:
                tickets_use_case = self._factory.create_use_case(ListProjectTicketsUseCase)
                tickets_result = await tickets_use_case.execute(
                    project_key=project_key,
                    max_results=max_issues,
                    instance_name=instance_name
                )

                if tickets_result.success:
                    overview_data["recent_issues"] = tickets_result.data["issues"]
                    overview_data["total_issues"] = tickets_result.data["issues_count"]
                else:
                    overview_data["recent_issues"] = []
                    overview_data["issues_error"] = tickets_result.error

            return UseCaseResult(
                success=True,
                data=overview_data,
                details={"project_key": project_key, "instance_name": instance_name}
            )

        except Exception as e:
            self._logger.error(f"Project overview failed: {e}")
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"project_key": project_key, "instance_name": instance_name}
            )

    async def get_multi_instance_summary(self) -> UseCaseResult:
        """
        Get summary information across all configured Jira instances.

        This orchestrates use cases across multiple instances to provide a unified view.
        """
        try:
            # Get all instances
            instances_use_case = self._factory.create_use_case(ListInstancesUseCase)
            instances_result = await instances_use_case.execute()

            if not instances_result.success:
                return instances_result

            instances = instances_result.data["instances"]
            summary_data = {
                "instances": [],
                "total_instances": len(instances),
                "total_projects": 0,
                "errors": []
            }

            # Get project count for each instance
            projects_use_case = self._factory.create_use_case(ListProjectsUseCase)

            for instance in instances:
                instance_name = instance["name"]
                instance_summary = {
                    "name": instance_name,
                    "url": instance["url"],
                    "is_default": instance["is_default"],
                    "project_count": 0,
                    "accessible": False
                }

                try:
                    projects_result = await projects_use_case.execute(instance_name=instance_name)

                    if projects_result.success:
                        instance_summary["project_count"] = projects_result.data["count"]
                        instance_summary["accessible"] = True
                        summary_data["total_projects"] += projects_result.data["count"]
                    else:
                        instance_summary["error"] = projects_result.error
                        summary_data["errors"].append(f"{instance_name}: {projects_result.error}")

                except Exception as e:
                    instance_summary["error"] = str(e)
                    summary_data["errors"].append(f"{instance_name}: {str(e)}")

                summary_data["instances"].append(instance_summary)

            return UseCaseResult(
                success=True,
                data=summary_data,
                details={"operation": "multi_instance_summary"}
            )

        except Exception as e:
            self._logger.error(f"Multi-instance summary failed: {e}")
            return UseCaseResult(
                success=False,
                error=str(e),
                details={"operation": "multi_instance_summary"}
            )
