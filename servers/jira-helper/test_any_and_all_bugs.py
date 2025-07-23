#!/usr/bin/env python3
"""
Real test for work logging that actually tries to authenticate and make API calls.
This test will fail properly if authentication doesn't work.
"""

import sys
import os
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def debug_with_auth_check():
    """Debug with authentication check first, then time validation."""
    print("🧪 Starting debug with authentication verification...")
    
    try:
        # Import the actual MCP tool function directly
        from adapters.mcp_bulk_registration import bulk_register_jira_tools
        from adapters.mcp_adapter import jira_lifespan
        from mcp.server.fastmcp import FastMCP
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        env_path = os.path.expanduser("~/.env")
        if not os.path.exists(env_path):
            print("❌ FAILED: ~/.env file not found")
            return False
            
        load_dotenv(env_path)
        
        # Check that we have the required environment variables
        jira_url = os.getenv('JIRA_URL')
        jira_user = os.getenv('JIRA_USER') 
        jira_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_user, jira_token]):
            print("❌ FAILED: Missing required environment variables")
            return False
            
        print("✅ Environment variables loaded")
        print(f"   URL: {jira_url}")
        print(f"   User: {jira_user}")
        print(f"   Token: {'*' * 20}...")
        
        # Create a FastMCP server and initialize the context
        server = FastMCP("Debug Jira Helper")
        
        print("\n🔍 Initializing Jira services...")
        async with jira_lifespan(server) as context:
            print("✅ Jira services initialized successfully")
            
            # Get tool functions
            tool_functions = bulk_register_jira_tools(context)
            tools = {}
            
            for func, name, description in tool_functions:
                tools[name] = func
                
            print(f"✅ Found {len(tools)} tools")
            
            # STEP 1: Test authentication with simple operations
            print("\n🔐 STEP 1: Testing authentication...")
            
            # Test 1: List projects
            if "list_jira_projects" in tools:
                try:
                    result = await tools["list_jira_projects"](instance_name="personal")
                    if result.get("projects"):
                        print(f"   ✅ Auth works - found {len(result['projects'])} projects")
                        # Look for ATP project
                        atp_found = any(p.get("key") == "ATP" for p in result["projects"])
                        if atp_found:
                            print("   ✅ ATP project found!")
                        else:
                            print("   ⚠️  ATP project not found in project list")
                    else:
                        print("   ❌ Auth failed - no projects returned")
                        return False
                except Exception as e:
                    print(f"   ❌ Auth failed - list projects error: {str(e)}")
                    return False
            
            # Test 2: Get ATP-1 issue details
            if "get_issue_details" in tools:
                try:
                    result = await tools["get_issue_details"](
                        issue_key="ATP-1",
                        instance_name="personal"
                    )
                    if result.get("issue"):
                        print("   ✅ Auth works - can access ATP-1 issue")
                        print(f"   Issue: {result['issue'].get('summary', 'No summary')}")
                    else:
                        print("   ❌ Auth failed - cannot access ATP-1")
                        return False
                except Exception as e:
                    print(f"   ❌ Auth failed - get issue error: {str(e)}")
                    return False
            
            print("\n🎉 Authentication verified! Proceeding to time validation debug...")
            
            # STEP 2: Now test time validation
            print("\n🕐 STEP 2: Testing time validation...")
            
            if "log_work" not in tools:
                print("❌ FAILED: log_work tool function not found")
                return False
            
            log_work_func = tools["log_work"]
            
            test_cases = [
                ("ATP-1", "30m", "Testing 30 minutes format"),
                ("ATP-1", "invalid", "Testing invalid format - should fail"),
            ]
            
            for issue_key, time_spent, description in test_cases:
                print(f"\n🧪 Testing: {description}")
                print(f"   Issue: {issue_key}, Time: {time_spent}")
                
                try:
                    result = await log_work_func(
                        issue_key=issue_key,
                        time_spent=time_spent,
                        comment=f"Debug test: {description}",
                        started=None,
                        adjust_estimate="auto",
                        new_estimate=None,
                        reduce_by=None,
                        instance_name="personal"
                    )
                    
                    print(f"   ✅ Result: {result}")
                    
                    # Check for the specific error we're debugging
                    if not result.get("success", False):
                        error_msg = result.get("error", "")
                        if "Expected format: True" in error_msg:
                            print(f"   🎯 FOUND THE TIME VALIDATION BUG!")
                            print(f"   Error: {error_msg}")
                        elif "can only join an iterable" in error_msg:
                            print(f"   🎯 FOUND THE JOIN BUG!")
                            print(f"   Error: {error_msg}")
                        else:
                            print(f"   ❌ Different error: {error_msg}")
                    
                except Exception as e:
                    print(f"   ❌ Exception: {str(e)}")
                    if "Expected format: True" in str(e):
                        print(f"   🎯 FOUND THE TIME VALIDATION BUG IN EXCEPTION!")
                    elif "can only join an iterable" in str(e):
                        print(f"   🎯 FOUND THE JOIN BUG IN EXCEPTION!")
                        import traceback
                        traceback.print_exc()
            
            return True
                    
    except Exception as e:
        print(f"❌ Test setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def debug_time_tracking_service_validation():
    """Debug the TimeTrackingService validation chain to find where True comes from."""
    print("\n🔍 STEP 3: Debugging TimeTrackingService validation chain...")
    
    try:
        # Import the service and dependencies
        from domain.services import TimeTrackingService
        from infrastructure.atlassian_time_adapter import AtlassianTimeFormatValidator, AtlassianTimeTrackingAdapter
        from infrastructure.config_adapter import ConfigurationAdapter
        from infrastructure.atlassian_api_adapter import AtlassianApiJiraClientFactory
        from infrastructure.atlassian_repository import AtlassianApiRepository
        import logging
        
        # Create a minimal logger
        class MockLogger:
            def debug(self, msg): print(f"DEBUG: {msg}")
            def info(self, msg): print(f"INFO: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
        
        # Create service dependencies
        config = ConfigurationAdapter()
        client_factory = AtlassianApiJiraClientFactory(config)
        repository = AtlassianApiRepository(client_factory, config)
        time_validator = AtlassianTimeFormatValidator()
        time_adapter = AtlassianTimeTrackingAdapter(config, client_factory)
        logger = MockLogger()
        
        # Create the service
        service = TimeTrackingService(
            time_tracking_port=time_adapter,
            repository=repository,
            config_provider=config,
            time_format_validator=time_validator,
            logger=logger
        )
        
        print("✅ TimeTrackingService created successfully")
        
        # Test the public validate_time_format method
        print("\n🧪 Testing public validate_time_format method...")
        result = await service.validate_time_format('30m')
        print(f"   ✅ Public method result: {result} (type: {type(result)})")
        
        # Test the private _validate_time_format method - this is where the error likely occurs
        print("\n🧪 Testing private _validate_time_format method...")
        try:
            await service._validate_time_format('30m')
            print("   ✅ Private method completed without error")
        except Exception as e:
            print(f"   🎯 FOUND THE BUG! Private method error: {e}")
            print(f"   Error type: {type(e)}")
            
            # Check if this is our InvalidTimeFormatError with True
            if "Expected format: True" in str(e):
                print("   🎯 CONFIRMED: This is where the 'True' is coming from!")
                
                # Let's trace the exact line where this happens
                import traceback
                print("\n📍 Full traceback:")
                traceback.print_exc()
            
        return True
        
    except Exception as e:
        print(f"❌ Service debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to run all debugging steps."""
    print("🚀 Starting comprehensive bug debugging...\n")
    
    # Step 1: Authentication and basic time validation
    success1 = await debug_with_auth_check()
    
    if not success1:
        print("\n❌ Authentication debug FAILED")
        return False
    
    # Step 2: Deep dive into TimeTrackingService validation
    success2 = await debug_time_tracking_service_validation()
    
    if not success2:
        print("\n❌ Service validation debug FAILED")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 All debugging completed successfully!")
    else:
        print("\n❌ Debugging FAILED - check errors above")
        
    sys.exit(0 if success else 1)
