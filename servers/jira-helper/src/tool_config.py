"""
Tool configuration for Jira Helper MCP Server.

Maps tool names to their implementation functions using mcp-commons pattern.
"""

from tools.issues import (
    list_jira_projects,
    get_issue_details,
    get_full_issue_details,
    create_jira_ticket,
    update_jira_issue,
    transition_jira_issue,
    change_issue_assignee,
    list_jira_instances,
    get_custom_field_mappings,
)
from tools.search import (
    search_jira_issues,
    list_project_tickets,
    validate_jql_query,
)
from tools.comments import (
    add_comment_to_jira_ticket,
    get_issue_transitions,
)
from tools.links import (
    create_issue_link,
    create_epic_story_link,
    get_issue_links,
    create_issue_with_links,
)
from tools.time_tracking import (
    log_work,
    get_work_logs,
    get_time_tracking_info,
    update_time_estimates,
)
from tools.workflow import (
    generate_project_workflow_graph,
)
from tools.confluence import (
    list_confluence_spaces,
    list_confluence_pages,
    get_confluence_page,
    search_confluence_pages,
    create_confluence_page,
    update_confluence_page,
)
from tools.files import (
    upload_file_to_jira,
    list_issue_attachments,
    delete_issue_attachment,
)


JIRA_TOOLS = {
    # Core Jira operations (13 tools)
    "list_jira_projects": {
        "function": list_jira_projects,
        "description": "List all projects available in the Jira instance.",
    },
    "get_issue_details": {
        "function": get_issue_details,
        "description": "Get detailed information about a specific Jira issue.",
    },
    "get_full_issue_details": {
        "function": get_full_issue_details,
        "description": "Get comprehensive information about a specific Jira issue with formatting options.",
    },
    "create_jira_ticket": {
        "function": create_jira_ticket,
        "description": "Create a new Jira ticket (issue).",
    },
    "add_comment_to_jira_ticket": {
        "function": add_comment_to_jira_ticket,
        "description": "Add a comment to an existing Jira ticket.",
    },
    "transition_jira_issue": {
        "function": transition_jira_issue,
        "description": "Transition a Jira issue through its workflow.",
    },
    "get_issue_transitions": {
        "function": get_issue_transitions,
        "description": "Get available workflow transitions for a Jira issue.",
    },
    "change_issue_assignee": {
        "function": change_issue_assignee,
        "description": "Change the assignee of a Jira issue.",
    },
    "list_project_tickets": {
        "function": list_project_tickets,
        "description": "List tickets (issues) in a Jira project with optional filtering.",
    },
    "get_custom_field_mappings": {
        "function": get_custom_field_mappings,
        "description": "Get mappings between Jira custom field IDs and their names/descriptions.",
    },
    "generate_project_workflow_graph": {
        "function": generate_project_workflow_graph,
        "description": "Generate a visual workflow graph for a specific project and issue type.",
    },
    "list_jira_instances": {
        "function": list_jira_instances,
        "description": "List all configured Jira instances.",
    },
    "update_jira_issue": {
        "function": update_jira_issue,
        "description": "Update an existing Jira issue with new field values.",
    },
    # Search & advanced operations (6 tools)
    "search_jira_issues": {
        "function": search_jira_issues,
        "description": "Execute a JQL search query to find Jira issues.",
    },
    "validate_jql_query": {
        "function": validate_jql_query,
        "description": "Validate JQL syntax without executing the query.",
    },
    "create_issue_link": {
        "function": create_issue_link,
        "description": "Create a link between two Jira issues.",
    },
    "create_epic_story_link": {
        "function": create_epic_story_link,
        "description": "Create an Epic-Story link between issues.",
    },
    "get_issue_links": {
        "function": get_issue_links,
        "description": "Get all links for a specific Jira issue.",
    },
    "create_issue_with_links": {
        "function": create_issue_with_links,
        "description": "Create a new Jira issue with links to other issues.",
    },
    # Time tracking operations (4 tools)
    "log_work": {
        "function": log_work,
        "description": "Log work time on a Jira issue.",
    },
    "get_work_logs": {
        "function": get_work_logs,
        "description": "Get work log entries for a Jira issue.",
    },
    "get_time_tracking_info": {
        "function": get_time_tracking_info,
        "description": "Get time tracking information for a Jira issue.",
    },
    "update_time_estimates": {
        "function": update_time_estimates,
        "description": "Update time estimates for a Jira issue.",
    },
    # File operations (3 tools)
    "upload_file_to_jira": {
        "function": upload_file_to_jira,
        "description": "Upload a file to a Jira issue as an attachment.",
    },
    "list_issue_attachments": {
        "function": list_issue_attachments,
        "description": "List all attachments for a Jira issue.",
    },
    "delete_issue_attachment": {
        "function": delete_issue_attachment,
        "description": "Delete an attachment from a Jira issue.",
    },
    # Confluence operations (6 tools)
    "list_confluence_spaces": {
        "function": list_confluence_spaces,
        "description": "List all Confluence spaces available in the instance.",
    },
    "list_confluence_pages": {
        "function": list_confluence_pages,
        "description": "List pages in a specific Confluence space.",
    },
    "get_confluence_page": {
        "function": get_confluence_page,
        "description": "Get detailed information about a specific Confluence page.",
    },
    "search_confluence_pages": {
        "function": search_confluence_pages,
        "description": "Search for Confluence pages using text query.",
    },
    "create_confluence_page": {
        "function": create_confluence_page,
        "description": "Create a new Confluence page.",
    },
    "update_confluence_page": {
        "function": update_confluence_page,
        "description": "Update an existing Confluence page.",
    },
}


def get_tools_config() -> dict:
    """Get the tools configuration for mcp-commons registration."""
    return JIRA_TOOLS