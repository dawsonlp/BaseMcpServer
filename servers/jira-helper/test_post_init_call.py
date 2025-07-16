"""
Test when __post_init__ gets called by dataclass.
"""

from dataclasses import dataclass

print("Testing when __post_init__ gets called...")

# Test 1: Simple dataclass with __post_init__
@dataclass
class SimpleDataclass:
    name: str
    
    def __post_init__(self):
        print(f"SimpleDataclass.__post_init__ called with name='{self.name}'")
        if not self.name:
            raise ValueError("name cannot be empty")

print("\n1. Testing SimpleDataclass:")
try:
    simple = SimpleDataclass("")
    print(f"❌ SimpleDataclass should have failed but got: {simple}")
except Exception as e:
    print(f"✅ SimpleDataclass correctly rejected: {e}")

# Test 2: Dataclass with field that has default_factory
from dataclasses import field
from typing import List

@dataclass
class WithDefaultFactory:
    name: str
    items: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        print(f"WithDefaultFactory.__post_init__ called with name='{self.name}', items={self.items}")
        if not self.name:
            raise ValueError("name cannot be empty")

print("\n2. Testing WithDefaultFactory:")
try:
    with_default = WithDefaultFactory("")
    print(f"❌ WithDefaultFactory should have failed but got: {with_default}")
except Exception as e:
    print(f"✅ WithDefaultFactory correctly rejected: {e}")

# Test 3: Manually call __post_init__
@dataclass
class ManualCall:
    name: str
    
    def __post_init__(self):
        print(f"ManualCall.__post_init__ called with name='{self.name}'")
        if not self.name:
            raise ValueError("name cannot be empty")

print("\n3. Testing ManualCall:")
try:
    manual = ManualCall.__new__(ManualCall)
    manual.name = ""
    print(f"Before __post_init__: {manual}")
    manual.__post_init__()
    print(f"❌ ManualCall should have failed")
except Exception as e:
    print(f"✅ ManualCall correctly rejected: {e}")

# Test 4: Check if dataclass calls __post_init__ automatically
print("\n4. Testing automatic __post_init__ call:")
try:
    auto = ManualCall("")
    print(f"❌ Auto call should have failed but got: {auto}")
except Exception as e:
    print(f"✅ Auto call correctly rejected: {e}")
