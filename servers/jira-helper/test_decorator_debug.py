"""
Debug why the decorator isn't working in our test.
"""

from dataclasses import dataclass
from src.domain.base import validate_required_fields

print("Debugging decorator application...")

# Test 1: Direct application like in our simple test
@validate_required_fields('name')
@dataclass
class DirectApplication:
    name: str

print("\n1. Testing DirectApplication:")
print(f"   __init__ = {DirectApplication.__init__}")
try:
    direct = DirectApplication("")
    print(f"❌ DirectApplication should have failed but got: {direct}")
except Exception as e:
    print(f"✅ DirectApplication correctly rejected: {e}")

# Test 2: Same as debug_decorators.py
@validate_required_fields('project_key', 'summary')
@dataclass
class TestRequest:
    project_key: str
    summary: str
    description: str = ""

print("\n2. Testing TestRequest:")
print(f"   __init__ = {TestRequest.__init__}")
try:
    test_req = TestRequest("", "Test")
    print(f"❌ TestRequest should have failed but got: {test_req}")
except Exception as e:
    print(f"✅ TestRequest correctly rejected: {e}")

# Test 3: Check if the issue is with multiple fields
@validate_required_fields('project_key')
@dataclass
class SingleField:
    project_key: str
    summary: str
    description: str = ""

print("\n3. Testing SingleField:")
print(f"   __init__ = {SingleField.__init__}")
try:
    single = SingleField("", "Test")
    print(f"❌ SingleField should have failed but got: {single}")
except Exception as e:
    print(f"✅ SingleField correctly rejected: {e}")

# Test 4: Check if the issue is with default values
@validate_required_fields('name')
@dataclass
class NoDefaults:
    name: str
    value: str

print("\n4. Testing NoDefaults:")
print(f"   __init__ = {NoDefaults.__init__}")
try:
    no_defaults = NoDefaults("", "test")
    print(f"❌ NoDefaults should have failed but got: {no_defaults}")
except Exception as e:
    print(f"✅ NoDefaults correctly rejected: {e}")

# Test 5: Manually inspect what the decorator does
print("\n5. Manual decorator inspection:")
print("Creating class without decorator...")

@dataclass
class BeforeDecorator:
    name: str

print(f"   Before: __init__ = {BeforeDecorator.__init__}")

print("Applying decorator...")
DecoratedClass = validate_required_fields('name')(BeforeDecorator)

print(f"   After: __init__ = {DecoratedClass.__init__}")

try:
    decorated = DecoratedClass("")
    print(f"❌ DecoratedClass should have failed but got: {decorated}")
except Exception as e:
    print(f"✅ DecoratedClass correctly rejected: {e}")
