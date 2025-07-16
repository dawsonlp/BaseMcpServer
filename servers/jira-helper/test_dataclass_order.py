"""
Test the order of decorators with dataclass.
"""

from dataclasses import dataclass
from src.domain.base import validate_required_fields

print("Testing decorator order with dataclass...")

# Test 1: Decorator BEFORE @dataclass (current approach)
@validate_required_fields('name')
@dataclass
class BeforeDataclass:
    name: str

# Test 2: Decorator AFTER @dataclass 
@dataclass
class AfterDataclass:
    name: str

# Apply decorator after dataclass
AfterDataclass = validate_required_fields('name')(AfterDataclass)

print("\n1. Testing BeforeDataclass:")
try:
    before = BeforeDataclass("")
    print(f"❌ BeforeDataclass should have failed but got: {before}")
except Exception as e:
    print(f"✅ BeforeDataclass correctly rejected: {e}")

print("\n2. Testing AfterDataclass:")
try:
    after = AfterDataclass("")
    print(f"❌ AfterDataclass should have failed but got: {after}")
except Exception as e:
    print(f"✅ AfterDataclass correctly rejected: {e}")

# Test 3: Check what __post_init__ looks like
print(f"\n3. BeforeDataclass.__post_init__ = {BeforeDataclass.__post_init__}")
print(f"   AfterDataclass.__post_init__ = {AfterDataclass.__post_init__}")

# Test 4: Manual test of what dataclass does
@dataclass
class ManualTest:
    name: str
    
    def __post_init__(self):
        print(f"ManualTest __post_init__ called with name='{self.name}'")

print(f"\n4. ManualTest.__post_init__ = {ManualTest.__post_init__}")

manual = ManualTest("test")
print(f"   ManualTest created: {manual}")
