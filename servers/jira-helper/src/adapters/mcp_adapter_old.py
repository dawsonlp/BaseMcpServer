"""
MCP adapter for the Jira Helper.

This module implements the MCP server adapter that translates between
MCP tool calls and the application's use cases, keeping all MCP-specific
code isolated from the core business logic.
"""

import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP

from .mcp_tools import create_mcp_tools
from application.use_cases import (
    ListProjectsUseCase, GetIssueDetailsUseCase, GetFullIssueDetailsUseCase,
    CreateIssueUseCase, AddCommentUseCase, TransitionIssueUseCase,
    GetIssueTransitionsUseCase, ChangeAssigneeUseCase, ListProjectTicketsUseCase,
    GetCustomFieldMappingsUseCase, GenerateWorkflowGraphUseCase, ListInstancesUseCase,
    UpdateIssueUseCase, CreateIssueLinkUseCase, CreateEpicStoryLinkUseCase,
    GetIssueLinksUseCase, SearchIssuesUseCase, LogWorkUseCase, GetWorkLogsUseCase,
    GetTimeTrackingInfoUseCase, UpdateTimeEstimatesUseCase, CreateIssueWithLinksUseCase,
    ValidateJQLUseCase
)
from domain.services import (
    IssueService, WorkflowService, ProjectService, VisualizationService, InstanceService,
    IssueUpdateService, IssueLinkService, SearchService, TimeTrackingService
)
from infrastructure.config_adapter import ConfigurationAdapter
from infrastructure.jira_client import (
    JiraClientFactoryImpl, JiraApiRepository, JiraIssueUpdateAdapter,
    JiraIssueLinkAdapter, JiraSearchAdapter, JiraTimeTrackingAdapter,
    JiraTimeFormatValidator, JiraJQLValidator
)
from infrastructure.graph_generator import GraphvizGenerator, WorkflowAnalyzerImpl, LoggerAdapter

logger = logging.getLogger(__name__)


