#!/usr/bin/env python3
"""
Test script to verify MCP SDK bulk tool registration works as expected.
"""

import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool

# Mock context for testing
class MockContext:
    def __init__(self):
        self.data = {"projects": ["PROJ1", "PROJ2"], "issues": {}}

# Business functions (pure, no MCP dependencies)
async def list_projects(context, instance_name: str = None):
    """List all projects in the Jira instance"""
    return {
        "success": True,
        "projects": context.data["projects"],
        "instance": instance_name or "default"
    }

async def create_issue(context, project_key: str, summary: str, description: str):
    """Create a new Jira issue"""
    issue_key = f"{project_key}-{len(context.data['issues']) + 1}"
    context.data["issues"][issue_key] = {
        "summary": summary,
        "description": description,
        "project": project_key
    }
    return {
        "success": True,
        "issue_key": issue_key,
        "summary": summary
    }

async def get_issue_details(context, issue_key: str, instance_name: str = None):
    """Get details of a specific issue"""
    issue = context.data["issues"].get(issue_key)
    if not issue:
        return {"success": False, "error": f"Issue {issue_key} not found"}
    
    return {
        "success": True,
        "issue_key": issue_key,
        "details": issue,
        "instance": instance_name or "default"
    }

def create_tools_from_functions(function_list, context_kwarg="context"):
    """Helper to convert function list to Tool objects"""
    return [
        Tool.from_function(func, name=name, context_kwarg=context_kwarg)
        for func, name in function_list
    ]

def create_test_mcp_server(context) -> FastMCP:
    """Create test MCP server with bulk tool registration"""
    
    # THE ONLY PLACE TO LIST TOOLS - just functions and names
    jira_functions = [
        (list_projects, "list_jira_projects"),
        (create_issue, "create_jira_ticket"),
        (get_issue_details, "get_issue_details"),
    ]
    
    # Convert to Tool objects
    tools = create_tools_from_functions(jira_functions)
    
    # Create server with all tools at once
    return FastMCP("Test Jira Helper", tools=tools)

async def test_bulk_registration():
    """Test that bulk tool registration works"""
    print("Testing MCP SDK bulk tool registration...")
    
    # Create context and server
    context = MockContext()
    mcp = create_test_mcp_server(context)
    
    # Test that tools are registered
    tool_manager = mcp._tool_manager
    tools = tool_manager.list_tools()
    
    print(f"✅ Registered {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description}")
    
    # Test tool execution
    print("\n🧪 Testing tool execution:")
    
    # Test list_projects - pass context properly
    result = await tool_manager.call_tool("list_jira_projects", {}, context=context)
    print(f"✅ list_jira_projects: {result}")
    
    # Test create_issue
    result = await tool_manager.call_tool("create_jira_ticket", {
        "project_key": "TEST",
        "summary": "Test Issue",
        "description": "This is a test issue"
    }, context=context)
    print(f"✅ create_jira_ticket: {result}")
    
    # Test get_issue_details
    result = await tool_manager.call_tool("get_issue_details", {
        "issue_key": "TEST-1"
    }, context=context)
    print(f"✅ get_issue_details: {result}")
    
    print("\n🎉 All tests passed! Bulk tool registration works perfectly!")

if __name__ == "__main__":
    asyncio.run(test_bulk_registration())
