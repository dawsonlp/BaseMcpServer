#!/usr/bin/env python3
"""
Extended test for work logging to debug the "can only join an iterable" error.
Tests the full path from domain through application to infrastructure layers.
"""

import sys
import os
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_worklog_request_creation():
    """Test WorkLogRequest creation directly."""
    print("🧪 Testing WorkLogRequest creation...")
    
    try:
        from domain.models import WorkLogRequest
        print("✅ Successfully imported WorkLogRequest")
        
        # Test creating a WorkLogRequest (this is where the error might occur)
        print("\n🔍 Testing WorkLogRequest creation with valid parameters...")
        try:
            work_log_request = WorkLogRequest(
                issue_key="ATP-45",
                time_spent="2h 30m",
                comment="Test work log entry",
                started=None,
                adjust_estimate="auto",
                new_estimate=None,
                reduce_by=None
            )
            print("✅ WorkLogRequest created successfully")
            print(f"   Issue Key: {work_log_request.issue_key}")
            print(f"   Time Spent: {work_log_request.time_spent}")
            print(f"   Adjust Estimate: {work_log_request.adjust_estimate}")
            print(f"   Comment: {work_log_request.comment}")
            
        except Exception as e:
            print(f"❌ WorkLogRequest creation failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test with invalid adjust_estimate to trigger the validation error
        print("\n🔍 Testing WorkLogRequest creation with invalid adjust_estimate...")
        try:
            invalid_request = WorkLogRequest(
                issue_key="ATP-45",
                time_spent="2h 30m",
                comment="Test work log entry",
                started=None,
                adjust_estimate="invalid_option",  # This should trigger the error
                new_estimate=None,
                reduce_by=None
            )
            print("❌ Should have failed with invalid adjust_estimate")
            return False
            
        except Exception as e:
            print(f"✅ Expected validation error occurred: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check if this is the "can only join an iterable" error
            if "can only join an iterable" in str(e):
                print("🎯 Found the 'can only join an iterable' error!")
                import traceback
                traceback.print_exc()
                return False
            else:
                print("✅ Validation error is working correctly")
            
    except Exception as e:
        print(f"❌ Import or setup failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_use_case_layer():
    """Test the application use case layer."""
    print("\n🧪 Testing Use Case Layer...")
    
    try:
        # Import use case and check how it gets dependencies
        from application.use_cases import LogWorkUseCase
        from application.base_use_case import BaseCommandUseCase
        from infrastructure.atlassian_time_adapter import AtlassianTimeTrackingAdapter
        from infrastructure.atlassian_api_adapter import AtlassianApiJiraClientFactory
        import os
        from dotenv import load_dotenv
        print("✅ Successfully imported use case components")
        
        # Load real authentication from ~/.env
        env_path = os.path.expanduser("~/.env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print("✅ Loaded ~/.env file")
        else:
            # Try tests/.env as fallback
            test_env_path = os.path.join(os.path.dirname(__file__), "..", "tests", ".env")
            if os.path.exists(test_env_path):
                load_dotenv(test_env_path)
                print("✅ Loaded tests/.env file")
            else:
                print("❌ No .env file found")
                return False
        
        # Create real configuration using environment variables
        class MockJiraInstance:
            def __init__(self, name, url, user, token):
                self.name = name
                self.url = url
                self.user = user
                self.token = token
                self.description = f"Test instance: {name}"
        
        class RealConfig:
            def get_instance(self, name):
                if name == "personal":
                    return MockJiraInstance(
                        name="personal",
                        url=os.getenv('JIRA_URL'),
                        user=os.getenv('JIRA_USER'),
                        token=os.getenv('JIRA_API_TOKEN')
                    )
                return None
        
        config = RealConfig()
        instance = config.get_instance('personal')
        print("✅ Real configuration created")
        print(f"   URL: {instance.url}")
        print(f"   User: {instance.user}")
        print(f"   Token: {'*' * 20}...")
        
        # Try to create the infrastructure components
        try:
            client_factory = AtlassianApiJiraClientFactory(config)
            time_adapter = AtlassianTimeTrackingAdapter(config, client_factory)
            print("✅ Infrastructure components created")
            
            # Create use case with proper dependency injection
            use_case = LogWorkUseCase()
            # The LogWorkUseCase should get its dependencies through the base class
            # Let's check what dependencies it expects
            print(f"✅ Use case created: {use_case}")
            print(f"   Use case type: {type(use_case)}")
            print(f"   Base classes: {type(use_case).__bases__}")
            
            # Check if it has the expected service attribute
            if hasattr(use_case, '_time_tracking_service'):
                print(f"   Has _time_tracking_service: {use_case._time_tracking_service}")
            else:
                print("   No _time_tracking_service attribute found")
                # Let's try to set it manually
                use_case._time_tracking_service = time_adapter  # Use adapter directly
                print("   Set _time_tracking_service to time_adapter")
            
            # Test use case execution
            print("\n🔍 Testing use case execution...")
            try:
                result = await use_case.execute(
                    issue_key="ATP-45",
                    time_spent="2h 30m",
                    comment="Test work log entry",
                    started=None,
                    adjust_estimate="auto",
                    new_estimate=None,
                    reduce_by=None,
                    instance_name="personal"
                )
                print("✅ Use case execution completed")
                print(f"   Result: {result}")
                
            except Exception as e:
                print(f"❌ Use case execution failed: {str(e)}")
                print(f"   Error type: {type(e).__name__}")
                
                # Check if this is the "can only join an iterable" error
                if "can only join an iterable" in str(e):
                    print("🎯 Found the 'can only join an iterable' error in use case layer!")
                    import traceback
                    traceback.print_exc()
                    return False
                else:
                    print("✅ Different error - let's see the full traceback:")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"❌ Infrastructure setup failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check if this is the "can only join an iterable" error
            if "can only join an iterable" in str(e):
                print("🎯 Found the 'can only join an iterable' error in infrastructure setup!")
                import traceback
                traceback.print_exc()
                return False
            else:
                print("✅ Different error - let's see the full traceback:")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Use case layer test failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check if this is the "can only join an iterable" error
        if "can only join an iterable" in str(e):
            print("🎯 Found the 'can only join an iterable' error in use case imports!")
            import traceback
            traceback.print_exc()
            return False
        else:
            print("✅ Different error - let's see the full traceback:")
            import traceback
            traceback.print_exc()
    
    return True


def test_validation_result():
    """Test ValidationResult to see if the error is there."""
    print("\n🧪 Testing ValidationResult...")
    
    try:
        from domain.results import ValidationResult
        print("✅ Successfully imported ValidationResult")
        
        # Test creating validation result with errors
        print("\n🔍 Testing ValidationResult with errors...")
        try:
            validation_result = ValidationResult.invalid(
                errors=["Error 1", "Error 2", "Error 3"],
                warnings=["Warning 1"]
            )
            print("✅ ValidationResult created successfully")
            
            # Test error summary (this might be where the join error occurs)
            error_summary = validation_result.get_error_summary()
            print(f"✅ Error summary: {error_summary}")
            
            # Test joining errors manually
            joined_errors = "; ".join(validation_result.errors)
            print(f"✅ Manual join: {joined_errors}")
            
        except Exception as e:
            print(f"❌ ValidationResult test failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check if this is the "can only join an iterable" error
            if "can only join an iterable" in str(e):
                print("🎯 Found the 'can only join an iterable' error in ValidationResult!")
                import traceback
                traceback.print_exc()
                return False
            
    except Exception as e:
        print(f"❌ ValidationResult import failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting comprehensive work logging debug tests...\n")
    
    # Test 1: Domain layer
    success1 = test_worklog_request_creation()
    
    # Test 2: ValidationResult
    success2 = test_validation_result()
    
    # Test 3: Use case layer
    success3 = await test_use_case_layer()
    
    if success1 and success2 and success3:
        print("\n🎉 All tests completed successfully!")
        return True
    else:
        print("\n❌ Some tests failed - check output above for 'can only join an iterable' errors")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