class JiraHelperContext:
    """Context object containing all initialized services and use cases."""
    
    def __init__(
        self,
        # Services
        issue_service: IssueService,
        workflow_service: WorkflowService,
        project_service: ProjectService,
        visualization_service: VisualizationService,
        instance_service: InstanceService,
        issue_update_service: IssueUpdateService,
        issue_link_service: IssueLinkService,
        search_service: SearchService,
        time_tracking_service: TimeTrackingService,
        # Use cases
        list_projects_use_case: ListProjectsUseCase,
        get_issue_details_use_case: GetIssueDetailsUseCase,
        get_full_issue_details_use_case: GetFullIssueDetailsUseCase,
        create_issue_use_case: CreateIssueUseCase,
        add_comment_use_case: AddCommentUseCase,
        transition_issue_use_case: TransitionIssueUseCase,
        get_issue_transitions_use_case: GetIssueTransitionsUseCase,
        change_assignee_use_case: ChangeAssigneeUseCase,
        list_project_tickets_use_case: ListProjectTicketsUseCase,
        get_custom_field_mappings_use_case: GetCustomFieldMappingsUseCase,
        generate_workflow_graph_use_case: GenerateWorkflowGraphUseCase,
        list_instances_use_case: ListInstancesUseCase,
        # New use cases
        update_issue_use_case: UpdateIssueUseCase,
        create_issue_link_use_case: CreateIssueLinkUseCase,
        create_epic_story_link_use_case: CreateEpicStoryLinkUseCase,
        get_issue_links_use_case: GetIssueLinksUseCase,
        search_issues_use_case: SearchIssuesUseCase,
        log_work_use_case: LogWorkUseCase,
        get_work_logs_use_case: GetWorkLogsUseCase,
        get_time_tracking_info_use_case: GetTimeTrackingInfoUseCase,
        update_time_estimates_use_case: UpdateTimeEstimatesUseCase,
        create_issue_with_links_use_case: CreateIssueWithLinksUseCase,
        validate_jql_use_case: ValidateJQLUseCase
    ):
        # Services
        self.issue_service = issue_service
        self.workflow_service = workflow_service
        self.project_service = project_service
        self.visualization_service = visualization_service
        self.instance_service = instance_service
        self.issue_update_service = issue_update_service
        self.issue_link_service = issue_link_service
        self.search_service = search_service
        self.time_tracking_service = time_tracking_service
        
        # Use cases
        self.list_projects_use_case = list_projects_use_case
        self.get_issue_details_use_case = get_issue_details_use_case
        self.get_full_issue_details_use_case = get_full_issue_details_use_case
        self.create_issue_use_case = create_issue_use_case
        self.add_comment_use_case = add_comment_use_case
        self.transition_issue_use_case = transition_issue_use_case
        self.get_issue_transitions_use_case = get_issue_transitions_use_case
        self.change_assignee_use_case = change_assignee_use_case
        self.list_project_tickets_use_case = list_project_tickets_use_case
        self.get_custom_field_mappings_use_case = get_custom_field_mappings_use_case
        self.generate_workflow_graph_use_case = generate_workflow_graph_use_case
        self.list_instances_use_case = list_instances_use_case
        # New use cases
        self.update_issue_use_case = update_issue_use_case
        self.create_issue_link_use_case = create_issue_link_use_case
        self.create_epic_story_link_use_case = create_epic_story_link_use_case
        self.get_issue_links_use_case = get_issue_links_use_case
        self.search_issues_use_case = search_issues_use_case
        self.log_work_use_case = log_work_use_case
        self.get_work_logs_use_case = get_work_logs_use_case
        self.get_time_tracking_info_use_case = get_time_tracking_info_use_case
        self.update_time_estimates_use_case = update_time_estimates_use_case
        self.create_issue_with_links_use_case = create_issue_with_links_use_case
        self.validate_jql_use_case = validate_jql_use_case


