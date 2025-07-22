"""
Test the exact code path that's freezing in the jira-helper infrastructure.

This replicates the exact sequence that causes the freeze.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "servers" / "jira-helper" / "src"
sys.path.insert(0, str(src_dir))

from infrastructure.config_adapter import ConfigurationAdapter
from infrastructure.jira_client import JiraSearchAdapter, JiraClientFactoryImpl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_exact_infrastructure_path():
    """Test the exact infrastructure code path that freezes."""
    logger.info("🔴 Testing EXACT infrastructure path (should freeze)")
    
    start_time = time.time()
    
    try:
        # This is the exact sequence from the jira-helper infrastructure
        config_provider = ConfigurationAdapter()
        client_factory = JiraClientFactoryImpl(config_provider)
        search_adapter = JiraSearchAdapter(client_factory, config_provider)
        
        # This is the exact call that freezes
        validation_errors = await search_adapter.validate_jql("project = NEMS", "trilliant")
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Infrastructure path completed in {elapsed:.3f}s - Errors: {validation_errors}")
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Infrastructure path failed after {elapsed:.3f}s: {e}")
        return False


async def test_direct_jira_client_factory():
    """Test just the client factory part."""
    logger.info("🟡 Testing just the client factory")
    
    start_time = time.time()
    
    try:
        config_provider = ConfigurationAdapter()
        client_factory = JiraClientFactoryImpl(config_provider)
        
        # Get the client
        client = await client_factory.get_client("trilliant")
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Client factory completed in {elapsed:.3f}s")
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Client factory failed after {elapsed:.3f}s: {e}")
        return False


async def main():
    """Run the exact path test."""
    logger.info("🧪 EXACT FREEZE PATH TEST")
    logger.info("=" * 60)
    
    # Test 1: Just the client factory
    logger.info("⏰ Testing client factory with 5 second timeout...")
    try:
        factory_works = await asyncio.wait_for(test_direct_jira_client_factory(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("⏰ Client factory timed out after 5 seconds")
        factory_works = False
    
    logger.info("-" * 60)
    
    # Test 2: Full infrastructure path
    logger.info("⏰ Testing full infrastructure path with 10 second timeout...")
    try:
        infra_works = await asyncio.wait_for(test_exact_infrastructure_path(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("⏰ Infrastructure path timed out after 10 seconds (this is the issue)")
        infra_works = False
    
    logger.info("=" * 60)
    logger.info(f"📊 RESULTS:")
    logger.info(f"   Client factory:       {'✅ WORKS' if factory_works else '❌ FREEZES'}")
    logger.info(f"   Full infrastructure:  {'✅ WORKS' if infra_works else '❌ FREEZES'}")
    
    if factory_works and not infra_works:
        logger.info("🎯 CONFIRMED: The issue is in the JiraSearchAdapter.validate_jql method")
    elif not factory_works:
        logger.info("🎯 CONFIRMED: The issue is in the JiraClientFactory")
    else:
        logger.info("🤔 Both work - the issue might be elsewhere")


if __name__ == "__main__":
    asyncio.run(main())
