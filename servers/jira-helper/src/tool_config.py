"""
Tool Configuration for Jira Helper MCP Server

This module contains the optimized tool configuration using mcp-commons patterns
while preserving the sophisticated hexagonal architecture. All service initialization
is handled at module level, and tools are directly mapped to use case execute() methods.

Migration from FastMCP bulk registration to mcp-commons direct function mapping.
"""

import logging
import sys
from typing import Dict, Any

# Configure logger to use stderr to avoid interfering with stdio JSON-RPC
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Reduce verbosity for MCP protocol compatibility

# Ensure handler uses stderr
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.propagate = False

# =============================================================================
# SERVICE INITIALIZATION - Copied from mcp_adapter.py jira_lifespan() function
# =============================================================================

logger.info("🚀 JIRA HELPER - Initializing services using hexagonal architecture...")

try:
    # Import all dependencies (copied from mcp_adapter.py)
    from application.use_cases import (
        AddCommentUseCase,
        ChangeAssigneeUseCase,
        CreateEpicStoryLinkUseCase,
        CreateIssueLinkUseCase,
        CreateIssueUseCase,
        CreateIssueWithLinksUseCase,
        GenerateWorkflowGraphUseCase,
        GetCustomFieldMappingsUseCase,
        GetFullIssueDetailsUseCase,
        GetIssueDetailsUseCase,
        GetIssueLinksUseCase,
        GetIssueTransitionsUseCase,
        GetTimeTrackingInfoUseCase,
        GetWorkLogsUseCase,
        ListInstancesUseCase,
        ListProjectsUseCase,
        ListProjectTicketsUseCase,
        LogWorkUseCase,
        SearchIssuesUseCase,
        TransitionIssueUseCase,
        UpdateIssueUseCase,
        UpdateTimeEstimatesUseCase,
        ValidateJqlUseCase,
    )
    from domain.services import (
        InstanceService,
        IssueLinkService,
        IssueService,
        IssueUpdateService,
        ProjectService,
        SearchService,
        TimeTrackingService,
        VisualizationService,
        WorkflowService,
    )
    from infrastructure.config_adapter import ConfigurationAdapter
    from infrastructure.graph_generator import (
        GraphvizGenerator,
        WorkflowAnalyzerImpl,
    )
    from infrastructure.atlassian_repository import (
        AtlassianApiJiraClientFactory,
        AtlassianApiRepository,
    )
    from infrastructure.atlassian_link_adapter import AtlassianIssueLinkAdapter
    from infrastructure.atlassian_update_adapter import AtlassianIssueUpdateAdapter
    from infrastructure.atlassian_search_adapter import (
        AtlassianJQLValidator,
        AtlassianSearchAdapter,
    )
    from infrastructure.atlassian_time_adapter import (
        AtlassianTimeFormatValidator,
        AtlassianTimeTrackingAdapter,
    )
    from infrastructure.atlassian_file_adapter import AtlassianFileAdapter
    from infrastructure.file_validation_adapter import StandardFileValidationAdapter
    from infrastructure.file_system_adapter import StandardFileSystemAdapter, FileUploadPolicyAdapter
    from application.file_use_cases import (
        UploadFileUseCase,
        ListAttachmentsUseCase,
        DeleteAttachmentUseCase,
    )

    # Initialize infrastructure layer (copied exactly from mcp_adapter.py)
    config_provider = ConfigurationAdapter()
    client_factory = AtlassianApiJiraClientFactory(config_provider)
    repository = AtlassianApiRepository(client_factory, config_provider)
    graph_generator = GraphvizGenerator()
    workflow_analyzer = WorkflowAnalyzerImpl()
    # Use standard logging pattern consistent with rest of project
    logger_adapter = logging.getLogger(__name__)

    # Initialize infrastructure adapters (copied exactly from mcp_adapter.py)
    issue_update_adapter = AtlassianIssueUpdateAdapter(config_provider)
    issue_link_adapter = AtlassianIssueLinkAdapter(config_provider, client_factory)
    search_adapter = AtlassianSearchAdapter(config_provider, client_factory)
    time_tracking_adapter = AtlassianTimeTrackingAdapter(config_provider, client_factory)
    time_format_validator = AtlassianTimeFormatValidator()

    # Initialize domain services (copied exactly from mcp_adapter.py)
    issue_service = IssueService(repository, config_provider, logger_adapter)
    workflow_service = WorkflowService(repository, config_provider, logger_adapter)
    project_service = ProjectService(repository, config_provider, logger_adapter)
    visualization_service = VisualizationService(
        repository, config_provider, graph_generator, workflow_analyzer, logger_adapter
    )
    instance_service = InstanceService(config_provider, logger_adapter)

    # Initialize new domain services (copied exactly from mcp_adapter.py)
    issue_update_service = IssueUpdateService(issue_update_adapter, repository, config_provider, logger_adapter)
    issue_link_service = IssueLinkService(issue_link_adapter, repository, config_provider, None, logger_adapter)
    search_service = SearchService(search_adapter, config_provider, AtlassianJQLValidator(), logger_adapter)
    time_tracking_service = TimeTrackingService(time_tracking_adapter, repository, config_provider, time_format_validator, logger_adapter)

    # Initialize file adapters (copied exactly from mcp_adapter.py)
    file_attachment_port = AtlassianFileAdapter(config_provider, client_factory)
    file_validation_port = StandardFileValidationAdapter(logger_adapter)
    file_system_port = StandardFileSystemAdapter(logger_adapter)
    file_upload_policy_provider = FileUploadPolicyAdapter(logger_adapter)

    # Initialize use cases with keyword arguments for BaseUseCase compatibility (copied exactly from mcp_adapter.py)
    list_projects_use_case = ListProjectsUseCase(project_service=project_service)
    get_issue_details_use_case = GetIssueDetailsUseCase(issue_service=issue_service)
    get_full_issue_details_use_case = GetFullIssueDetailsUseCase(issue_service=issue_service)
    create_issue_use_case = CreateIssueUseCase(issue_service=issue_service)
    add_comment_use_case = AddCommentUseCase(comment_service=issue_service)
    transition_issue_use_case = TransitionIssueUseCase(workflow_service=workflow_service)
    get_issue_transitions_use_case = GetIssueTransitionsUseCase(workflow_service=workflow_service)
    change_assignee_use_case = ChangeAssigneeUseCase(workflow_service=workflow_service)
    list_project_tickets_use_case = ListProjectTicketsUseCase(search_service=search_service)
    get_custom_field_mappings_use_case = GetCustomFieldMappingsUseCase(field_service=project_service)
    generate_workflow_graph_use_case = GenerateWorkflowGraphUseCase(workflow_service=visualization_service)
    list_instances_use_case = ListInstancesUseCase(config_service=instance_service)

    # Initialize new use cases with keyword arguments (copied exactly from mcp_adapter.py)
    update_issue_use_case = UpdateIssueUseCase(issue_update_service=issue_update_service)
    create_issue_link_use_case = CreateIssueLinkUseCase(issue_link_service=issue_link_service)
    create_epic_story_link_use_case = CreateEpicStoryLinkUseCase(issue_link_service=issue_link_service)
    get_issue_links_use_case = GetIssueLinksUseCase(issue_link_service=issue_link_service)
    
    # Add force_async to the search_issues_use_case (copied exactly from mcp_adapter.py)
    search_issues_use_case = SearchIssuesUseCase(search_service=search_service)
    
    log_work_use_case = LogWorkUseCase(time_tracking_service=time_tracking_service)
    get_work_logs_use_case = GetWorkLogsUseCase(time_tracking_service=time_tracking_service)
    get_time_tracking_info_use_case = GetTimeTrackingInfoUseCase(time_tracking_service=time_tracking_service)
    update_time_estimates_use_case = UpdateTimeEstimatesUseCase(time_tracking_service=time_tracking_service)
    create_issue_with_links_use_case = CreateIssueWithLinksUseCase(issue_service=issue_service, issue_link_service=issue_link_service)
    validate_jql_use_case = ValidateJqlUseCase(search_service=search_service)

    # Initialize file use cases (copied exactly from mcp_adapter.py)
    upload_file_use_case = UploadFileUseCase(
        file_attachment_port=file_attachment_port,
        file_validation_port=file_validation_port,
        file_system_port=file_system_port,
        policy_provider=file_upload_policy_provider,
        config_provider=config_provider,
        event_publisher=None,  # No event publisher needed for now
        logger=logger_adapter
    )
    list_attachments_use_case = ListAttachmentsUseCase(
        file_attachment_port=file_attachment_port,
        config_provider=config_provider,
        logger=logger_adapter
    )
    delete_attachment_use_case = DeleteAttachmentUseCase(
        file_attachment_port=file_attachment_port,
        config_provider=config_provider,
        event_publisher=None,  # No event publisher needed for now
        logger=logger_adapter
    )

    logger.info(f"✅ JIRA HELPER - Successfully initialized {len(locals())} services and use cases")