@asynccontextmanager
async def jira_lifespan(server: FastMCP) -> AsyncIterator[JiraHelperContext]:
    """Manage application lifecycle with dependency injection."""
    logger.info("Initializing Jira Helper services...")
    
    try:
        # Initialize infrastructure layer
        config_provider = ConfigurationAdapter()
        client_factory = JiraClientFactoryImpl(config_provider)
        repository = JiraApiRepository(client_factory, config_provider)
        graph_generator = GraphvizGenerator()
        workflow_analyzer = WorkflowAnalyzerImpl()
        logger_adapter = LoggerAdapter()
        
        # Initialize infrastructure adapters
        issue_update_adapter = JiraIssueUpdateAdapter(client_factory, config_provider)
        issue_link_adapter = JiraIssueLinkAdapter(client_factory, config_provider)
        search_adapter = JiraSearchAdapter(client_factory, config_provider)
        time_tracking_adapter = JiraTimeTrackingAdapter(client_factory, config_provider)
        time_format_validator = JiraTimeFormatValidator()
        
        # Initialize domain services
        issue_service = IssueService(repository, config_provider, logger_adapter)
        workflow_service = WorkflowService(repository, config_provider, logger_adapter)
        project_service = ProjectService(repository, config_provider, logger_adapter)
        visualization_service = VisualizationService(
            repository, config_provider, graph_generator, workflow_analyzer, logger_adapter
        )
        instance_service = InstanceService(config_provider, logger_adapter)
        
        # Initialize new domain services
        issue_update_service = IssueUpdateService(issue_update_adapter, repository, config_provider, logger_adapter)
        issue_link_service = IssueLinkService(issue_link_adapter, repository, config_provider, None, logger_adapter)
        search_service = SearchService(search_adapter, config_provider, JiraJQLValidator(), logger_adapter)
        time_tracking_service = TimeTrackingService(time_tracking_adapter, repository, config_provider, time_format_validator, logger_adapter)
        
        # Initialize use cases
        list_projects_use_case = ListProjectsUseCase(project_service)
        get_issue_details_use_case = GetIssueDetailsUseCase(issue_service)
        get_full_issue_details_use_case = GetFullIssueDetailsUseCase(issue_service)
        create_issue_use_case = CreateIssueUseCase(issue_service)
        add_comment_use_case = AddCommentUseCase(issue_service)
        transition_issue_use_case = TransitionIssueUseCase(workflow_service)
        get_issue_transitions_use_case = GetIssueTransitionsUseCase(workflow_service)
        change_assignee_use_case = ChangeAssigneeUseCase(workflow_service)
        list_project_tickets_use_case = ListProjectTicketsUseCase(issue_service)
        get_custom_field_mappings_use_case = GetCustomFieldMappingsUseCase(project_service)
        generate_workflow_graph_use_case = GenerateWorkflowGraphUseCase(visualization_service)
        list_instances_use_case = ListInstancesUseCase(instance_service)
        
        # Initialize new use cases
        update_issue_use_case = UpdateIssueUseCase(issue_update_service)
        create_issue_link_use_case = CreateIssueLinkUseCase(issue_link_service)
        create_epic_story_link_use_case = CreateEpicStoryLinkUseCase(issue_link_service)
        get_issue_links_use_case = GetIssueLinksUseCase(issue_link_service)
        search_issues_use_case = SearchIssuesUseCase(search_service)
        log_work_use_case = LogWorkUseCase(time_tracking_service)
        get_work_logs_use_case = GetWorkLogsUseCase(time_tracking_service)
        get_time_tracking_info_use_case = GetTimeTrackingInfoUseCase(time_tracking_service)
        update_time_estimates_use_case = UpdateTimeEstimatesUseCase(time_tracking_service)
        create_issue_with_links_use_case = CreateIssueWithLinksUseCase(issue_service, issue_link_service)
        validate_jql_use_case = ValidateJQLUseCase(search_service)
        
        # Create context
        context = JiraHelperContext(
            # Services
            issue_service=issue_service,
            workflow_service=workflow_service,
            project_service=project_service,
            visualization_service=visualization_service,
            instance_service=instance_service,
            issue_update_service=issue_update_service,
            issue_link_service=issue_link_service,
            search_service=search_service,
            time_tracking_service=time_tracking_service,
            # Use cases
            list_projects_use_case=list_projects_use_case,
            get_issue_details_use_case=get_issue_details_use_case,
            get_full_issue_details_use_case=get_full_issue_details_use_case,
            create_issue_use_case=create_issue_use_case,
            add_comment_use_case=add_comment_use_case,
            transition_issue_use_case=transition_issue_use_case,
            get_issue_transitions_use_case=get_issue_transitions_use_case,
            change_assignee_use_case=change_assignee_use_case,
            list_project_tickets_use_case=list_project_tickets_use_case,
            get_custom_field_mappings_use_case=get_custom_field_mappings_use_case,
            generate_workflow_graph_use_case=generate_workflow_graph_use_case,
            list_instances_use_case=list_instances_use_case,
            # New use cases
            update_issue_use_case=update_issue_use_case,
            create_issue_link_use_case=create_issue_link_use_case,
            create_epic_story_link_use_case=create_epic_story_link_use_case,
            get_issue_links_use_case=get_issue_links_use_case,
            search_issues_use_case=search_issues_use_case,
            log_work_use_case=log_work_use_case,
            get_work_logs_use_case=get_work_logs_use_case,
            get_time_tracking_info_use_case=get_time_tracking_info_use_case,
            update_time_estimates_use_case=update_time_estimates_use_case,
            create_issue_with_links_use_case=create_issue_with_links_use_case,
            validate_jql_use_case=validate_jql_use_case
        )
        
        logger.info("Jira Helper services initialized successfully")
        yield context
        
    except Exception as e:
        logger.error(f"Failed to initialize Jira Helper services: {str(e)}")
        raise
    finally:
        logger.info("Shutting down Jira Helper services...")


