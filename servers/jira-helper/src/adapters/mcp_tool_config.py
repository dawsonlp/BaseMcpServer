"""
MCP Tool Configuration

This module contains the metadata configuration for all Jira MCP tools.
This single source of truth replaces manual tool registration and enables
bulk registration with proper dependency injection.
"""

from typing import Dict, Any, Type
from application.use_cases import (
    ListProjectsUseCase,
    GetIssueDetailsUseCase,
    GetFullIssueDetailsUseCase,
    CreateIssueUseCase,
    AddCommentUseCase,
    TransitionIssueUseCase,
    GetIssueTransitionsUseCase,
    ChangeAssigneeUseCase,
    ListProjectTicketsUseCase,
    ListInstancesUseCase,
    GetCustomFieldMappingsUseCase,
    GenerateWorkflowGraphUseCase,
    UpdateIssueUseCase,
    SearchIssuesUseCase,
    ValidateJqlUseCase
)


# Complete tool configuration - single source of truth for all Jira MCP tools
JIRA_TOOLS: Dict[str, Dict[str, Any]] = {
    'list_jira_projects': {
        'use_case_class': ListProjectsUseCase,
        'description': 'List all projects available in the Jira instance.',
        'dependencies': ['project_service']
    },
    
    'get_issue_details': {
        'use_case_class': GetIssueDetailsUseCase,
        'description': 'Get detailed information about a specific Jira issue.',
        'dependencies': ['issue_service']
    },
    
    'get_full_issue_details': {
        'use_case_class': GetFullIssueDetailsUseCase,
        'description': 'Get comprehensive information about a specific Jira issue with formatting options.',
        'dependencies': ['issue_service']
    },
    
    'create_jira_ticket': {
        'use_case_class': CreateIssueUseCase,
        'description': 'Create a new Jira ticket (issue).',
        'dependencies': ['issue_service']
    },
    
    'add_comment_to_jira_ticket': {
        'use_case_class': AddCommentUseCase,
        'description': 'Add a comment to an existing Jira ticket.',
        'dependencies': ['comment_service']
    },
    
    'transition_jira_issue': {
        'use_case_class': TransitionIssueUseCase,
        'description': 'Transition a Jira issue through its workflow.',
        'dependencies': ['workflow_service']
    },
    
    'get_issue_transitions': {
        'use_case_class': GetIssueTransitionsUseCase,
        'description': 'Get available workflow transitions for a Jira issue.',
        'dependencies': ['workflow_service']
    },
    
    'change_issue_assignee': {
        'use_case_class': ChangeAssigneeUseCase,
        'description': 'Change the assignee of a Jira issue.',
        'dependencies': ['workflow_service']
    },
    
    'list_project_tickets': {
        'use_case_class': ListProjectTicketsUseCase,
        'description': 'List tickets (issues) in a Jira project with optional filtering.',
        'dependencies': ['search_service']
    },
    
    'get_custom_field_mappings': {
        'use_case_class': GetCustomFieldMappingsUseCase,
        'description': 'Get mappings between Jira custom field IDs and their names/descriptions.',
        'dependencies': ['field_service']
    },
    
    'generate_project_workflow_graph': {
        'use_case_class': GenerateWorkflowGraphUseCase,
        'description': 'Generate a visual workflow graph for a specific project and issue type.',
        'dependencies': ['workflow_service']
    },
    
    'list_jira_instances': {
        'use_case_class': ListInstancesUseCase,
        'description': 'List all configured Jira instances.',
        'dependencies': ['config_service']
    },
    
    'update_jira_issue': {
        'use_case_class': UpdateIssueUseCase,
        'description': 'Update an existing Jira issue with new field values.',
        'dependencies': ['issue_service']
    },
    
    'search_jira_issues': {
        'use_case_class': SearchIssuesUseCase,
        'description': 'Execute a JQL search query to find Jira issues.',
        'dependencies': ['search_service']
    },
    
    'validate_jql_query': {
        'use_case_class': ValidateJqlUseCase,
        'description': 'Validate JQL syntax without executing the query.',
        'dependencies': ['search_service']
    }
}


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
    
    required_keys = ['use_case_class', 'description', 'dependencies']
    
    for tool_name, config in JIRA_TOOLS.items():
        # Check required keys
        for key in required_keys:
            if key not in config:
                issues.append(f"Tool '{tool_name}' missing required key: {key}")
        
        # Check use_case_class is a class
        if 'use_case_class' in config:
            if not isinstance(config['use_case_class'], type):
                issues.append(f"Tool '{tool_name}' use_case_class must be a class")
        
        # Check description is non-empty string
        if 'description' in config:
            if not isinstance(config['description'], str) or not config['description'].strip():
                issues.append(f"Tool '{tool_name}' description must be non-empty string")
        
        # Check dependencies is list
        if 'dependencies' in config:
            if not isinstance(config['dependencies'], list):
                issues.append(f"Tool '{tool_name}' dependencies must be a list")
            elif not config['dependencies']:
                warnings.append(f"Tool '{tool_name}' has no dependencies")
    
    return {
        'valid': len(issues) == 0,
        'tool_count': len(JIRA_TOOLS),
        'issues': issues,
        'warnings': warnings
    }


def get_dependency_summary() -> Dict[str, list[str]]:
    """
    Get summary of which services are needed by which tools.
    
    Returns:
        Dictionary mapping service names to lists of tools that use them
    """
    dependency_map = {}
    
    for tool_name, config in JIRA_TOOLS.items():
        for dependency in config.get('dependencies', []):
            if dependency not in dependency_map:
                dependency_map[dependency] = []
            dependency_map[dependency].append(tool_name)
    
    return dependency_map


def get_config_stats() -> Dict[str, Any]:
    """
    Get statistics about the tool configuration.
    
    Returns:
        Configuration statistics
    """
    validation = validate_tool_config()
    dependencies = get_dependency_summary()
    
    return {
        'total_tools': len(JIRA_TOOLS),
        'unique_dependencies': len(dependencies),
        'validation': validation,
        'dependency_usage': {dep: len(tools) for dep, tools in dependencies.items()},
        'replaces_lines': 300,  # Lines eliminated from manual @mcp.tool() registrations
        'description': 'Metadata-driven tool configuration replacing manual registrations'
    }