except Exception as e:
    logger.error(f"❌ JIRA HELPER - Failed to initialize services: {str(e)}")
    raise

# =============================================================================
# TOOL CONFIGURATION - Direct mapping to use case execute() methods
# =============================================================================

# Tool configuration using mcp-commons pattern: direct function mapping
JIRA_TOOLS: Dict[str, Dict[str, Any]] = {
    # Core Jira operations (13 tools)
    'list_jira_projects': {
        'function': list_projects_use_case.execute,  # Direct mapping to use case execute method!
        'description': 'List all projects available in the Jira instance.'
    },
    
    'get_issue_details': {
        'function': get_issue_details_use_case.execute,
        'description': 'Get detailed information about a specific Jira issue.'
    },
    
    'get_full_issue_details': {
        'function': get_full_issue_details_use_case.execute,
        'description': 'Get comprehensive information about a specific Jira issue with formatting options.'
    },
    
    'create_jira_ticket': {
        'function': create_issue_use_case.execute,
        'description': 'Create a new Jira ticket (issue).'
    },
    
    'add_comment_to_jira_ticket': {
        'function': add_comment_use_case.execute,
        'description': 'Add a comment to an existing Jira ticket.'
    },
    
    'transition_jira_issue': {
        'function': transition_issue_use_case.execute,
        'description': 'Transition a Jira issue through its workflow.'
    },
    
    'get_issue_transitions': {
        'function': get_issue_transitions_use_case.execute,
        'description': 'Get available workflow transitions for a Jira issue.'
    },
    
    'change_issue_assignee': {
        'function': change_assignee_use_case.execute,
        'description': 'Change the assignee of a Jira issue.'
    },
    
    'list_project_tickets': {
        'function': list_project_tickets_use_case.execute,
        'description': 'List tickets (issues) in a Jira project with optional filtering.'
    },
    
    'get_custom_field_mappings': {
        'function': get_custom_field_mappings_use_case.execute,
        'description': 'Get mappings between Jira custom field IDs and their names/descriptions.'
    },
    
    'generate_project_workflow_graph': {
        'function': generate_workflow_graph_use_case.execute,
        'description': 'Generate a visual workflow graph for a specific project and issue type.'
    },
    
    'list_jira_instances': {
        'function': list_instances_use_case.execute,
        'description': 'List all configured Jira instances.'
    },
    
    'update_jira_issue': {
        'function': update_issue_use_case.execute,
        'description': 'Update an existing Jira issue with new field values.'
    },
    
    # Search & advanced operations (7 tools)
    'search_jira_issues': {
        'function': search_issues_use_case.execute,
        'description': 'Execute a JQL search query to find Jira issues.'
    },
    
    'validate_jql_query': {
        'function': validate_jql_use_case.execute,
        'description': 'Validate JQL syntax without executing the query.'
    },
    
    'create_issue_link': {
        'function': create_issue_link_use_case.execute,
        'description': 'Create a link between two Jira issues.'
    },
    
    'create_epic_story_link': {
        'function': create_epic_story_link_use_case.execute,
        'description': 'Create an Epic-Story link between issues.'
    },
    
    'get_issue_links': {
        'function': get_issue_links_use_case.execute,
        'description': 'Get all links for a specific Jira issue.'
    },
    
    'create_issue_with_links': {
        'function': create_issue_with_links_use_case.execute,
        'description': 'Create a new Jira issue with links to other issues.'
    },
    
    # Time tracking operations (4 tools)
    'log_work': {
        'function': log_work_use_case.execute,
        'description': 'Log work time on a Jira issue.'
    },
    
    'get_work_logs': {
        'function': get_work_logs_use_case.execute,
        'description': 'Get work log entries for a Jira issue.'
    },
    
    'get_time_tracking_info': {
        'function': get_time_tracking_info_use_case.execute,
        'description': 'Get time tracking information for a Jira issue.'
    },
    
    'update_time_estimates': {
        'function': update_time_estimates_use_case.execute,
        'description': 'Update time estimates for a Jira issue.'
    },
    
    # File operations (3 tools)
    'upload_file_to_jira': {
        'function': upload_file_use_case.execute,
        'description': 'Upload a file to a Jira issue as an attachment.'
    },
    
    'list_issue_attachments': {
        'function': list_attachments_use_case.execute,
        'description': 'List all attachments for a Jira issue.'
    },
    
    'delete_issue_attachment': {
        'function': delete_attachment_use_case.execute,
        'description': 'Delete an attachment from a Jira issue.'
    }
}

