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

from application.use_cases import (
    ListProjectsUseCase, GetIssueDetailsUseCase, GetFullIssueDetailsUseCase,
    CreateIssueUseCase, AddCommentUseCase, TransitionIssueUseCase,
    GetIssueTransitionsUseCase, ChangeAssigneeUseCase, ListProjectTicketsUseCase,
    GetCustomFieldMappingsUseCase, GenerateWorkflowGraphUseCase, ListInstancesUseCase
)
from domain.services import (
    IssueService, WorkflowService, ProjectService, VisualizationService, InstanceService
)
from infrastructure.config_adapter import ConfigurationAdapter
from infrastructure.jira_client import JiraClientFactoryImpl, JiraApiRepository
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
        list_instances_use_case: ListInstancesUseCase
    ):
        # Services
        self.issue_service = issue_service
        self.workflow_service = workflow_service
        self.project_service = project_service
        self.visualization_service = visualization_service
        self.instance_service = instance_service
        
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
        
        # Initialize domain services
        issue_service = IssueService(repository, config_provider, logger_adapter)
        workflow_service = WorkflowService(repository, config_provider, logger_adapter)
        project_service = ProjectService(repository, config_provider, logger_adapter)
        visualization_service = VisualizationService(
            repository, config_provider, graph_generator, workflow_analyzer, logger_adapter
        )
        instance_service = InstanceService(config_provider, logger_adapter)
        
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
        
        # Create context
        context = JiraHelperContext(
            # Services
            issue_service=issue_service,
            workflow_service=workflow_service,
            project_service=project_service,
            visualization_service=visualization_service,
            instance_service=instance_service,
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
            list_instances_use_case=list_instances_use_case
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


# MCP Tool Implementations
# Each tool translates MCP parameters to use case calls and formats responses

@mcp.tool()
async def list_jira_projects(instance_name: Optional[str] = None) -> Dict[str, Any]:
    """
    List all projects available in the Jira instance.

    Args:
        instance_name: Name of the Jira instance to use. If None, uses default instance.

    Returns:
        A dictionary containing a list of Jira projects
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.list_projects_use_case.execute(instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in list_jira_projects: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"instance_name": instance_name}
        }


@mcp.tool()
async def get_issue_details(issue_key: str, instance_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJECT-123')
        instance_name: Name of the Jira instance to use. If None, uses default instance.
        
    Returns:
        A dictionary containing issue details
    """
    try:
        ctx = mcp.get_context()
        jira_ctx = ctx.request_context.lifespan_context
        
        result = await jira_ctx.get_issue_details_use_case.execute(issue_key, instance_name)
        
        if result.success:
            return result.data
        else:
            return {
                "success": False,
                "error": result.error,
                "details": result.details
            }
            
    except Exception as e:
        logger.error(f"Error in get_issue_details: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "details": {"issue_key": issue_key, "instance_name": instance_name}
        }


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


# Export the MCP server for use in main.py
__all__ = ["mcp"]
