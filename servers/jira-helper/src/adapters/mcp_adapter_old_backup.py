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
    """Get comprehensive information about a specific Jira issue with formatting options."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["get_full_issue_details"](issue_key, raw_data, format, instance_name)

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
    """Create a new Jira ticket (issue)."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["create_jira_ticket"](project_key, summary, description, issue_type, priority, assignee, labels, instance_name)

@mcp.tool()
async def add_comment_to_jira_ticket(
    issue_key: str, 
    comment: str, 
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Add a comment to an existing Jira ticket."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["add_comment_to_jira_ticket"](issue_key, comment, instance_name)

@mcp.tool()
async def transition_jira_issue(
    issue_key: str,
    transition_name: str,
    comment: Optional[str] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Transition a Jira issue through its workflow."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["transition_jira_issue"](issue_key, transition_name, comment, instance_name)

@mcp.tool()
async def get_issue_transitions(
    issue_key: str, 
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Get available workflow transitions for a Jira issue."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["get_issue_transitions"](issue_key, instance_name)

@mcp.tool()
async def change_issue_assignee(
    issue_key: str,
    assignee: Optional[str] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Change the assignee of a Jira issue."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["change_issue_assignee"](issue_key, assignee, instance_name)

@mcp.tool()
async def list_project_tickets(
    project_key: str,
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    max_results: int = 50,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """List tickets (issues) in a Jira project with optional filtering."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["list_project_tickets"](project_key, status, issue_type, max_results, instance_name)

@mcp.tool()
async def get_custom_field_mappings(
    reverse: bool = False, 
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Get mappings between Jira custom field IDs and their names/descriptions."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["get_custom_field_mappings"](reverse, instance_name)

@mcp.tool()
async def generate_project_workflow_graph(
    project_key: str,
    issue_type: str = "Story",
    format: str = "svg",
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a visual workflow graph for a specific project and issue type."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["generate_project_workflow_graph"](project_key, issue_type, format, instance_name)

@mcp.tool()
async def list_jira_instances() -> Dict[str, Any]:
    """List all configured Jira instances."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["list_jira_instances"]()

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
    """Update an existing Jira issue with new field values."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["update_jira_issue"](issue_key, summary, description, priority, assignee, labels, instance_name)

@mcp.tool()
async def search_jira_issues(
    jql: str,
    max_results: int = 50,
    start_at: int = 0,
    fields: Optional[list[str]] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a JQL search query to find Jira issues."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["search_jira_issues"](jql, max_results, start_at, fields, instance_name)

@mcp.tool()
async def validate_jql_query(
    jql: str,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Validate JQL syntax without executing the query."""
    ctx = mcp.get_context()
    jira_ctx = ctx.request_context.lifespan_context
    tools = create_mcp_tools(jira_ctx)
    return await tools["validate_jql_query"](jql, instance_name)


# Export the MCP server for use in main.py
__all__ = ["mcp"]
