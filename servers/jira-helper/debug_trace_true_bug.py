#!/usr/bin/env python3
"""
Debug script to trace exactly where the True value is coming from in the time validation bug.
This will add detailed logging to catch the exact location and call stack.
"""

import sys
import os
import asyncio
import traceback
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

async def trace_true_bug():
    """Add detailed tracing to find exactly where True is coming from."""
    print("🔍 Starting detailed trace to find where True is coming from...")
    
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
        server = FastMCP("Debug Jira Helper")
        
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
            
            print("\n🎯 STEP 1: Adding detailed tracing to catch the True bug...")
            
            # Monkey patch the InvalidTimeFormatError to add tracing
            from domain.exceptions import InvalidTimeFormatError
            
            original_init = InvalidTimeFormatError.__init__
            
            def traced_init(self, time_value: str, expected_format):
                print(f"\n🚨 InvalidTimeFormatError CALLED!")
                print(f"   time_value: {time_value!r} (type: {type(time_value)})")
                print(f"   expected_format: {expected_format!r} (type: {type(expected_format)})")
                
                if expected_format is True:
                    print("🎯 FOUND THE BUG! expected_format is True (boolean)")
                    print("📍 Call stack:")
                    for line in traceback.format_stack():
                        print(f"     {line.strip()}")
                
                # Call the original constructor
                original_init(self, time_value, expected_format)
            
            # Apply the monkey patch
            InvalidTimeFormatError.__init__ = traced_init
            
            print("✅ Monkey patch applied to InvalidTimeFormatError")
            
            print("\n🎯 STEP 2: Testing with the traced error constructor...")
            
            try:
                result = await log_work_func(
                    issue_key="ATP-1",
                    time_spent="30m",
                    comment="Debug test to trace True bug",
                    started=None,
                    adjust_estimate="auto",
                    new_estimate=None,
                    reduce_by=None,
                    instance_name="personal"
                )
                
                print(f"✅ Result: {result}")
                
                # Check for the specific error we're debugging
                if not result.get("success", False):
                    error_msg = result.get("error", "")
                    if "Expected format: True" in error_msg:
                        print(f"🎯 CONFIRMED: Found the True bug in result!")
                        print(f"   Error: {error_msg}")
                    else:
                        print(f"❌ Different error: {error_msg}")
                
            except Exception as e:
                print(f"❌ Exception during test: {str(e)}")
                if "Expected format: True" in str(e):
                    print(f"🎯 CONFIRMED: Found the True bug in exception!")
                traceback.print_exc()
            
            return True
                    
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        traceback.print_exc()
        return False


async def trace_validation_chain():
    """Trace the validation chain to see where True is being assigned."""
    print("\n🔍 STEP 3: Tracing the validation chain...")
    
    try:
        # Import validation components
        from domain.services import TimeTrackingService
        from infrastructure.atlassian_time_adapter import AtlassianTimeFormatValidator
        from domain.results import ValidationResult
        from application.base_use_case import BaseUseCase
        
        # Monkey patch the validator to trace its return values
        original_validate = AtlassianTimeFormatValidator.validate_time_format
        
        def traced_validate(self, time_string: str):
            result = original_validate(self, time_string)
            print(f"\n🔍 AtlassianTimeFormatValidator.validate_time_format('{time_string}')")
            print(f"   Result: {result!r} (type: {type(result)})")
            print(f"   Bool value: {bool(result)}")
            
            if result is True:
                print("🚨 VALIDATOR RETURNED True (boolean)!")
                print("📍 Call stack:")
                for line in traceback.format_stack():
                    print(f"     {line.strip()}")
            
            return result
        
        # Apply the monkey patch
        AtlassianTimeFormatValidator.validate_time_format = traced_validate
        
        print("✅ Monkey patch applied to AtlassianTimeFormatValidator")
        
        # Monkey patch ValidationResult constructor to trace where True gets assigned
        original_validation_result_init = ValidationResult.__init__
        
        def traced_validation_result_init(self, is_valid: bool = True, errors=None, warnings=None, context=None):
            print(f"\n🔍 ValidationResult.__init__ CALLED!")
            print(f"   is_valid: {is_valid!r} (type: {type(is_valid)})")
            print(f"   errors: {errors!r} (type: {type(errors)})")
            print(f"   warnings: {warnings!r} (type: {type(warnings)})")
            
            if errors is True:
                print("🚨 FOUND THE BUG! ValidationResult.errors is being set to True (boolean)!")
                print("📍 Call stack:")
                for line in traceback.format_stack():
                    print(f"     {line.strip()}")
            
            # Call the original constructor
            original_validation_result_init(self, is_valid, errors, warnings, context)
        
        # Apply the monkey patch
        ValidationResult.__init__ = traced_validation_result_init
        
        print("✅ Monkey patch applied to ValidationResult")
        
        # Monkey patch str() calls to trace where True gets converted to "True"
        original_str = str
        
        def traced_str(obj):
            result = original_str(obj)
            if obj is True and result == "True":
                print(f"\n🚨 FOUND str(True) CONVERSION!")
                print(f"   Input: {obj!r} (type: {type(obj)})")
                print(f"   Output: {result!r} (type: {type(result)})")
                print("📍 Call stack:")
                for line in traceback.format_stack():
                    print(f"     {line.strip()}")
            return result
        
        # This is too invasive, let's not patch str globally
        # Instead, let's patch the specific BaseUseCase method
        
        # Test the validator directly
        validator = AtlassianTimeFormatValidator()
        print("\n🧪 Testing validator directly...")
        result = validator.validate_time_format('30m')
        print(f"Direct validator result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation chain trace failed: {str(e)}")
        traceback.print_exc()
        return False


async def main():
    """Main function to run all tracing steps."""
    print("🚀 Starting comprehensive True bug tracing...\n")
    
    # Step 1: Trace the InvalidTimeFormatError constructor
    success1 = await trace_true_bug()
    
    if not success1:
        print("\n❌ True bug tracing FAILED")
        return False
    
    # Step 2: Trace the validation chain
    success2 = await trace_validation_chain()
    
    if not success2:
        print("\n❌ Validation chain tracing FAILED")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 All tracing completed successfully!")
    else:
        print("\n❌ Tracing FAILED - check errors above")
        
    sys.exit(0 if success else 1)
