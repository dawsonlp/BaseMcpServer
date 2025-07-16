"""
Test the foundation layer base classes and decorators.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

# Import our new foundation classes
from src.domain.base import BaseResult, FieldValidator, validate_required_fields
from src.domain.base_service import BaseJiraService
from src.utils.decorators import validate_issue_key, validate_project_key, log_operation


# Mock dependencies for testing
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
    
    def info(self, msg):
        self.messages.append(f"INFO: {msg}")
    
    def error(self, msg):
        self.messages.append(f"ERROR: {msg}")


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
        instance_name = self._resolve_instance_name(instance_name)
        return f"Issue {issue_key} from {instance_name}"
    
    @validate_project_key
    @log_operation()
    async def get_project(self, project_key: str, instance_name: Optional[str] = None):
        instance_name = self._resolve_instance_name(instance_name)
        return f"Project {project_key} from {instance_name}"


async def test_foundation():
    print("🧪 Testing foundation layer...")
    
    # Test BaseResult
    print("\n1️⃣ Testing BaseResult:")
    result = BaseResult(success=True)
    result.add_detail("test", "value")
    print(f"   ✅ BaseResult: success={result.is_successful()}, details={result.details}")
    
    error_result = BaseResult(success=False, error="Test error")
    print(f"   ✅ Error result: success={error_result.is_successful()}, error={error_result.error}")
    
    # Test FieldValidator
    print("\n2️⃣ Testing FieldValidator:")
    try:
        FieldValidator.validate_issue_key("PROJ-123")
        print("   ✅ Valid issue key accepted")
    except ValueError as e:
        print(f"   ❌ Unexpected error: {e}")
    
    try:
        FieldValidator.validate_issue_key("invalid")
        print("   ❌ Invalid issue key should have failed")
    except ValueError:
        print("   ✅ Invalid issue key correctly rejected")
    
    # Test validate_required_fields decorator
    print("\n3️⃣ Testing validate_required_fields decorator:")
    try:
        valid_request = TestRequest(project_key="PROJ", summary="Test")
        print("   ✅ Valid request created successfully")
    except ValueError as e:
        print(f"   ❌ Unexpected error: {e}")
    
    try:
        invalid_request = TestRequest(project_key="", summary="Test")
        print("   ❌ Empty project_key should have failed")
    except ValueError as e:
        print(f"   ✅ Empty project_key correctly rejected: {e}")
    
    # Test BaseJiraService
    print("\n4️⃣ Testing BaseJiraService:")
    config_provider = MockConfigProvider()
    logger = MockLogger()
    
    service = TestService(config_provider=config_provider, logger=logger)
    
    # Test successful operation
    try:
        result = await service.get_issue("PROJ-123")
        print(f"   ✅ get_issue result: {result}")
    except Exception as e:
        print(f"   ❌ get_issue failed: {e}")
    
    # Test validation decorator
    try:
        await service.get_issue("invalid-key")
        print("   ❌ Invalid issue key should have failed")
    except ValueError as e:
        print(f"   ✅ Invalid issue key correctly rejected by decorator: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error type: {type(e).__name__}: {e}")
    
    # Test project validation
    try:
        result = await service.get_project("PROJ")
        print(f"   ✅ get_project result: {result}")
    except Exception as e:
        print(f"   ❌ get_project failed: {e}")
    
    # Check logging
    print("\n5️⃣ Testing logging:")
    for message in logger.messages:
        print(f"   📝 {message}")
    
    print("\n🎉 Foundation layer test complete!")


if __name__ == "__main__":
    asyncio.run(test_foundation())
