"""
MCP Bulk Registration System

This module provides bulk registration of MCP tools from metadata configuration.
Replaces 300+ lines of manual @mcp.tool() decorations with automated registration.
"""

import logging
from typing import Dict, Any, List, Tuple, Callable

from adapters.mcp_result_adapter import create_mcp_adapter
from adapters.mcp_tool_config import JIRA_TOOLS, validate_tool_config, get_config_stats

logger = logging.getLogger(__name__)


class BulkRegistrationError(Exception):
    """Exception raised during bulk tool registration."""
    pass


def bulk_register_jira_tools(context) -> List[Tuple[Callable, str, str]]:
    """
    Bulk register all Jira tools from metadata configuration.
    
    This function replaces all manual @mcp.tool() decorations by automatically
    creating MCP tools from use case classes and their dependencies.
    
    Args:
        context: JiraHelperContext containing all initialized services
        
    Returns:
        List of tuples (function, name, description) for FastMCP registration
        
    Raises:
        BulkRegistrationError: If registration fails for any tool
    """
    logger.info("Starting bulk registration of Jira MCP tools...")
    
    # Validate configuration first
    validation = validate_tool_config()
    if not validation['valid']:
        error_msg = f"Tool configuration validation failed: {validation['issues']}"
        logger.error(error_msg)
        raise BulkRegistrationError(error_msg)
    
    logger.info(f"Registering {validation['tool_count']} tools from configuration...")
    
    tools = []
    registration_errors = []
    
    for tool_name, config in JIRA_TOOLS.items():
        try:
            tool = _register_single_tool(tool_name, config, context)
            tools.append(tool)
            logger.debug(f"Successfully registered tool: {tool_name}")
            
        except Exception as e:
            error_msg = f"Failed to register tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            registration_errors.append(error_msg)
    
    # Report results
    if registration_errors:
        error_summary = f"Registration failed for {len(registration_errors)} tools: {registration_errors}"
        logger.error(error_summary)
        raise BulkRegistrationError(error_summary)
    
    logger.info(f"Successfully registered {len(tools)} MCP tools")
    return tools


def _register_single_tool(tool_name: str, config: Dict[str, Any], context) -> Tuple[Callable, str, str]:
    """
    Register a single MCP tool from configuration.
    
    Args:
        tool_name: Name of the tool
        config: Tool configuration dictionary
        context: JiraHelperContext containing services
        
    Returns:
        Tuple of (function, name, description) for FastMCP registration
        
    Raises:
        BulkRegistrationError: If registration fails
    """
    try:
        # Get use case class and dependencies
        use_case_class = config['use_case_class']
        dependencies = config['dependencies']
        description = config['description']
        
        # Resolve dependencies from context
        resolved_deps = {}
        for dep_name in dependencies:
            if not hasattr(context, dep_name):
                raise BulkRegistrationError(f"Missing dependency '{dep_name}' in context for tool '{tool_name}'")
            resolved_deps[dep_name] = getattr(context, dep_name)
        
        # Create use case instance with dependencies
        use_case = use_case_class(**resolved_deps)
        
        # Create MCP-adapted method
        adapted_method = create_mcp_adapter(use_case.execute)
        
        # Return function, name, description tuple for FastMCP registration
        return (adapted_method, tool_name, description)
        
    except Exception as e:
        raise BulkRegistrationError(f"Error registering tool '{tool_name}': {str(e)}") from e


def validate_context_dependencies(context) -> Dict[str, Any]:
    """
    Validate that the context has all required dependencies for tool registration.
    
    Args:
        context: JiraHelperContext to validate
        
    Returns:
        Validation results with missing dependencies
    """
    missing_deps = []
    available_deps = []
    
    # Get all unique dependencies from tool configuration
    all_dependencies = set()
    for config in JIRA_TOOLS.values():
        all_dependencies.update(config.get('dependencies', []))
    
    # Check each dependency
    for dep_name in all_dependencies:
        if hasattr(context, dep_name):
            available_deps.append(dep_name)
        else:
            missing_deps.append(dep_name)
    
    return {
        'valid': len(missing_deps) == 0,
        'total_dependencies': len(all_dependencies),
        'available_dependencies': available_deps,
        'missing_dependencies': missing_deps
    }


def get_registration_stats() -> Dict[str, Any]:
    """
    Get statistics about the bulk registration system.
    
    Returns:
        Registration system statistics
    """
    config_stats = get_config_stats()
    
    return {
        'system_version': '1.0.0',
        'tools_supported': config_stats['total_tools'],
        'dependencies_required': config_stats['unique_dependencies'],
        'replaces_manual_registrations': True,
        'lines_eliminated': 300,  # Manual @mcp.tool() decorations eliminated
        'description': 'Automated bulk registration replacing manual tool decorations'
    }


def create_registration_report(tool_tuples: List[Tuple[Callable, str, str]], context) -> Dict[str, Any]:
    """
    Create a detailed report of the registration process.
    
    Args:
        tool_tuples: List of successfully registered tool tuples (function, name, description)
        context: JiraHelperContext used for registration
        
    Returns:
        Detailed registration report
    """
    dependency_validation = validate_context_dependencies(context)
    config_validation = validate_tool_config()
    
    # Group tools by dependency
    tools_by_dependency = {}
    for tool_name, config in JIRA_TOOLS.items():
        for dep in config.get('dependencies', []):
            if dep not in tools_by_dependency:
                tools_by_dependency[dep] = []
            tools_by_dependency[dep].append(tool_name)
    
    return {
        'registration_timestamp': None,  # Would be set by caller
        'total_tools_registered': len(tool_tuples),
        'total_tools_configured': len(JIRA_TOOLS),
        'success_rate': len(tool_tuples) / len(JIRA_TOOLS) if JIRA_TOOLS else 0,
        'configuration_validation': config_validation,
        'dependency_validation': dependency_validation,
        'tools_by_dependency': tools_by_dependency,
        'registered_tool_names': [name for _, name, _ in tool_tuples],
        'system_stats': get_registration_stats()
    }


def log_registration_summary(tool_tuples: List[Tuple[Callable, str, str]], context):
    """
    Log a summary of the registration process.
    
    Args:
        tool_tuples: List of successfully registered tool tuples (function, name, description)
        context: JiraHelperContext used for registration
    """
    report = create_registration_report(tool_tuples, context)
    
    logger.info("=== MCP Tool Registration Summary ===")
    logger.info(f"Tools registered: {report['total_tools_registered']}/{report['total_tools_configured']}")
    logger.info(f"Success rate: {report['success_rate']:.1%}")
    logger.info(f"Dependencies resolved: {len(report['dependency_validation']['available_dependencies'])}")
    
    if report['dependency_validation']['missing_dependencies']:
        logger.warning(f"Missing dependencies: {report['dependency_validation']['missing_dependencies']}")
    
    logger.info("Registered tools:")
    for tool_name in sorted(report['registered_tool_names']):
        logger.info(f"  ✓ {tool_name}")
    
    logger.info(f"Lines of boilerplate eliminated: {report['system_stats']['lines_eliminated']}")
    logger.info("=== Registration Complete ===")