# Create the FastMCP server with lifespan management
mcp = FastMCP("Jira Helper", lifespan=jira_lifespan)


# MCP Tool Implementations using shared tool definitions
# This ensures DRY compliance between direct and HTTP adapters

# Register all MCP tools using shared tool definitions
@mcp.tool()
async def list_jira_projects(instance_name: Optional[str] = None) -> Dict[str, Any]:
    """List all projects available in the Jira instance."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["list_jira_projects"](instance_name)

@mcp.tool()
async def get_issue_details(issue_key: str, instance_name: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed information about a specific Jira issue."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["get_issue_details"](issue_key, instance_name)


@mcp.tool()
async def get_full_issue_details(
    issue_key: str, 
    raw_data: bool = False, 
    format: str = "formatted",
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get comprehensive information about a specific Jira issue with formatting options.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        raw_data: If True, returns the minimally processed raw data from Jira API (default: False)
        format: Output format when raw_data is False - can be "formatted" (YAML-like) or "summary" (default: "formatted")
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing issue details in the requested format
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.get_full_issue_details_use_case.execute(
            issue_key, raw_data, format, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in get_full_issue_details: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "instance_name": instance_name}
        }


@mcp.tool()
async def create_jira_ticket(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Story",
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[list[str]] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Jira ticket (issue).

    Args:
        project_key: The project key (e.g., 'PROJ')
        summary: The ticket summary/title
        description: The ticket description
        issue_type: The issue type (Story, Task, Epic, Bug) - defaults to "Story"
        priority: Optional priority (e.g., "High", "Medium", "Low")
        assignee: Optional username to assign the ticket to
        labels: Optional list of labels to apply to the ticket
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the created issue details
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.create_issue_use_case.execute(
            project_key, summary, description, issue_type, priority, assignee, labels, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in create_jira_ticket: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"project_key": project_key, "summary": summary}
        }


@mcp.tool()
async def add_comment_to_jira_ticket(
    issue_key: str, 
    comment: str, 
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a comment to an existing Jira ticket.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        comment: The comment text to add
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the comment details and status
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.add_comment_use_case.execute(issue_key, comment, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in add_comment_to_jira_ticket: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key}
        }


@mcp.tool()
async def transition_jira_issue(
    issue_key: str,
    transition_name: str,
    comment: Optional[str] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transition a Jira issue through its workflow (e.g., move from "To Do" to "In Progress").

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        transition_name: Name of the transition to execute (e.g., "Start Progress", "Done")
        comment: Optional comment to add when transitioning
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the transition result and new status
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.transition_issue_use_case.execute(
            issue_key, transition_name, comment, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in transition_jira_issue: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "transition_name": transition_name}
        }


@mcp.tool()
async def get_issue_transitions(
    issue_key: str, 
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get available workflow transitions for a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing available transitions and current status
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.get_issue_transitions_use_case.execute(issue_key, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in get_issue_transitions: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key}
        }


@mcp.tool()
async def change_issue_assignee(
    issue_key: str,
    assignee: Optional[str] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Change the assignee of a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        assignee: Username or email of the new assignee. Use None or empty string to unassign.
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the assignment result
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.change_assignee_use_case.execute(issue_key, assignee, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in change_issue_assignee: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "assignee": assignee}
        }


@mcp.tool()
async def list_project_tickets(
    project_key: str,
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    max_results: int = 50,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    List tickets (issues) in a Jira project with optional filtering.

    Args:
        project_key: The project key (e.g., 'PROJ')
        status: Optional filter by status (e.g., "In Progress", "Done")
        issue_type: Optional filter by issue type (e.g., "Story", "Bug")
        max_results: Maximum number of results to return (default 50)
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing a list of matching tickets
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.list_project_tickets_use_case.execute(
            project_key, status, issue_type, max_results, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in list_project_tickets: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"project_key": project_key}
        }


@mcp.tool()
async def get_custom_field_mappings(
    reverse: bool = False, 
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get mappings between Jira custom field IDs and their names/descriptions. If you have a dataset
    with custom field IDs such as the way data gets returned from the Jira API, you can use this to translate to 
    human-readable names. Similarly if you need to map from human-readable names to IDs, you can use the reverse option.
    This is useful for understanding the custom fields in your Jira instance.

    Args:
        reverse: If False (default), map from field_id to (name, description)
                If True, map from name to (field_id, description)
        instance_name: Name of the Jira instance to use. If None, uses default instance.
    
    Returns:
        A dictionary containing the custom field mappings
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.get_custom_field_mappings_use_case.execute(reverse, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in get_custom_field_mappings: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"reverse": reverse}
        }


@mcp.tool()
async def generate_project_workflow_graph(
    project_key: str,
    issue_type: str = "Story",
    format: str = "svg",
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a visual workflow graph for a specific project and issue type.

    Args:
        project_key: The project key (e.g., 'PROJ')
        issue_type: The issue type to analyze workflow for (default: "Story")
        format: Output format - "svg", "png", "dot", or "json" (default: "svg")
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the workflow graph data
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.generate_workflow_graph_use_case.execute(
            project_key, issue_type, format, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in generate_project_workflow_graph: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"project_key": project_key, "issue_type": issue_type}
        }


@mcp.tool()
async def list_jira_instances() -> Dict[str, Any]:
    """
    List all configured Jira instances.

    Returns:
        A dictionary containing information about all configured Jira instances
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.list_instances_use_case.execute()
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in list_jira_instances: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def update_jira_issue(
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[list[str]] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Jira issue with new field values.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        summary: Optional new summary/title
        description: Optional new description
        priority: Optional new priority (e.g., "High", "Medium", "Low")
        assignee: Optional new assignee username
        labels: Optional new list of labels
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the update result
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.update_issue_use_case.execute(
            issue_key, summary, description, priority, assignee, labels, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in update_jira_issue: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "instance_name": instance_name}
        }


