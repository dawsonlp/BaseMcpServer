from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class GreetingStyle(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"

@dataclass
class Greeting:
    """Represents a greeting message."""
    message: str
    style: GreetingStyle
    recipient: str
    timestamp: Optional[str] = None

@dataclass
class GreetingTemplate:
    """Represents a greeting template."""
    name: str
    template: str
    style: GreetingStyle
    description: str
    variables: List[str]

@dataclass
class ServerConfig:
    """Server configuration."""
    name: str
    version: str
    greetings_file: str
    default_style: GreetingStyle
