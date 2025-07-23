#!/usr/bin/env python3
"""
Direct test for work logging functionality to debug the "can only join an iterable" error.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Settings
from infrastructure.atlassian_api_adapter import AtlassianApiJiraClientFactory
from infrastructure.atlassian_time_adapter import AtlassianTimeTrackingAdapter
from domain.models import WorkLogRequest


async def test_work_logging():
    """Test work logging directly."""
    print("🧪 Testing work logging functionality...")
    
    try:
        # Set up configuration
        config_provider = Settings()
        print("✅ Configuration loaded")
        
        # Set up client factory
        client_factory = AtlassianApiJiraClientFactory(config_provider)
        print("✅ Client factory created")
        
        # Set up time tracking adapter
        time_adapter = AtlassianTimeTrackingAdapter(config_provider, client_factory)
        print("✅ Time tracking adapter created")
        
        # Test creating a WorkLogRequest (this is where the error might occur)
        print("\n🔍 Testing WorkLogRequest creation...")
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
            
        except Exception as e:
            print(f"❌ WorkLogRequest creation failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return
        
        # Test the actual work logging
        print("\n🔍 Testing actual work logging...")
        try:
            result = await time_adapter.log_work(work_log_request, "personal")
            print("✅ Work logging completed")
            print(f"   Result: {result}")
            
        except Exception as e:
            print(f"❌ Work logging failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return
            
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_work_logging())
