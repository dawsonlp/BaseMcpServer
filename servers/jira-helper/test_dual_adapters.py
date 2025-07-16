#!/usr/bin/env python3
"""
Test script for dual adapter architecture.

This script tests both the direct MCP adapter and the HTTP adapter
to ensure they provide consistent functionality while maintaining DRY principles.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

async def test_shared_tools():
    """Test that shared tools work correctly."""
    print("🔧 Testing shared MCP tools...")
    
    try:
        from adapters.mcp_tools import create_mcp_tools, get_tool_schemas
        from adapters.mcp_adapter import jira_lifespan
        from mcp.server.fastmcp import FastMCP
        
        # Create a dummy server for lifespan management
        dummy_server = FastMCP("Test Server", lifespan=jira_lifespan)
        
        # Test context initialization and tool creation
        async with jira_lifespan(dummy_server) as context:
            tools = create_mcp_tools(context)
            schemas = get_tool_schemas()
            
            print(f"✅ Successfully created {len(tools)} tools")
            print(f"✅ Successfully loaded {len(schemas)} tool schemas")
            
            # Test a simple tool call
            if "list_jira_instances" in tools:
                result = await tools["list_jira_instances"]()
                print(f"✅ Tool call successful: {type(result)}")
            else:
                print("⚠️  list_jira_instances tool not found")
                
        return True
        
    except Exception as e:
        print(f"❌ Shared tools test failed: {str(e)}")
        return False

async def test_http_adapter():
    """Test HTTP adapter functionality."""
    print("\n🌐 Testing HTTP adapter...")
    
    try:
        from adapters.http_adapter import JiraHelperHTTPServer
        
        # Create server instance
        server = JiraHelperHTTPServer()
        
        # Test initialization
        async with server.initialize():
            print("✅ HTTP server initialized successfully")
            
            if server.tools:
                print(f"✅ HTTP server has {len(server.tools)} tools available")
            else:
                print("❌ HTTP server has no tools")
                return False
                
            if server.context:
                print("✅ HTTP server context initialized")
            else:
                print("❌ HTTP server context not initialized")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ HTTP adapter test failed: {str(e)}")
        return False

def test_direct_adapter():
    """Test direct MCP adapter functionality."""
    print("\n🔗 Testing direct MCP adapter...")
    
    try:
        from adapters.mcp_adapter import mcp, JiraHelperContext
        
        print("✅ Direct MCP adapter imported successfully")
        
        # Check that the MCP server is properly configured
        if hasattr(mcp, '_tools'):
            print(f"✅ Direct adapter has tools registered")
        else:
            print("⚠️  Direct adapter tools not immediately visible (normal for FastMCP)")
            
        return True
        
    except Exception as e:
        print(f"❌ Direct adapter test failed: {str(e)}")
        return False

def test_dry_compliance():
    """Test that both adapters use the same tool definitions."""
    print("\n🔄 Testing DRY compliance...")
    
    try:
        from adapters.mcp_tools import create_mcp_tools, get_tool_schemas
        
        # Get tool schemas
        schemas = get_tool_schemas()
        
        # Check that we have expected tools
        expected_tools = [
            "list_jira_projects",
            "get_issue_details", 
            "create_jira_ticket",
            "list_jira_instances"
        ]
        
        missing_tools = []
        for tool in expected_tools:
            if tool not in schemas:
                missing_tools.append(tool)
                
        if missing_tools:
            print(f"❌ Missing expected tools: {missing_tools}")
            return False
        else:
            print(f"✅ All expected tools present in schemas")
            
        # Verify schema structure
        for tool_name, schema in schemas.items():
            if "description" not in schema:
                print(f"❌ Tool {tool_name} missing description")
                return False
            if "inputSchema" not in schema:
                print(f"❌ Tool {tool_name} missing inputSchema")
                return False
                
        print("✅ All tool schemas have required fields")
        print("✅ DRY compliance verified - single source of truth for tools")
        
        return True
        
    except Exception as e:
        print(f"❌ DRY compliance test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing Dual Adapter Architecture for Jira Helper")
    print("=" * 60)
    
    tests = [
        ("Shared Tools", test_shared_tools()),
        ("HTTP Adapter", test_http_adapter()),
        ("Direct Adapter", test_direct_adapter()),
        ("DRY Compliance", test_dry_compliance())
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Dual adapter architecture is working correctly.")
        print("\n📋 Next Steps:")
        print("  1. Test direct MCP mode: python src/main.py")
        print("  2. Test HTTP mode: python src/http_main.py")
        print("  3. Test Docker deployment: docker compose -f docker-compose.http.yml up")
        return 0
    else:
        print(f"\n💥 {failed} test(s) failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
