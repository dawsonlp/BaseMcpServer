"""Typed MCP boundary; domain functions receive explicit lazy client dependencies."""

import logging
from collections.abc import Callable
from functools import partial
from typing import Any, Literal, TypeVar

import anyio
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

from exceptions import JiraError, public_error_message
from runtime import RuntimeState
from tools import (
    comments,
    confluence,
    files,
    issues,
    links as issue_links,
    search,
    time_tracking,
    workflow,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def _call(
    ctx: Context[RuntimeState],
    service: Literal["jira", "confluence"],
    instance_name: str | None,
    operation: Callable[..., T],
    **arguments: Any,
) -> T:
    state = ctx.request_context.lifespan_context
    try:
        # Do not abandon a thread on cancellation: its client stays owned until it finishes.
        return await anyio.to_thread.run_sync(
            partial(state.execute, service, instance_name, operation, arguments),
            abandon_on_cancel=False,
        )
    except JiraError as error:
        logger.info("Expected Jira operation failure", exc_info=True)
        raise ToolError(public_error_message(error)) from error


async def list_jira_projects(
    instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> issues.ProjectsResult:
    return await _call(ctx, "jira", instance_name, issues.list_jira_projects)


async def get_issue_details(
    issue_key: str, instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> issues.IssueDetailsResult:
    return await _call(
        ctx, "jira", instance_name, issues.get_issue_details, issue_key=issue_key
    )


async def get_full_issue_details(
    issue_key: str,
    instance_name: str | None = None,
    include_comments: bool = True,
    raw_data: bool = False,
    format: Literal["structured"] = "structured",
    *,
    ctx: Context[RuntimeState],
) -> dict[str, Any]:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issues.get_full_issue_details,
        issue_key=issue_key,
        include_comments=include_comments,
        raw_data=raw_data,
        format=format,
    )


async def create_jira_ticket(
    project_key: str,
    summary: str,
    issue_type: str = "Task",
    description: str = "",
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
    components: list[str] | None = None,
    instance_name: str | None = None,
    custom_fields: dict[str, Any] | None = None,
    *,
    ctx: Context[RuntimeState],
) -> issues.CreatedIssueResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issues.create_jira_ticket,
        project_key=project_key,
        summary=summary,
        issue_type=issue_type,
        description=description,
        priority=priority,
        assignee=assignee,
        labels=labels,
        components=components,
        custom_fields=custom_fields,
    )


async def update_jira_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
    components: list[str] | None = None,
    instance_name: str | None = None,
    custom_fields: dict[str, Any] | None = None,
    *,
    ctx: Context[RuntimeState],
) -> issues.UpdatedIssueResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issues.update_jira_issue,
        issue_key=issue_key,
        summary=summary,
        description=description,
        priority=priority,
        assignee=assignee,
        labels=labels,
        components=components,
        custom_fields=custom_fields,
    )


async def transition_jira_issue(
    issue_key: str,
    transition_name: str | None = None,
    transition_id: str | None = None,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> issues.TransitionResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issues.transition_jira_issue,
        issue_key=issue_key,
        transition_name=transition_name,
        transition_id=transition_id,
    )


async def change_issue_assignee(
    issue_key: str,
    assignee: str,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> issues.AssigneeResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issues.change_issue_assignee,
        issue_key=issue_key,
        assignee=assignee,
    )


async def list_jira_instances(*, ctx: Context[RuntimeState]) -> issues.InstancesResult:
    return issues.list_jira_instances(
        configuration=ctx.request_context.lifespan_context.clients.configuration
    )


