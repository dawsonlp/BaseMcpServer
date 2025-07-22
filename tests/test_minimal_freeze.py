"""
Minimal test to isolate the exact Trilliant freeze issue.

This test creates the smallest possible reproduction of the problem:
- One piece of code that works (synchronous)
- One piece of code that freezes (async wrapper)
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "servers" / "jira-helper" / "src"
sys.path.insert(0, str(src_dir))

from jira import JIRA
from infrastructure.config_adapter import ConfigurationAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_sync_works():
    """Test that synchronous JIRA calls work fine."""
    logger.info("🟢 Testing SYNCHRONOUS call (should work)")
    
    config_provider = ConfigurationAdapter()
    instance_config = config_provider.get_instance("trilliant")
    
    start_time = time.time()
    
    # Create synchronous JIRA client
    client = JIRA(
        server=instance_config.url,
        basic_auth=(instance_config.user, instance_config.token),
        options={'verify': True}
    )
    
    # Make synchronous call
    try:
        result = client.search_issues("project = NEMS", maxResults=1, validate_query=True)
        elapsed = time.time() - start_time
        logger.info(f"✅ SYNC call completed in {elapsed:.3f}s - Found {len(result)} issues")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ SYNC call failed after {elapsed:.3f}s: {e}")
        return False


async def test_async_freezes():
    """Test that async wrapper freezes."""
    logger.info("🔴 Testing ASYNC wrapper (should freeze)")
    
    config_provider = ConfigurationAdapter()
    instance_config = config_provider.get_instance("trilliant")
    
    start_time = time.time()
    
    # Create synchronous JIRA client (same as above)
    client = JIRA(
        server=instance_config.url,
        basic_auth=(instance_config.user, instance_config.token),
        options={'verify': True}
    )
    
    # Make the SAME call but wrapped in asyncio
    try:
        # This is the problematic pattern - running sync code in async context
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: client.search_issues("project = NEMS", maxResults=1, validate_query=True)
        )
        elapsed = time.time() - start_time
        logger.info(f"✅ ASYNC call completed in {elapsed:.3f}s - Found {len(result)} issues")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ ASYNC call failed after {elapsed:.3f}s: {e}")
        return False


async def main():
    """Run the minimal test."""
    logger.info("🧪 MINIMAL FREEZE TEST - Isolating the exact issue")
    logger.info("=" * 60)
    
    # Test 1: Synchronous (should work)
    sync_works = test_sync_works()
    
    logger.info("-" * 60)
    
    # Test 2: Async wrapper with timeout (should freeze)
    logger.info("⏰ Starting async test with 10 second timeout...")
    try:
        async_works = await asyncio.wait_for(test_async_freezes(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("⏰ ASYNC test timed out after 10 seconds (this proves the issue)")
        async_works = False
    
    logger.info("=" * 60)
    logger.info(f"📊 RESULTS:")
    logger.info(f"   Synchronous call: {'✅ WORKS' if sync_works else '❌ FAILS'}")
    logger.info(f"   Async wrapper:    {'✅ WORKS' if async_works else '❌ FREEZES'}")
    
    if sync_works and not async_works:
        logger.info("🎯 CONFIRMED: The issue is with async wrapper, not the Jira API itself")
    else:
        logger.info("🤔 Unexpected results - need further investigation")


if __name__ == "__main__":
    asyncio.run(main())
