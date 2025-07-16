#!/usr/bin/env python3
"""
Test script to understand how MCP SDK handles metadata and descriptions.
"""

import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool

# Test functions with different metadata scenarios
async def function_with_good_docstring(context, project_key: str, summary: str):
    """
    Create a new Jira issue with the specified details.
    
    This tool creates a new issue in the specified Jira project with the given
    summary and description. It returns the created issue key and details.
    
    Args:
        project_key: The key of the Jira project (e.g., 'PROJ', 'TEST')
        summary: Brief summary of the issue
    
    Returns:
        Dict containing success status, issue key, and issue details
    """
    return {"success": True, "issue_key": f"{project_key}-123", "summary": summary}

async def function_with_minimal_docstring(context, issue_key: str):
    """Get issue details"""
    return {"issue_key": issue_key, "status": "Open"}

async def function_with_no_docstring(context, instance_name: str = None):
    return {"projects": ["PROJ1", "PROJ2"], "instance": instance_name}

async def function_with_empty_docstring(context, query: str):
    """"""
    return {"results": [], "query": query}

def test_metadata_scenarios():
    """Test different metadata handling approaches"""
    
    print("🧪 Testing MCP SDK metadata handling...\n")
    
    # Scenario 1: Using function docstrings (current approach)
    print("1️⃣ Using function docstrings:")
    tools_with_docstrings = [
        Tool.from_function(function_with_good_docstring, name="create_issue", context_kwarg="context"),
        Tool.from_function(function_with_minimal_docstring, name="get_issue", context_kwarg="context"),
        Tool.from_function(function_with_no_docstring, name="list_projects", context_kwarg="context"),
        Tool.from_function(function_with_empty_docstring, name="search_issues", context_kwarg="context"),
    ]
    
    for tool in tools_with_docstrings:
        print(f"   {tool.name}: '{tool.description}'")
    
    # Scenario 2: Explicit descriptions override docstrings
    print("\n2️⃣ Using explicit descriptions:")
    tools_with_explicit_descriptions = [
        Tool.from_function(
            function_with_good_docstring, 
            name="create_issue",
            description="Create a new Jira ticket with project key and summary",
            context_kwarg="context"
        ),
        Tool.from_function(
            function_with_no_docstring,
            name="list_projects", 
            description="List all available Jira projects in the specified instance",
            context_kwarg="context"
        ),
        Tool.from_function(
            function_with_empty_docstring,
            name="search_issues",
            description="Search for Jira issues using JQL query syntax",
            context_kwarg="context"
        ),
    ]
    
    for tool in tools_with_explicit_descriptions:
        print(f"   {tool.name}: '{tool.description}'")
    
    # Scenario 3: Mixed approach - some with docstrings, some with explicit
    print("\n3️⃣ Mixed approach (recommended):")
    mixed_tools = [
        # Good docstring - use it
        Tool.from_function(function_with_good_docstring, name="create_issue", context_kwarg="context"),
        
        # No/bad docstring - provide explicit description
        Tool.from_function(
            function_with_no_docstring,
            name="list_projects",
            description="List all available Jira projects, optionally filtered by instance",
            context_kwarg="context"
        ),
        Tool.from_function(
            function_with_empty_docstring, 
            name="search_issues",
            description="Execute JQL search query to find matching Jira issues",
            context_kwarg="context"
        ),
    ]
    
    for tool in mixed_tools:
        print(f"   {tool.name}: '{tool.description}'")

def test_parameter_schemas():
    """Test how parameter schemas are generated"""
    
    print("\n🔍 Testing parameter schema generation...\n")
    
    # Function with type hints
    async def well_typed_function(
        context,
        project_key: str,
        summary: str,
        description: str = "",
        priority: str = "Medium",
        assignee: str = None
    ):
        """Create a Jira issue with full type information"""
        pass
    
    tool = Tool.from_function(well_typed_function, name="create_issue", context_kwarg="context")
    
    print("Parameter schema for well-typed function:")
    import json
    print(json.dumps(tool.parameters, indent=2))

if __name__ == "__main__":
    test_metadata_scenarios()
    test_parameter_schemas()
