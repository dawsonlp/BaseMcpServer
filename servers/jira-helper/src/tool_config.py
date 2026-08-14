"""
Tool configuration for Jira Helper MCP Server.

Maps tool names to implementation functions for factory-based SDK registration.
"""

from mcp.types import ToolAnnotations
from mcp.server.mcpserver.resources import FileResource

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
    WORKFLOW_RESOURCE_PATHS,
    WORKFLOW_RESOURCE_URIS,
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


_READ_ONLY_TOOLS = {
    "list_jira_projects", "get_issue_details", "get_full_issue_details",
    "get_issue_transitions", "list_project_tickets", "get_custom_field_mappings",
    "list_jira_instances", "search_jira_issues",
    "validate_jql_query", "get_issue_links", "get_work_logs",
    "get_time_tracking_info", "list_issue_attachments", "list_confluence_spaces",
    "list_confluence_pages", "get_confluence_page", "search_confluence_pages",
}
_DESTRUCTIVE_TOOLS = {
    "transition_jira_issue", "change_issue_assignee", "update_jira_issue",
    "update_time_estimates", "delete_issue_attachment", "update_confluence_page",
}

for _name, _spec in JIRA_TOOLS.items():
    _read_only = _name in _READ_ONLY_TOOLS
    _spec["title"] = _name.replace("_", " ").title()
    _spec["annotations"] = ToolAnnotations(
        readOnlyHint=_read_only,
        destructiveHint=_name in _DESTRUCTIVE_TOOLS,
        idempotentHint=_read_only or _name == "generate_project_workflow_graph",
        openWorldHint=_name not in {"list_jira_instances", "validate_jql_query"},
    )


def get_tools_config() -> dict:
    """Get the tools configuration consumed by ``create_server()``."""
    return JIRA_TOOLS


def get_resources() -> tuple[FileResource, ...]:
    """Return the fixed workflow artifacts exposed through MCP resources."""
    return tuple(
        FileResource(
            uri=WORKFLOW_RESOURCE_URIS[fmt],
            path=WORKFLOW_RESOURCE_PATHS[fmt],
            name=f"latest-jira-workflow-{fmt}",
            title=f"Latest Jira Workflow ({fmt.upper()})",
            description=f"Most recently generated Jira workflow graph in {fmt.upper()} format.",
            mime_type="image/png" if fmt == "png" else "image/svg+xml",
        )
        for fmt in ("png", "svg")
    )
