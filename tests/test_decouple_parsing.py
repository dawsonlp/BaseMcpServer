#!/usr/bin/env python3
"""
Test script to verify python-decouple can parse the multi-line JSON configuration
that was causing python-dotenv to fail.
"""

import json
import os
from decouple import config

def test_decouple_parsing():
    """Test that python-decouple can parse the problematic .env file."""
    
    print("Testing python-decouple parsing...")
    print("=" * 50)
    
    # Copy the backup .env file to current directory for testing
    os.system("cp /Users/ldawson/.mcp_servers/jira-helper-env-backup.env .env")
    
    try:
        # Test basic string values
        server_name = config('SERVER_NAME', default='not-found')
        api_key = config('API_KEY', default='not-found')
        debug_mode = config('DEBUG_MODE', default=False, cast=bool)
        
        print(f"✅ SERVER_NAME: {server_name}")
        print(f"✅ API_KEY: {api_key}")
        print(f"✅ DEBUG_MODE: {debug_mode}")
        
        # Test the critical multi-line JSON parsing
        jira_instances_json = config('JIRA_INSTANCES', default='[]')
        print(f"\n📄 Raw JIRA_INSTANCES length: {len(jira_instances_json)} characters")
        print(f"📄 First 100 chars: {repr(jira_instances_json[:100])}")
        
        # Try to parse the JSON
        instances_config = json.loads(jira_instances_json)
        print(f"\n✅ JSON parsing successful!")
        print(f"✅ Number of instances: {len(instances_config)}")
        
        # Display parsed instances
        for i, instance in enumerate(instances_config):
            print(f"\n🏢 Instance {i+1}:")
            print(f"   Name: {instance.get('name', 'N/A')}")
            print(f"   URL: {instance.get('url', 'N/A')}")
            print(f"   User: {instance.get('user', 'N/A')}")
            print(f"   Token: {'***' + instance.get('token', '')[-8:] if instance.get('token') else 'N/A'}")
            print(f"   Description: {instance.get('description', 'N/A')}")
        
        print(f"\n🎉 SUCCESS: python-decouple successfully parsed the multi-line JSON!")
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parsing failed: {e}")
        print(f"❌ Raw value: {repr(jira_instances_json)}")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    finally:
        # Clean up
        if os.path.exists('.env'):
            os.remove('.env')

if __name__ == "__main__":
    success = test_decouple_parsing()
    exit(0 if success else 1)
