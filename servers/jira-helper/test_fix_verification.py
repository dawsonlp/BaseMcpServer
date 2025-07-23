#!/usr/bin/env python3
"""
Simple test to verify the time validation fix is working.
"""

import sys
import os
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_time_validation_fix():
    """Test that time validation is working correctly."""
    print("🧪 Testing time validation fix...")
    
    try:
        # Import the actual MCP tool function directly
        from adapters.mcp_bulk_registration import bulk_register_jira_tools
        from adapters.mcp_adapter import jira_lifespan
        from mcp.server.fastmcp import FastMCP
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        env_path = os.path.expanduser("~/.env")
        load_dotenv(env_path)
        
        # Create a FastMCP server and initialize the context
        server = FastMCP("Test Jira Helper")
        
        print("🔍 Initializing Jira services...")
        async with jira_lifespan(server) as context:
            print("✅ Jira services initialized successfully")
            
            # Get tool functions
            tool_functions = bulk_register_jira_tools(context)
            tools = {}
            
            for func, name, description in tool_functions:
                tools[name] = func
            
            # Get the log_work function
            if "log_work" not in tools:
                print("❌ FAILED: log_work tool function not found")
                return False
            
            log_work_func = tools["log_work"]
            
            print("\n🧪 TEST 1: Testing with VALID time format (should work)...")
            
            try:
                result = await log_work_func(
                    issue_key="ATP-1",
                    time_spent="2h",  # Valid time format
                    comment="Test with valid time format",
                    started=None,
                    adjust_estimate="auto",
                    new_estimate=None,
                    reduce_by=None,
                    instance_name="personal"
                )
                
                print(f"✅ Valid time test result: {result}")
                
                if result.get("success", False):
                    print("🎉 SUCCESS: Valid time format worked!")
                else:
                    print(f"❌ FAILED: Valid time format failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Exception during valid time test: {str(e)}")
            
            print("\n🧪 TEST 2: Testing with INVALID time format (should fail gracefully)...")
            
            try:
                result = await log_work_func(
                    issue_key="ATP-1",
                    time_spent="30m",  # This should be invalid according to our validator
                    comment="Test with invalid time format",
                    started=None,
                    adjust_estimate="auto",
                    new_estimate=None,
                    reduce_by=None,
                    instance_name="personal"
                )
                
                print(f"✅ Invalid time test result: {result}")
                
                if not result.get("success", False):
                    error_msg = result.get("error", "")
                    if "Expected format: True" in error_msg:
                        print("❌ STILL BROKEN: Still showing 'Expected format: True'")
                        return False
                    else:
                        print("🎉 SUCCESS: Invalid time format failed gracefully with proper error message!")
                        print(f"   Error: {error_msg}")
                        return True
                else:
                    print("❌ UNEXPECTED: Invalid time format was accepted!")
                    return False
                
            except Exception as e:
                print(f"❌ Exception during invalid time test: {str(e)}")
                return False
            
            return True
                    
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return False


async def main():
    """Main function to run the test."""
    print("🚀 Starting time validation fix verification...\n")
    
    success = await test_time_validation_fix()
    
    if success:
        print("\n🎉 Time validation fix verification PASSED!")
    else:
        print("\n❌ Time validation fix verification FAILED")
        
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
