"""
MCP adapter for the Jira Helper - Refactored Version.

This module implements the MCP server adapter using bulk registration
to eliminate boilerplate and simplify tool management.
"""

import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP

from adapters.mcp_bulk_registration import bulk_register_jira_tools, log_registration_summary
from application.use_cases import (
    ListProjectsUseCase, GetIssueDetailsUseCase, GetFullIssueDetailsUseCase,
    CreateIssueUseCase, AddCommentUseCase, TransitionIssueUseCase,
    GetIssueTransitionsUseCase, ChangeAssigneeUseCase, ListProjectTicketsUseCase,
    GetCustomFieldMappingsUseCase, GenerateWorkflowGraphUseCase, ListInstancesUseCase,
    UpdateIssueUseCase, CreateIssueLinkUseCase, CreateEpicStoryLinkUseCase,
    GetIssueLinksUseCase, SearchIssuesUseCase, LogWorkUseCase, GetWorkLogsUseCase,
    GetTimeTrackingInfoUseCase, UpdateTimeEstimatesUseCase, CreateIssueWithLinksUseCase,
    ValidateJqlUseCase
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
    """Context object containing all initialized services for bulk tool registration."""
    
    def __init__(
        self,
        # Services (mapped to dependency names in tool config)
        project_service: ProjectService,
        issue_service: IssueService,
        comment_service: IssueService,  # Comments handled by issue service
        workflow_service: WorkflowService,
        search_service: SearchService,
        field_service: ProjectService,  # Custom fields handled by project service
        config_service: InstanceService,  # Instance config handled by instance service
        # Additional services for extended functionality
        visualization_service: VisualizationService,
        issue_update_service: IssueUpdateService,
        issue_link_service: IssueLinkService,
        time_tracking_service: TimeTrackingService,
        # Use cases (for backward compatibility if needed)
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
        validate_jql_use_case: ValidateJqlUseCase
    ):
        # Services mapped to dependency names used in tool configuration
        self.project_service = project_service
        self.issue_service = issue_service
        self.comment_service = comment_service
        self.workflow_service = workflow_service
        self.search_service = search_service
        self.field_service = field_service
        self.config_service = config_service
        
        # Additional services
        self.visualization_service = visualization_service
        self.issue_update_service = issue_update_service
        self.issue_link_service = issue_link_service
        self.time_tracking_service = time_tracking_service
        
        # Use cases (for backward compatibility)
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
    """Manage application lifecycle with dependency injection and bulk tool registration."""
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
        
        # Initialize use cases with keyword arguments for BaseUseCase compatibility
        list_projects_use_case = ListProjectsUseCase(project_service=project_service)
        get_issue_details_use_case = GetIssueDetailsUseCase(issue_service=issue_service)
        get_full_issue_details_use_case = GetFullIssueDetailsUseCase(issue_service=issue_service)
        create_issue_use_case = CreateIssueUseCase(issue_service=issue_service)
        add_comment_use_case = AddCommentUseCase(issue_service=issue_service)
        transition_issue_use_case = TransitionIssueUseCase(workflow_service=workflow_service)
        get_issue_transitions_use_case = GetIssueTransitionsUseCase(workflow_service=workflow_service)
        change_assignee_use_case = ChangeAssigneeUseCase(workflow_service=workflow_service)
        list_project_tickets_use_case = ListProjectTicketsUseCase(issue_service=issue_service)
        get_custom_field_mappings_use_case = GetCustomFieldMappingsUseCase(project_service=project_service)
        generate_workflow_graph_use_case = GenerateWorkflowGraphUseCase(visualization_service=visualization_service)
        list_instances_use_case = ListInstancesUseCase(instance_service=instance_service)
        
        # Initialize new use cases with keyword arguments
        update_issue_use_case = UpdateIssueUseCase(issue_update_service=issue_update_service)
        create_issue_link_use_case = CreateIssueLinkUseCase(issue_link_service=issue_link_service)
        create_epic_story_link_use_case = CreateEpicStoryLinkUseCase(issue_link_service=issue_link_service)
        get_issue_links_use_case = GetIssueLinksUseCase(issue_link_service=issue_link_service)
        search_issues_use_case = SearchIssuesUseCase(search_service=search_service)
        log_work_use_case = LogWorkUseCase(time_tracking_service=time_tracking_service)
        get_work_logs_use_case = GetWorkLogsUseCase(time_tracking_service=time_tracking_service)
        get_time_tracking_info_use_case = GetTimeTrackingInfoUseCase(time_tracking_service=time_tracking_service)
        update_time_estimates_use_case = UpdateTimeEstimatesUseCase(time_tracking_service=time_tracking_service)
        create_issue_with_links_use_case = CreateIssueWithLinksUseCase(issue_service=issue_service, issue_link_service=issue_link_service)
        validate_jql_use_case = ValidateJqlUseCase(search_service=search_service)
        
        # Create context with service mappings for bulk registration
        context = JiraHelperContext(
            # Services mapped to dependency names
            project_service=project_service,
            issue_service=issue_service,
            comment_service=issue_service,  # Comments handled by issue service
            workflow_service=workflow_service,
            search_service=search_service,
            field_service=project_service,  # Custom fields handled by project service
            config_service=instance_service,  # Instance config handled by instance service
            # Additional services
            visualization_service=visualization_service,
            issue_update_service=issue_update_service,
            issue_link_service=issue_link_service,
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
        
        # Bulk register all MCP tools - this replaces 300+ lines of manual @mcp.tool() decorations
        logger.info("Starting bulk registration of MCP tools...")
        tool_tuples = bulk_register_jira_tools(context)
        
        # Register tools with FastMCP server
        for func, name, description in tool_tuples:
            server.add_tool(func, name=name, description=description)
        
        # Log registration summary
        log_registration_summary(tool_tuples, context)
        
        logger.info("Jira Helper services and MCP tools initialized successfully")
        yield context
        
    except Exception as e:
        logger.error(f"Failed to initialize Jira Helper services: {str(e)}")
        raise
    finally:
        logger.info("Shutting down Jira Helper services...")


# Create the FastMCP server with lifespan management
# No manual tool registrations needed - all handled by bulk registration
mcp = FastMCP("Jira Helper", lifespan=jira_lifespan)

# Export the MCP server for use in main.py
__all__ = ["mcp"]