@mcp.tool()
async def search_jira_issues(
    jql: str,
    max_results: int = 50,
    start_at: int = 0,
    fields: Optional[list[str]] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a JQL search query to find Jira issues.

    Args:
        jql: The JQL (Jira Query Language) search string
        max_results: Maximum number of results to return (default 50, max 1000)
        start_at: Starting index for pagination (default 0)
        fields: Optional list of fields to include in results
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing search results with pagination info
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.search_issues_use_case.execute(
            jql, max_results, start_at, fields, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in search_jira_issues: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"jql": jql, "instance_name": instance_name}
        }


@mcp.tool()
async def validate_jql_query(
    jql: str,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate JQL syntax without executing the query.

    Args:
        jql: The JQL (Jira Query Language) string to validate
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing validation results
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.validate_jql_use_case.execute(jql, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in validate_jql_query: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"jql": jql, "instance_name": instance_name}
        }


@mcp.tool()
async def create_issue_link(
    source_issue: str,
    target_issue: str,
    link_type: str,
    direction: str = "outward",
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a link between two Jira issues.

    Args:
        source_issue: The source issue key (e.g., 'PROJECT-123')
        target_issue: The target issue key (e.g., 'PROJECT-456')
        link_type: Type of link (e.g., 'Blocks', 'Relates', 'Epic-Story', 'Parent-Child')
        direction: Link direction - 'outward' or 'inward' (default: 'outward')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the link creation result
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.create_issue_link_use_case.execute(
            source_issue, target_issue, link_type, direction, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in create_issue_link: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {
                "source_issue": source_issue,
                "target_issue": target_issue,
                "link_type": link_type,
                "instance_name": instance_name
            }
        }


@mcp.tool()
async def create_epic_story_link(
    epic_key: str,
    story_key: str,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an Epic-Story link between two issues.

    Args:
        epic_key: The Epic issue key (e.g., 'PROJECT-123')
        story_key: The Story issue key (e.g., 'PROJECT-456')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the Epic-Story link creation result
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.create_epic_story_link_use_case.execute(
            epic_key, story_key, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in create_epic_story_link: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {
                "epic_key": epic_key,
                "story_key": story_key,
                "instance_name": instance_name
            }
        }


@mcp.tool()
async def get_issue_links(
    issue_key: str,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all links for a specific Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing all links for the issue
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.get_issue_links_use_case.execute(issue_key, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in get_issue_links: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "instance_name": instance_name}
        }


@mcp.tool()
async def create_jira_ticket_with_links(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Story",
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[list[str]] = None,
    links: Optional[list[dict]] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Jira ticket with links to other issues.

    Args:
        project_key: The project key (e.g., 'PROJ')
        summary: The ticket summary/title
        description: The ticket description
        issue_type: The issue type (Story, Task, Epic, Bug) - defaults to "Story"
        priority: Optional priority (e.g., "High", "Medium", "Low")
        assignee: Optional username to assign the ticket to
        labels: Optional list of labels to apply to the ticket
        links: Optional list of link objects with keys: link_type, source_issue, target_issue, direction
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the created issue details and link results
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.create_issue_with_links_use_case.execute(
            project_key, summary, description, issue_type, priority, assignee, labels, links, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in create_jira_ticket_with_links: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"project_key": project_key, "summary": summary, "instance_name": instance_name}
        }


@mcp.tool()
async def log_work_on_issue(
    issue_key: str,
    time_spent: str,
    comment: str = "",
    started: Optional[str] = None,
    adjust_estimate: str = "auto",
    new_estimate: Optional[str] = None,
    reduce_by: Optional[str] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log work time on a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        time_spent: Time spent in Jira format (e.g., '2h 30m', '1d', '4h')
        comment: Optional comment describing the work done
        started: Optional start time in ISO format (e.g., '2023-01-01T09:00:00.000+0000')
        adjust_estimate: How to adjust remaining estimate - 'auto', 'new', 'manual', or 'leave'
        new_estimate: New remaining estimate if adjust_estimate is 'new'
        reduce_by: Amount to reduce estimate by if adjust_estimate is 'manual'
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the work log result
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.log_work_use_case.execute(
            issue_key, time_spent, comment, started, adjust_estimate, new_estimate, reduce_by, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in log_work_on_issue: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "time_spent": time_spent, "instance_name": instance_name}
        }


@mcp.tool()
async def get_work_logs(
    issue_key: str,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all work logs for a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing all work logs for the issue
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.get_work_logs_use_case.execute(issue_key, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in get_work_logs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "instance_name": instance_name}
        }


@mcp.tool()
async def get_time_tracking_info(
    issue_key: str,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get time tracking information for a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing time tracking information
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.get_time_tracking_info_use_case.execute(issue_key, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in get_time_tracking_info: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "instance_name": instance_name}
        }


@mcp.tool()
async def update_time_estimates(
    issue_key: str,
    original_estimate: Optional[str] = None,
    remaining_estimate: Optional[str] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update time estimates for a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        original_estimate: New original estimate in Jira format (e.g., '2h 30m', '1d')
        remaining_estimate: New remaining estimate in Jira format (e.g., '1h 15m')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing the time estimate update result
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.update_time_estimates_use_case.execute(
            issue_key, original_estimate, remaining_estimate, instance_name
        )
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in update_time_estimates: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {
                "issue_key": issue_key,
                "original_estimate": original_estimate,
                "remaining_estimate": remaining_estimate,
                "instance_name": instance_name
            }
        }


# Export the MCP server for use in main.py
__all__ = ["mcp"]
