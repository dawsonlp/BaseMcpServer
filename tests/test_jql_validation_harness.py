#!/usr/bin/env python3
"""
JQL Validation Test Harness

This test harness allows rapid iteration on JQL validation issues
by testing directly against Jira instances without the MCP server overhead.
"""

import asyncio
import sys
import os
import time
import logging
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'servers', 'jira-helper', 'src'))

from infrastructure.jira_client import JiraClientFactoryImpl, JiraSearchAdapter
from config import Settings
from config_adapter import SettingsConfigurationAdapter

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/jql_validation_test.log')
    ]
)

logger = logging.getLogger(__name__)


class JQLValidationTester:
    """Test harness for JQL validation across different Jira instances."""
    
    def __init__(self):
        """Initialize the test harness."""
        self.settings = Settings()
        self.config_provider = SettingsConfigurationAdapter(self.settings)
        self.client_factory = JiraClientFactoryImpl(self.config_provider)
        self.search_adapters = {}
        
        # Initialize search adapters for each instance
        for instance_name in self.config_provider.get_instances().keys():
            self.search_adapters[instance_name] = JiraSearchAdapter(
                self.client_factory, 
                self.config_provider
            )
    
    async def test_jql_patterns(self, instance_name: str, jql_patterns: List[str]) -> Dict[str, Any]:
        """Test multiple JQL patterns against a specific instance."""
        logger.info(f"🧪 Testing {len(jql_patterns)} JQL patterns against {instance_name}")
        
        results = {
            'instance': instance_name,
            'patterns_tested': len(jql_patterns),
            'results': []
        }
        
        search_adapter = self.search_adapters.get(instance_name)
        if not search_adapter:
            logger.error(f"❌ No search adapter found for instance: {instance_name}")
            return results
        
        for i, jql in enumerate(jql_patterns, 1):
            logger.info(f"🔍 [{i}/{len(jql_patterns)}] Testing JQL: {jql}")
            
            result = await self.test_single_jql(search_adapter, jql, instance_name)
            results['results'].append(result)
            
            # Add delay between tests to avoid overwhelming the server
            await asyncio.sleep(1)
        
        return results
    
    async def test_single_jql(self, search_adapter: JiraSearchAdapter, jql: str, instance_name: str) -> Dict[str, Any]:
        """Test a single JQL pattern with detailed timing and error capture."""
        start_time = time.time()
        
        result = {
            'jql': jql,
            'instance': instance_name,
            'success': False,
            'validation_time': 0,
            'search_time': 0,
            'total_time': 0,
            'error': None,
            'error_type': None,
            'issues_found': 0,
            'total_available': 0
        }
        
        try:
            # Test JQL validation first
            logger.info(f"🔒 Starting JQL validation for: {jql}")
            validation_start = time.time()
            
            validation_errors = await search_adapter.validate_jql(jql, instance_name)
            validation_time = time.time() - validation_start
            result['validation_time'] = validation_time
            
            if validation_errors:
                result['error'] = f"JQL validation failed: {'; '.join(validation_errors)}"
                result['error_type'] = 'validation_error'
                logger.warning(f"⚠️  JQL validation failed in {validation_time:.3f}s: {result['error']}")
            else:
                logger.info(f"✅ JQL validation passed in {validation_time:.3f}s")
                
                # If validation passes, try the actual search
                try:
                    from domain.models import SearchQuery
                    
                    search_start = time.time()
                    query = SearchQuery(jql=jql, max_results=1, start_at=0)
                    
                    logger.info(f"🔍 Starting JQL search for: {jql}")
                    search_result = await search_adapter.search_issues(query, instance_name)
                    search_time = time.time() - search_start
                    
                    result['search_time'] = search_time
                    result['issues_found'] = len(search_result.issues)
                    result['total_available'] = search_result.total_results
                    result['success'] = True
                    
                    logger.info(f"✅ JQL search completed in {search_time:.3f}s - Found {result['issues_found']} issues (total: {result['total_available']})")
                    
                except Exception as search_error:
                    search_time = time.time() - search_start
                    result['search_time'] = search_time
                    result['error'] = f"JQL search failed: {str(search_error)}"
                    result['error_type'] = 'search_error'
                    logger.error(f"❌ JQL search failed in {search_time:.3f}s: {result['error']}")
        
        except Exception as validation_error:
            validation_time = time.time() - validation_start if 'validation_start' in locals() else 0
            result['validation_time'] = validation_time
            result['error'] = f"JQL validation exception: {str(validation_error)}"
            result['error_type'] = 'validation_exception'
            logger.error(f"❌ JQL validation exception in {validation_time:.3f}s: {result['error']}")
        
        result['total_time'] = time.time() - start_time
        return result
    
    def print_results_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of test results."""
        instance = results['instance']
        patterns_tested = results['patterns_tested']
        test_results = results['results']
        
        print(f"\n📊 JQL Validation Test Results for {instance}")
        print(f"{'='*60}")
        print(f"Patterns tested: {patterns_tested}")
        
        successful = [r for r in test_results if r['success']]
        validation_errors = [r for r in test_results if r['error_type'] == 'validation_error']
        search_errors = [r for r in test_results if r['error_type'] == 'search_error']
        exceptions = [r for r in test_results if r['error_type'] in ['validation_exception', 'search_error']]
        
        print(f"✅ Successful: {len(successful)}")
        print(f"⚠️  Validation errors: {len(validation_errors)}")
        print(f"❌ Search errors: {len(search_errors)}")
        print(f"💥 Exceptions: {len(exceptions)}")
        
        print(f"\n📈 Performance Summary:")
        if successful:
            avg_validation = sum(r['validation_time'] for r in successful) / len(successful)
            avg_search = sum(r['search_time'] for r in successful) / len(successful)
            avg_total = sum(r['total_time'] for r in successful) / len(successful)
            
            print(f"   Average validation time: {avg_validation:.3f}s")
            print(f"   Average search time: {avg_search:.3f}s")
            print(f"   Average total time: {avg_total:.3f}s")
        
        print(f"\n📋 Detailed Results:")
        for i, result in enumerate(test_results, 1):
            status = "✅" if result['success'] else "❌"
            jql = result['jql'][:50] + "..." if len(result['jql']) > 50 else result['jql']
            
            print(f"   {i:2d}. {status} {jql}")
            print(f"       Time: {result['total_time']:.3f}s (val: {result['validation_time']:.3f}s, search: {result['search_time']:.3f}s)")
            
            if result['success']:
                print(f"       Found: {result['issues_found']} issues (total: {result['total_available']})")
            else:
                print(f"       Error: {result['error']}")
            print()


def generate_test_patterns_for_instance(instance_name: str) -> List[str]:
    """Generate appropriate test patterns for each instance with correct project names."""
    
    # Map instances to their project keys and sample issue keys
    instance_projects = {
        'personal': {'project': 'FORGE', 'sample_key': 'FORGE-1'},
        'highspring': {'project': 'TRIL', 'sample_key': 'TRIL-1'},
        'trilliant': {'project': 'NEMS', 'sample_key': 'NEMS-1'}
    }
    
    if instance_name not in instance_projects:
        logger.warning(f"Unknown instance {instance_name}, using NEMS as default")
        project_info = {'project': 'NEMS', 'sample_key': 'NEMS-1'}
    else:
        project_info = instance_projects[instance_name]
    
    project = project_info['project']
    sample_key = project_info['sample_key']
    
    return [
        # Basic patterns
        f"key = {sample_key}",
        f"project = {project}",
        f"project in ({project})",
        
        # With ORDER BY
        f"project = {project} ORDER BY key",
        f"project = {project} ORDER BY created DESC",
        f"project in ({project}) ORDER BY key",
        f"project in ({project}) ORDER BY created DESC",
        
        # With LIMIT-like syntax
        f"project = {project} ORDER BY created DESC LIMIT 1",
        
        # Different project syntax
        f'project = "{project}"',
        f"project = '{project}'",
        
        # More complex queries
        f"project = {project} AND status != Closed",
        f"project = {project} AND created >= -30d",
        f"project = {project} AND assignee is not EMPTY",
        
        # Alternative syntax
        f"project.key = {project}",
        f"Project = {project}",
        f"PROJECT = {project}",
        
        # Very simple queries
        f"key in ({sample_key}, {project}-2)",
        f"project = {project} AND key = {sample_key}",
    ]


async def main():
    """Main test function."""
    print("🚀 JQL Validation Test Harness")
    print("=" * 50)
    
    tester = JQLValidationTester()
    
    # Test against all instances with appropriate project names
    instances_to_test = ['personal', 'highspring', 'trilliant']
    
    all_results = {}
    all_patterns = {}
    
    for instance in instances_to_test:
        print(f"\n🎯 Testing instance: {instance}")
        print("-" * 30)
        
        try:
            # Generate instance-specific test patterns
            test_patterns = generate_test_patterns_for_instance(instance)
            all_patterns[instance] = test_patterns
            
            print(f"📋 Using {len(test_patterns)} patterns for {instance} instance")
            
            results = await tester.test_jql_patterns(instance, test_patterns)
            all_results[instance] = results
            tester.print_results_summary(results)
            
        except Exception as e:
            logger.error(f"❌ Failed to test instance {instance}: {str(e)}")
            print(f"❌ Failed to test instance {instance}: {str(e)}")
    
    # Print comparative summary using pattern templates
    print(f"\n🔍 Comparative Analysis")
    print("=" * 50)
    
    # Create pattern templates for comparison
    pattern_templates = [
        "key = {sample_key}",
        "project = {project}",
        "project in ({project})",
        "project = {project} ORDER BY key",
        "project = {project} ORDER BY created DESC",
        "project in ({project}) ORDER BY key",
        "project in ({project}) ORDER BY created DESC",
        'project = "{project}"',
        "project = '{project}'",
        "project = {project} AND status != Closed",
        "project = {project} AND created >= -30d",
        "project = {project} AND assignee is not EMPTY",
        "project.key = {project}",
        "Project = {project}",
        "PROJECT = {project}",
        "key in ({sample_key}, {project}-2)",
        "project = {project} AND key = {sample_key}",
    ]
    
    for template in pattern_templates:
        print(f"\nPattern Template: {template}")
        for instance in instances_to_test:
            if instance in all_results and instance in all_patterns:
                # Find the actual pattern for this instance
                instance_patterns = all_patterns[instance]
                # Match by position in the list (they're generated in the same order)
                try:
                    pattern_index = pattern_templates.index(template)
                    if pattern_index < len(instance_patterns):
                        actual_pattern = instance_patterns[pattern_index]
                        result = next((r for r in all_results[instance]['results'] if r['jql'] == actual_pattern), None)
                        if result:
                            status = "✅" if result['success'] else "❌"
                            time_info = f"({result['total_time']:.2f}s)"
                            error_info = f" - {result['error'][:50]}..." if result['error'] else ""
                            print(f"   {instance:12}: {status} {time_info}{error_info}")
                        else:
                            print(f"   {instance:12}: ❓ No result found")
                    else:
                        print(f"   {instance:12}: ❓ Pattern not tested")
                except ValueError:
                    print(f"   {instance:12}: ❓ Template not found")
    
    print(f"\n📁 Detailed logs written to: /tmp/jql_validation_test.log")
    print("🎉 JQL Validation Test Complete!")


if __name__ == "__main__":
    asyncio.run(main())