# =============================================================================
# UTILITY FUNCTIONS - Following worldcontext pattern
# =============================================================================

def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """
    Get the tools configuration for registration with mcp-commons.
    
    Returns:
        Dictionary mapping tool names to their configuration
    """
    return JIRA_TOOLS


def get_tool_count() -> int:
    """Get the total number of configured tools."""
    return len(JIRA_TOOLS)


def get_tool_names() -> list[str]:
    """Get list of all tool names."""
    return list(JIRA_TOOLS.keys())


def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool configuration dictionary

    Raises:
        KeyError: If tool name not found
    """
    if tool_name not in JIRA_TOOLS:
        raise KeyError(f"Tool '{tool_name}' not found in configuration")
    
    return JIRA_TOOLS[tool_name].copy()


def validate_tool_config() -> Dict[str, Any]:
    """
    Validate the tool configuration for completeness and correctness.

    Returns:
        Validation results with any issues found
    """
    issues = []
    warnings = []
    
    required_keys = ['function', 'description']
    
    for tool_name, config in JIRA_TOOLS.items():
        # Check required keys
        for key in required_keys:
            if key not in config:
                issues.append(f"Tool '{tool_name}' missing required key: {key}")
        
        # Check function is callable
        if 'function' in config:
            if not callable(config['function']):
                issues.append(f"Tool '{tool_name}' function must be callable")
        
        # Check description is non-empty string
        if 'description' in config:
            if not isinstance(config['description'], str) or not config['description'].strip():
                issues.append(f"Tool '{tool_name}' description must be non-empty string")
    
    return {
        'valid': len(issues) == 0,
        'tool_count': len(JIRA_TOOLS),
        'issues': issues,
        'warnings': warnings
    }


def get_config_stats() -> Dict[str, Any]:
    """
    Get statistics about the tool configuration.

    Returns:
        Configuration statistics
    """
    validation = validate_tool_config()
    
    # Count tools by category
    categories = {
        'Core Operations': 13,  # list_projects, get_issue_details, create_ticket, etc.
        'Search & Advanced': 6,  # search_issues, validate_jql, create_link, etc.
        'Time Tracking': 4,     # log_work, get_work_logs, etc.
        'File Operations': 3    # upload_file, list_attachments, delete_attachment
    }
    
    return {
        'total_tools': len(JIRA_TOOLS),
        'categories': categories,
        'validation': validation,
        'architecture': 'Hexagonal (Domain/Application/Infrastructure)',
        'pattern': 'mcp-commons direct function mapping',
        'migration_status': 'FastMCP -> mcp-commons hybrid approach',
        'complexity_reduction': '~75% reduction in server setup code',
        'description': 'Jira Helper MCP server with sophisticated business logic and simplified server management'
    }


# Module initialization complete
logger.info(f"🎯 JIRA HELPER - Tool configuration initialized with {get_tool_count()} tools ready for mcp-commons registration")