async def get_custom_field_mappings(
    instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> issues.CustomFieldsResult:
    return await _call(ctx, "jira", instance_name, issues.get_custom_field_mappings)


async def upload_file_to_jira(
    issue_key: str,
    file_path: str,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> files.UploadResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        files.upload_file_to_jira,
        issue_key=issue_key,
        file_path=file_path,
    )


async def list_issue_attachments(
    issue_key: str, instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> files.AttachmentsResult:
    return await _call(
        ctx, "jira", instance_name, files.list_issue_attachments, issue_key=issue_key
    )


async def delete_issue_attachment(
    attachment_id: str, instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> files.DeleteAttachmentResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        files.delete_issue_attachment,
        attachment_id=attachment_id,
    )


async def list_confluence_spaces(
    instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> confluence.SpacesResult:
    return await _call(
        ctx, "confluence", instance_name, confluence.list_confluence_spaces
    )


async def list_confluence_pages(
    space_key: str,
    instance_name: str | None = None,
    limit: confluence.ResultLimit = 20,
    *,
    ctx: Context[RuntimeState],
) -> confluence.PagesResult:
    return await _call(
        ctx,
        "confluence",
        instance_name,
        confluence.list_confluence_pages,
        space_key=space_key,
        limit=limit,
    )


async def get_confluence_page(
    page_id: str | None = None,
    title: str | None = None,
    space_key: str | None = None,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> confluence.PageResult:
    return await _call(
        ctx,
        "confluence",
        instance_name,
        confluence.get_confluence_page,
        page_id=page_id,
        title=title,
        space_key=space_key,
    )


async def search_confluence_pages(
    query: str,
    instance_name: str | None = None,
    limit: confluence.ResultLimit = 20,
    *,
    ctx: Context[RuntimeState],
) -> confluence.SearchPagesResult:
    return await _call(
        ctx,
        "confluence",
        instance_name,
        confluence.search_confluence_pages,
        query=query,
        limit=limit,
    )


async def create_confluence_page(
    space_key: str,
    title: str,
    body: str,
    parent_id: str | None = None,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> confluence.CreatedPageResult:
    return await _call(
        ctx,
        "confluence",
        instance_name,
        confluence.create_confluence_page,
        space_key=space_key,
        title=title,
        body=body,
        parent_id=parent_id,
    )


async def update_confluence_page(
    page_id: str,
    title: str | None = None,
    body: str | None = None,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> confluence.UpdatedPageResult:
    return await _call(
        ctx,
        "confluence",
        instance_name,
        confluence.update_confluence_page,
        page_id=page_id,
        title=title,
        body=body,
    )


async def create_issue_link(
    from_issue_key: str,
    to_issue_key: str,
    link_type: str = "Relates",
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> issue_links.LinkCreatedResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issue_links.create_issue_link,
        from_issue_key=from_issue_key,
        to_issue_key=to_issue_key,
        link_type=link_type,
    )


async def create_epic_story_link(
    epic_key: str,
    story_key: str,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> issue_links.EpicLinkResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issue_links.create_epic_story_link,
        epic_key=epic_key,
        story_key=story_key,
    )


async def get_issue_links(
    issue_key: str, instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> issue_links.IssueLinksResult:
    return await _call(
        ctx, "jira", instance_name, issue_links.get_issue_links, issue_key=issue_key
    )


async def create_issue_with_links(
    project_key: str,
    summary: str,
    issue_type: str = "Task",
    description: str = "",
    links: list[issue_links.IssueLinkInput] | None = None,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> issue_links.LinkedIssueResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        issue_links.create_issue_with_links,
        project_key=project_key,
        summary=summary,
        issue_type=issue_type,
        description=description,
        links=links,
    )


async def search_jira_issues(
    jql: str,
    max_results: search.ResultLimit = 20,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> search.SearchResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        search.search_jira_issues,
        jql=jql,
        max_results=max_results,
    )


async def list_project_tickets(
    project_key: str,
    status: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
    max_results: search.ResultLimit = 20,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> search.SearchResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        search.list_project_tickets,
        project_key=project_key,
        status=status,
        assignee=assignee,
        issue_type=issue_type,
        max_results=max_results,
    )


async def validate_jql_query(
    jql: str, *, ctx: Context[RuntimeState]
) -> search.JqlValidationResult:
    return search.validate_jql_query(jql)


async def generate_project_workflow_graph(
    project_key: str,
    issue_type: str = "Task",
    output_format: Literal["png", "svg", "json"] = "png",
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> workflow.WorkflowResult:
    result = await _call(
        ctx,
        "jira",
        instance_name,
        workflow.generate_project_workflow_graph,
        project_key=project_key,
        issue_type=issue_type,
        output_format=output_format,
    )
    if "resource_uri" in result:
        await ctx.notify_resource_updated(result["resource_uri"])
    return result


async def log_work(
    issue_key: str,
    time_spent: str,
    comment: str | None = None,
    started: str | None = None,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> time_tracking.WorkLoggedResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        time_tracking.log_work,
        issue_key=issue_key,
        time_spent=time_spent,
        comment=comment,
        started=started,
    )


async def get_work_logs(
    issue_key: str, instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> time_tracking.WorkLogsResult:
    return await _call(
        ctx, "jira", instance_name, time_tracking.get_work_logs, issue_key=issue_key
    )


async def get_time_tracking_info(
    issue_key: str, instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> time_tracking.TimeTrackingResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        time_tracking.get_time_tracking_info,
        issue_key=issue_key,
    )


async def update_time_estimates(
    issue_key: str,
    original_estimate: str | None = None,
    remaining_estimate: str | None = None,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> time_tracking.EstimatesUpdatedResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        time_tracking.update_time_estimates,
        issue_key=issue_key,
        original_estimate=original_estimate,
        remaining_estimate=remaining_estimate,
    )


async def add_comment_to_jira_ticket(
    issue_key: str,
    comment: str,
    instance_name: str | None = None,
    *,
    ctx: Context[RuntimeState],
) -> comments.CommentResult:
    return await _call(
        ctx,
        "jira",
        instance_name,
        comments.add_comment_to_jira_ticket,
        issue_key=issue_key,
        comment=comment,
    )


async def get_issue_transitions(
    issue_key: str, instance_name: str | None = None, *, ctx: Context[RuntimeState]
) -> comments.TransitionsResult:
    return await _call(
        ctx, "jira", instance_name, comments.get_issue_transitions, issue_key=issue_key
    )
