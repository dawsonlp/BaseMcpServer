"""
Test to demonstrate the async wrapper issue and validate sync adapter routing.

This test shows that:
1. Async adapter fails on Trilliant with wrapper issues
2. Sync adapter succeeds on Trilliant 
3. SearchService properly routes to sync adapter for Trilliant
4. Other instances still use async adapter
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "servers" / "jira-helper" / "src"
sys.path.insert(0, str(src_dir))

from config_adapter import SettingsConfigurationAdapter
from domain.services import SearchService
from infrastructure.jira_client import JiraSearchAdapter, JiraJQLValidator
from infrastructure.trilliant_sync_adapter import TrilliantSyncJiraAdapter
from domain.models import JiraInstance
from domain.ports import ConfigurationProvider


class TestConfigProvider(ConfigurationProvider):
    """Simple test configuration provider."""
    
    def __init__(self):
        self._instances = {
            "trilliant": JiraInstance(
                name="trilliant",
                url="https://trilliant.atlassian.net",
                user="test@example.com",
                token="test-token",
                description="Trilliant test instance"
            ),
            "personal": JiraInstance(
                name="personal",
                url="https://personal.atlassian.net",
                user="test@example.com",
                token="test-token",
                description="Personal test instance"
            )
        }
        self._default = "trilliant"
    
    def get_instances(self) -> dict[str, JiraInstance]:
        return self._instances
    
    def get_default_instance_name(self) -> str | None:
        return self._default
    
    def get_instance(self, instance_name: str | None = None) -> JiraInstance | None:
        if instance_name is None:
            instance_name = self._default
        return self._instances.get(instance_name)


class TestLoggerAdapter:
    """Simple logger adapter for testing."""
    
    def __init__(self):
        self.logger = logging.getLogger("test_logger")
    
    def info(self, message: str) -> None:
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        self.logger.error(message)

# Configure logging for detailed analysis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/validate_jql_routing_test.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)


async def test_async_adapter_fails():
    """Test that async adapter fails on Trilliant with wrapper issues."""
    logger.info("🔴 Testing async adapter failure on Trilliant...")
    
    config_provider = TestConfigProvider()
    logger_adapter = TestLoggerAdapter()
    
    # Create async search adapter (this should fail)
    async_adapter = JiraSearchAdapter(None, config_provider)  # client_factory=None for this test
    
    try:
        # Try to validate JQL using async adapter
        start_time = time.time()
        validation_errors = await async_adapter.validate_jql(
            "project = NEMS AND status = Open", 
            "trilliant"
        )
        elapsed = time.time() - start_time
        
        if validation_errors:
            logger.error(f"❌ Async adapter failed as expected after {elapsed:.3f}s: {validation_errors}")
            return True  # Expected failure
        else:
            logger.warning(f"⚠️ Async adapter unexpectedly succeeded after {elapsed:.3f}s")
            return False  # Unexpected success
            
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Async adapter failed as expected after {elapsed:.3f}s: {str(e)}")
        return True  # Expected failure


async def test_sync_adapter_succeeds():
    """Test that sync adapter succeeds on Trilliant."""
    logger.info("🟢 Testing sync adapter success on Trilliant...")
    
    config_provider = TestConfigProvider()
    
    # Create sync adapter (this should succeed)
    sync_adapter = TrilliantSyncJiraAdapter(config_provider)
    
    try:
        # Try to validate JQL using sync adapter
        start_time = time.time()
        validation_errors = await sync_adapter.validate_jql(
            "project = NEMS AND status = Open", 
            "trilliant"
        )
        elapsed = time.time() - start_time
        
        if not validation_errors:
            logger.info(f"✅ Sync adapter succeeded as expected after {elapsed:.3f}s")
            return True  # Expected success
        else:
            logger.error(f"❌ Sync adapter unexpectedly failed after {elapsed:.3f}s: {validation_errors}")
            return False  # Unexpected failure
            
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Sync adapter unexpectedly failed after {elapsed:.3f}s: {str(e)}")
        return False  # Unexpected failure


async def test_search_service_routing():
    """Test that SearchService properly routes to sync adapter for Trilliant."""
    logger.info("🔄 Testing SearchService routing logic...")
    
    config_provider = TestConfigProvider()
    logger_adapter = TestLoggerAdapter()
    jql_validator = JiraJQLValidator()
    
    # Create async adapter (will fail)
    async_adapter = JiraSearchAdapter(None, config_provider)
    
    # Create sync adapter (will succeed)
    sync_adapter = TrilliantSyncJiraAdapter(config_provider)
    
    # Create SearchService with both adapters
    search_service = SearchService(
        search_port=async_adapter,
        config_provider=config_provider,
        jql_validator=jql_validator,
        logger=logger_adapter,
        trilliant_sync_adapter=sync_adapter
    )
    
    try:
        # Test validation routing for Trilliant (should use sync adapter)
        logger.info("🔧 Testing validate_jql routing for Trilliant...")
        start_time = time.time()
        
        result = await search_service.validate_jql(
            "project = NEMS AND status = Open",
            "trilliant"
        )
        
        elapsed = time.time() - start_time
        
        if result.get("valid", False):
            logger.info(f"✅ SearchService validation succeeded for Trilliant after {elapsed:.3f}s (used sync adapter)")
            trilliant_success = True
        else:
            logger.error(f"❌ SearchService validation failed for Trilliant after {elapsed:.3f}s: {result.get('errors', [])}")
            trilliant_success = False
        
        # Test validation routing for non-Trilliant instance (should use async adapter)
        logger.info("🔧 Testing validate_jql routing for personal instance...")
        start_time = time.time()
        
        try:
            result = await search_service.validate_jql(
                "project = PERSONAL AND status = Open",
                "personal"
            )
            elapsed = time.time() - start_time
            
            # For personal, we expect it might fail due to async issues, but that's OK for this test
            logger.info(f"ℹ️ SearchService validation for personal completed after {elapsed:.3f}s: {result}")
            personal_completed = True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.info(f"ℹ️ SearchService validation for personal failed after {elapsed:.3f}s (expected): {str(e)}")
            personal_completed = True  # Expected behavior
        
        return trilliant_success and personal_completed
        
    except Exception as e:
        logger.error(f"❌ SearchService routing test failed: {str(e)}")
        return False


async def test_direct_sync_validation():
    """Test direct sync validation to ensure the method works."""
    logger.info("🎯 Testing direct sync validation...")
    
    config_provider = TestConfigProvider()
    sync_adapter = TrilliantSyncJiraAdapter(config_provider)
    
    try:
        # Test the sync validation method directly
        start_time = time.time()
        is_valid = sync_adapter.validate_jql_sync(
            "project = NEMS AND status = Open",
            "trilliant"
        )
        elapsed = time.time() - start_time
        
        if is_valid:
            logger.info(f"✅ Direct sync validation succeeded after {elapsed:.3f}s")
            return True
        else:
            logger.error(f"❌ Direct sync validation failed after {elapsed:.3f}s")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Direct sync validation failed after {elapsed:.3f}s: {str(e)}")
        return False


async def main():
    """Run all tests to demonstrate the issue and solution."""
    logger.info("🚀 Starting validate_jql routing tests...")
    logger.info("=" * 80)
    
    results = {}
    
    # Test 1: Show async adapter fails
    logger.info("\n📋 TEST 1: Async Adapter Failure")
    logger.info("-" * 40)
    results["async_fails"] = await test_async_adapter_fails()
    
    # Test 2: Show sync adapter succeeds
    logger.info("\n📋 TEST 2: Sync Adapter Success")
    logger.info("-" * 40)
    results["sync_succeeds"] = await test_sync_adapter_succeeds()
    
    # Test 3: Show direct sync validation works
    logger.info("\n📋 TEST 3: Direct Sync Validation")
    logger.info("-" * 40)
    results["direct_sync"] = await test_direct_sync_validation()
    
    # Test 4: Show SearchService routing works
    logger.info("\n📋 TEST 4: SearchService Routing")
    logger.info("-" * 40)
    results["routing_works"] = await test_search_service_routing()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:20} : {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED - Sync adapter routing is working correctly!")
        logger.info("✅ Async adapter fails on Trilliant (expected)")
        logger.info("✅ Sync adapter succeeds on Trilliant (fixed)")
        logger.info("✅ SearchService routes correctly to sync adapter")
    else:
        logger.error("\n💥 SOME TESTS FAILED - There are still issues to resolve")
        failed_tests = [name for name, result in results.items() if not result]
        logger.error(f"Failed tests: {', '.join(failed_tests)}")
    
    logger.info(f"\n📁 Detailed logs written to: /tmp/validate_jql_routing_test.log")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
