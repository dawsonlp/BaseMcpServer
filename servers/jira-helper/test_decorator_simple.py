"""
Simple test to verify decorator application.
"""

from dataclasses import dataclass
from src.domain.base import validate_required_fields

print("Testing decorator application...")

# Test without decorator
@dataclass
class SimpleClass:
    name: str
    
    def __post_init__(self):
        print(f"SimpleClass __post_init__ called with name='{self.name}'")

# Test with decorator
@validate_required_fields('name')
@dataclass
class DecoratedClass:
    name: str
    
    def __post_init__(self):
        print(f"DecoratedClass __post_init__ called with name='{self.name}'")

print("\n1. Testing SimpleClass:")
try:
    simple = SimpleClass("")
    print(f"SimpleClass created: {simple}")
except Exception as e:
    print(f"SimpleClass failed: {e}")

print("\n2. Testing DecoratedClass:")
try:
    decorated = DecoratedClass("")
    print(f"DecoratedClass created: {decorated}")
except Exception as e:
    print(f"DecoratedClass failed: {e}")

print("\n3. Testing DecoratedClass with None:")
try:
    decorated_none = DecoratedClass(None)
    print(f"DecoratedClass with None created: {decorated_none}")
except Exception as e:
    print(f"DecoratedClass with None failed: {e}")

print("\n4. Testing DecoratedClass with valid value:")
try:
    decorated_valid = DecoratedClass("valid")
    print(f"DecoratedClass with valid value created: {decorated_valid}")
except Exception as e:
    print(f"DecoratedClass with valid value failed: {e}")

# Check if __post_init__ was modified
print(f"\n5. DecoratedClass.__post_init__ = {DecoratedClass.__post_init__}")
print(f"   SimpleClass.__post_init__ = {SimpleClass.__post_init__}")
