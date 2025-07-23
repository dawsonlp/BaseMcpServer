#!/usr/bin/env python3
"""
Direct test of the time validator to see what's happening.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_validator_directly():
    """Test the validator directly to see what it returns."""
    print("🧪 Testing AtlassianTimeFormatValidator directly...")
    
    try:
        from infrastructure.atlassian_time_adapter import AtlassianTimeFormatValidator
        
        validator = AtlassianTimeFormatValidator()
        
        test_cases = [
            "2h",
            "30m", 
            "1d",
            "1w",
            "2h 30m",
            "1d 4h",
            "invalid",
            "",
            None
        ]
        
        for test_case in test_cases:
            print(f"\n🔍 Testing: {test_case!r}")
            try:
                result = validator.validate_time_format(test_case)
                print(f"   Result: {result!r} (type: {type(result)})")
                print(f"   Bool value: {bool(result)}")
                
                if result is True:
                    print("   🚨 FOUND THE BUG! Validator returned True (boolean)")
                elif result is False:
                    print("   🚨 FOUND THE BUG! Validator returned False (boolean)")
                elif not isinstance(result, (list, tuple)):
                    print(f"   🚨 FOUND THE BUG! Validator returned non-list type: {type(result)}")
                elif isinstance(result, list) and len(result) == 0:
                    print("   ✅ GOOD: Empty list (valid format)")
                elif isinstance(result, list) and len(result) > 0:
                    print("   ✅ GOOD: List with errors (invalid format)")
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test validator: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_validator_directly()
    sys.exit(0 if success else 1)
