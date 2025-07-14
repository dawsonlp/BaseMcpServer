#!/usr/bin/env python3
"""
Simple test script to verify the health endpoint works.
Run this after starting the server to test the /health endpoint.
"""

import requests
import json
import sys
import time

def test_health_endpoint(host="localhost", port=7501, max_retries=5):
    """Test the health endpoint."""
    url = f"http://{host}:{port}/health"
    
    print(f"Testing health endpoint: {url}")
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}...")
            response = requests.get(url, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = response.json()
                    print(f"Response Body: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Response Body (raw): {response.text}")
            else:
                print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Health check passed!")
                return True
            elif response.status_code == 503:
                print("⚠️  Server is unhealthy (503) - check Jira connection")
                return False
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - server may not be running")
            if attempt < max_retries - 1:
                print("Waiting 2 seconds before retry...")
                time.sleep(2)
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        if attempt < max_retries - 1:
            print()
    
    print(f"❌ Health check failed after {max_retries} attempts")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 7501
        
    success = test_health_endpoint(port=port)
    sys.exit(0 if success else 1)
