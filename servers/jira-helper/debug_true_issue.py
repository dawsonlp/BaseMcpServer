#!/usr/bin/env python3
"""
Debug script to isolate where True is being passed as expected_format.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_direct_error_creation():
    """Test creating InvalidTimeFormatError directly."""
    print("🧪 Testing InvalidTimeFormatError creation directly...")
    
    from domain.exceptions import InvalidTimeFormatError
    
    # Test with string (correct)
    try:
        error1 = InvalidTimeFormatError("30m", "Valid Jira time format")
        print(f"✅ String format: {error1}")
    except Exception as e:
        print(f"❌ String format failed: {e}")
    
    # Test with True (incorrect - this is the bug)
    try:
        error2 = InvalidTimeFormatError("30m", True)
        print(f"🎯 FOUND THE BUG! Boolean format: {error2}")
    except Exception as e:
        print(f"❌ Boolean format failed: {e}")
    
    # Test with empty list (might be the issue)
    try:
        error3 = InvalidTimeFormatError("30m", [])
        print(f"⚠️  Empty list format: {error3}")
    except Exception as e:
        print(f"❌ Empty list format failed: {e}")

def test_time_validation_chain():
    """Test the time validation chain to find where True comes from."""
    print("\n🔍 Testing time validation chain...")
    
    from infrastructure.atlassian_time_adapter import AtlassianTimeFormatValidator
    
    validator = AtlassianTimeFormatValidator()
    
    # Test the validator directly
    result = validator.validate_time_format('30m')
    print(f"✅ Validator result: {result} (type: {type(result)}, bool: {bool(result)})")
    
    # Test what happens when we convert the result
    if result:
        print(f"🎯 Result is truthy: {result}")
    else:
        print(f"✅ Result is falsy: {result}")
    
    # Test the boolean conversion
    bool_result = bool(result)
    print(f"Boolean conversion: {bool_result} (type: {type(bool_result)})")
    
    # This might be where the issue is - if somewhere we're passing bool(result) instead of result
    if bool_result:
        print("🎯 POTENTIAL BUG: bool(result) is True when result is truthy")
    else:
        print("✅ bool(result) is False for empty list")

def main():
    print("🚀 Starting debug to find where True is passed as expected_format...\n")
    
    test_direct_error_creation()
    test_time_validation_chain()
    
    print("\n🎉 Debug complete!")

if __name__ == "__main__":
    main()
