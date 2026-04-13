"""Tests for tool configuration."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_tool_config_has_all_tools():
    """Verify all 32 tools are registered."""
    from tool_config import get_tools_config
    config = get_tools_config()
    assert len(config) == 32, f"Expected 32 tools, got {len(config)}"


def test_all_tools_have_function_and_description():
    """Every tool must have a callable function and non-empty description."""
    from tool_config import get_tools_config
    config = get_tools_config()
    for name, tool in config.items():
        assert "function" in tool, f"Tool '{name}' missing 'function'"
        assert callable(tool["function"]), f"Tool '{name}' function is not callable"
        assert "description" in tool, f"Tool '{name}' missing 'description'"
        assert isinstance(tool["description"], str) and tool["description"].strip(), (
            f"Tool '{name}' description is empty"
        )


def test_tool_names_match_expected():
    """Verify the exact set of tool names matches what was in v1.2.0."""
    from tool_config import get_tools_config
    config = get_tools_config()
    expected = {
        "list_jira_projects", "get_issue_details", "get_full_issue_details",
        "create_jira_ticket", "add_comment_to_jira_ticket", "transition_jira_issue",
        "get_issue_transitions", "change_issue_assignee", "list_project_tickets",
        "get_custom_field_mappings", "generate_project_workflow_graph",
        "list_jira_instances", "update_jira_issue", "search_jira_issues",
        "validate_jql_query", "create_issue_link", "create_epic_story_link",
        "get_issue_links", "create_issue_with_links", "log_work", "get_work_logs",
        "get_time_tracking_info", "update_time_estimates", "upload_file_to_jira",
        "list_issue_attachments", "delete_issue_attachment", "list_confluence_spaces",
        "list_confluence_pages", "get_confluence_page", "search_confluence_pages",
        "create_confluence_page", "update_confluence_page",
    }
    assert set(config.keys()) == expected