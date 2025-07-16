"""
Debug the decorator issues to understand what's happening.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

# Import our foundation classes
from src.domain.base import BaseResult, FieldValidator, validate_required_fields
from src.domain.base_service import BaseJiraService
from src.utils.decorators import validate_issue_key, validate_project_key, log_operation


# Mock dependencies
class MockConfigProvider:
    def get_default_instance_name(self):
        return "test-instance"
    
    def get_instances(self):
        return {"test-instance": {"url": "http://test.com"}}


class MockLogger:
    def __init__(self):
        self.messages = []
    
    def debug(self, msg):
        self.messages.append(f"DEBUG: {msg}")
        print(f"LOGGER DEBUG: {msg}")
    
    def info(self, msg):
        self.messages.append(f"INFO: {msg}")
        print(f"LOGGER INFO: {msg}")
    
    def error(self, msg):
        self.messages.append(f"ERROR: {msg}")
        print(f"LOGGER ERROR: {msg}")


# Test the validate_required_fields decorator
@validate_required_fields('project_key', 'summary')
@dataclass
class TestRequest:
    project_key: str
    summary: str
    description: str = ""


# Test service using base class
class TestService(BaseJiraService):
    @validate_issue_key
    @log_operation("get_test_issue")
    async def get_issue(self, issue_key: str, instance_name: Optional[str] = None):
        print(f"INSIDE get_issue: issue_key='{issue_key}', instance_name='{instance_name}'")
        instance_name = self._resolve_instance_name(instance_name)
        return f"Issue {issue_key} from {instance_name}"


async def debug_decorators():
    print("🔍 Debugging decorators...")
    
    # Test 1: Dataclass validation
    print("\n1️⃣ Testing dataclass validation:")
    print("Creating valid request...")
    try:
        valid_request = TestRequest(project_key="PROJ", summary="Test")
        print(f"✅ Valid request created: {valid_request}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\nCreating invalid request with empty project_key...")
    try:
        invalid_request = TestRequest(project_key="", summary="Test")
        print(f"❌ Invalid request should have failed but got: {invalid_request}")
    except Exception as e:
        print(f"✅ Invalid request correctly rejected: {e}")
    
    print("\nCreating invalid request with None project_key...")
    try:
        # This should trigger the validation
        invalid_request2 = TestRequest(project_key=None, summary="Test")
        print(f"❌ Invalid request should have failed but got: {invalid_request2}")
    except Exception as e:
        print(f"✅ Invalid request correctly rejected: {e}")
    
    # Test 2: Service decorator validation
    print("\n2️⃣ Testing service decorator validation:")
    config_provider = MockConfigProvider()
    logger = MockLogger()
    
    service = TestService(config_provider=config_provider, logger=logger)
    
    print("\nTesting valid issue key...")
    try:
        result = await service.get_issue("PROJ-123")
        print(f"✅ Valid issue key result: {result}")
    except Exception as e:
        print(f"❌ Valid issue key failed: {e}")
    
    print("\nTesting invalid issue key...")
    try:
        result = await service.get_issue("invalid-key")
        print(f"❌ Invalid issue key should have failed but got: {result}")
    except Exception as e:
        print(f"✅ Invalid issue key correctly rejected: {e}")
    
    print("\nTesting empty issue key...")
    try:
        result = await service.get_issue("")
        print(f"❌ Empty issue key should have failed but got: {result}")
    except Exception as e:
        print(f"✅ Empty issue key correctly rejected: {e}")
    
    print("\n🔍 Debug complete!")


if __name__ == "__main__":
    asyncio.run(debug_decorators())
