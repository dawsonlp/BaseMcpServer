#!/usr/bin/env python3
"""
Complete example showing the recommended pattern for MCP server development
with proper metadata handling, bulk registration, and transport selection.
"""

import sys
import asyncio
from typing import Optional, List, Dict, Any, Tuple, Callable
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool

# Mock context for demonstration
class MockJiraContext:
    def __init__(self):
        self.projects = ["PROJ", "TEST", "DEV"]
        self.issues = {}
        self.issue_counter = 0

# ============================================================================
# STEP 1: Pure Business Functions (No MCP Dependencies)
# ============================================================================

async def list_projects(context: MockJiraContext, instance_name: Optional[str] = None) -> Dict[str, Any]:
    """List all available Jira projects."""
    return {
        "success": True,
        "projects": context.projects,
        "instance": instance_name or "default"
    }

async def create_issue(
    context: MockJiraContext,
    project_key: str,
    summary: str,
    description: str = "",
    issue_type: str = "Story",
    priority: str = "Medium",
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new Jira issue with comprehensive details."""
    context.issue_counter += 1
    issue_key = f"{project_key}-{context.issue_counter}"
    
    issue = {
        "summary": summary,
        "description": description,
        "issue_type": issue_type,
        "priority": priority,
        "assignee": assignee,
        "labels": labels or [],
        "status": "Open"
    }
    
    context.issues[issue_key] = issue
    
    return {
        "success": True,
        "issue_key": issue_key,
        "summary": summary,
        "instance": instance_name or "default"
    }

async def get_issue_details(
    context: MockJiraContext, 
    issue_key: str, 
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Get comprehensive details about a specific Jira issue."""
    issue = context.issues.get(issue_key)
    if not issue:
        return {"success": False, "error": f"Issue {issue_key} not found"}
    
    return {
        "success": True,
        "issue_key": issue_key,
        "details": issue,
        "instance": instance_name or "default"
    }

async def search_issues(
    context: MockJiraContext,
    jql: str,
    max_results: int = 50,
    start_at: int = 0,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Execute JQL search to find matching issues."""
    # Mock JQL search - in reality this would parse JQL
    matching_issues = []
    for key, issue in context.issues.items():
        if jql.lower() in issue["summary"].lower() or jql.lower() in issue["description"].lower():
            matching_issues.append({"key": key, **issue})
    
    return {
        "success": True,
        "issues": matching_issues[start_at:start_at + max_results],
        "total": len(matching_issues),
        "jql": jql,
        "instance": instance_name or "default"
    }

# ============================================================================
# STEP 2: Tool Definitions with AI-Optimized Metadata
# ============================================================================

# Define tools with explicit descriptions optimized for AI tool selection
JIRA_TOOL_DEFINITIONS: List[Tuple[Callable, str, str]] = [
    (
        list_projects, 
        "list_jira_projects",
        "List all available Jira projects, optionally filtered by instance name"
    ),
    (
        create_issue,
        "create_jira_ticket", 
        "Create a new Jira issue with project key, summary, description, and optional priority/assignee/labels"
    ),
    (
        get_issue_details,
        "get_issue_details",
        "Get comprehensive details about a specific Jira issue by its key"
    ),
    (
        search_issues,
        "search_jira_issues",
        "Execute a JQL (Jira Query Language) search to find issues matching criteria with pagination"
    ),
]

# ============================================================================
# STEP 3: Smart Tool Registration
# ============================================================================

def create_tools_with_metadata(
    tool_definitions: List[Tuple[Callable, str, str]], 
    context_kwarg: str = "context"
) -> List[Tool]:
    """Create Tool objects with proper metadata for AI tool selection."""
    tools = []
    
    for func, name, description in tool_definitions:
        tool = Tool.from_function(
            func,
            name=name,
            description=description,  # Explicit description overrides docstring
            context_kwarg=context_kwarg
        )
        tools.append(tool)
    
    return tools

# ============================================================================
# STEP 4: Server Factory with Bulk Registration
# ============================================================================

def create_jira_mcp_server(context: MockJiraContext) -> FastMCP:
    """Create Jira MCP server with optimized tool metadata and bulk registration."""
    
    # Convert tool definitions to Tool objects with proper metadata
    tools = create_tools_with_metadata(JIRA_TOOL_DEFINITIONS)
    
    # Create server with all tools at once - no decorators needed!
    return FastMCP("Jira Helper", tools=tools)

# ============================================================================
# STEP 5: Universal Entry Point with Transport Selection
# ============================================================================

def main():
    """Universal entry point with runtime transport selection."""
    
    # Parse command line arguments
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    if transport not in ["stdio", "sse", "streamable-http"]:
        print(f"Error: Unknown transport '{transport}'")
        print("Usage: python test_complete_pattern.py [stdio|sse|streamable-http] [port]")
        sys.exit(1)
    
    # Run with context
    asyncio.run(run_with_context(transport, port))

async def run_with_context(transport: str, port: int):
    """Run server with proper context management."""
    
    # Create context (in real app, this would be dependency injection)
    context = MockJiraContext()
    
    # Create MCP server with all tools
    mcp = create_jira_mcp_server(context)
    
    # Configure transport-specific settings
    if transport in ["sse", "streamable-http"]:
        mcp.settings.port = port
    
    print(f"🚀 Starting Jira Helper MCP server with {transport} transport on port {port}")
    print(f"📋 Registered {len(JIRA_TOOL_DEFINITIONS)} tools:")
    for _, name, description in JIRA_TOOL_DEFINITIONS:
        print(f"   - {name}: {description}")
    
    # Run with selected transport
    mcp.run(transport=transport)

# ============================================================================
# STEP 6: Testing Function
# ============================================================================

async def test_complete_pattern():
    """Test the complete pattern without running the server."""
    print("🧪 Testing complete MCP pattern...\n")
    
    # Create context and server
    context = MockJiraContext()
    mcp = create_jira_mcp_server(context)
    
    # Test tool registration
    tool_manager = mcp._tool_manager
    tools = tool_manager.list_tools()
    
    print(f"✅ Registered {len(tools)} tools with optimized metadata:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description}")
    
    print(f"\n🔍 Parameter schemas generated from type hints:")
    for tool in tools:
        if tool.name == "create_jira_ticket":
            import json
            print(f"   {tool.name} parameters:")
            print(json.dumps(tool.parameters, indent=4))
            break
    
    # Test tool execution
    print(f"\n🧪 Testing tool execution:")
    
    # Test list projects
    result = await tool_manager.call_tool("list_jira_projects", {}, context=context)
    print(f"✅ list_jira_projects: {result}")
    
    # Test create issue
    result = await tool_manager.call_tool("create_jira_ticket", {
        "project_key": "TEST",
        "summary": "Test Issue",
        "description": "This is a test issue",
        "priority": "High",
        "labels": ["test", "demo"]
    }, context=context)
    print(f"✅ create_jira_ticket: {result}")
    
    # Test get issue details
    result = await tool_manager.call_tool("get_issue_details", {
        "issue_key": "TEST-1"
    }, context=context)
    print(f"✅ get_issue_details: {result}")
    
    # Test search
    result = await tool_manager.call_tool("search_jira_issues", {
        "jql": "test",
        "max_results": 10
    }, context=context)
    print(f"✅ search_jira_issues: {result}")
    
    print(f"\n🎉 Complete pattern test successful!")
    print(f"\n📖 Usage examples:")
    print(f"   python test_complete_pattern.py stdio")
    print(f"   python test_complete_pattern.py sse 8000")
    print(f"   python test_complete_pattern.py streamable-http 8000")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_complete_pattern())
    else:
        main()
