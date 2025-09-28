# Building a New MCP Server: A Complete Guide

This guide teaches you how to build production-ready MCP (Model Context Protocol) servers using two proven architectural approaches from our existing servers.

## Choose Your Architecture

### 🚀 Simple Approach (Recommended for Most Cases)
**Based on `worldcontext` server** - Uses mcp-commons framework for rapid development with minimal boilerplate.

**Best for:**
- Simple tools and utilities
- Rapid prototyping
- Servers with straightforward business logic
- Getting started with MCP development

### 🏗️ Hexagonal Architecture Approach
**Based on `jira-helper` server** - Full domain-driven design with extensive separation of concerns.

**Best for:**
- Complex business logic
- External API integrations
- Long-term maintainability
- Enterprise applications

## Table of Contents

### Simple Approach
1. [Simple Architecture Overview](#simple-architecture-overview)
2. [Simple Project Setup](#simple-project-setup)
3. [Creating Tools with mcp-commons](#creating-tools-with-mcp-commons)
4. [Simple Configuration](#simple-configuration)
5. [Testing Simple Servers](#testing-simple-servers)

### Hexagonal Architecture Approach
6. [Hexagonal Architecture Overview](#hexagonal-architecture-overview)
7. [Hexagonal Project Setup](#hexagonal-project-setup)
8. [Implementing the Domain Layer](#implementing-the-domain-layer)
9. [Building the Infrastructure Layer](#building-the-infrastructure-layer)
10. [Creating the Application Layer](#creating-the-application-layer)
11. [Implementing the MCP Adapter](#implementing-the-mcp-adapter)
12. [Hexagonal Configuration Management](#hexagonal-configuration-management)
13. [Testing Hexagonal Servers](#testing-hexagonal-servers)

### Both Approaches
14. [Adding Tools to Existing Servers](#adding-tools-to-existing-servers)
15. [Best Practices](#best-practices)
16. [Integration with mcp-manager](#integration-with-mcp-manager)
17. [Deployment and Maintenance](#deployment-and-maintenance)

---

# Simple Approach (Recommended)

## Simple Architecture Overview

The simple approach uses the `mcp-commons` framework to minimize boilerplate and accelerate development. This pattern is used by the `worldcontext` server.

```
simple-server/
├── pyproject.toml              # Package configuration
├── config.yaml.example        # Configuration template  
├── src/
│   ├── main.py                # Entry point using mcp-commons
│   ├── config.py              # Simple configuration
│   └── tool_config.py         # All tools defined here
└── tests/
    └── test_tools.py          # Tool tests
```

**Key Benefits:**
- **Fast Development**: Minimal setup, focus on tool logic
- **Low Boilerplate**: mcp-commons handles MCP protocol details
- **Easy Testing**: Direct function testing
- **Simple Maintenance**: All tools in one configuration file

## Simple Project Setup

### 1. Create Project Structure

```bash
mkdir hello-simple-mcp
cd hello-simple-mcp

mkdir -p src tests
touch src/{main.py,config.py,tool_config.py}
touch pyproject.toml config.yaml.example
touch tests/test_tools.py
```

### 2. Package Configuration

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "hello-simple-mcp"
version = "1.0.0"
description = "Simple Hello World MCP server"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "mcp>=1.15.0",
    "mcp-commons>=1.0.0",
    "pyyaml>=6.0.2"
]
requires-python = ">=3.11"

[project.scripts]
hello-simple-mcp = "main:main"

[tool.setuptools]
packages = ["hello-simple-mcp"]
package-dir = {"hello-simple-mcp" = "src"}
```

## Creating Tools with mcp-commons

### 1. Configuration System

Create `src/config.py`:

```python
"""Simple configuration for Hello Simple MCP Server."""

from typing import Dict, Any


class SimpleConfig:
    """Simple configuration class."""
    
    def __init__(self):
        self._config = {
            "server": {
                "name": "hello-simple-mcp",
                "host": "localhost", 
                "port": 7501
            },
            "greeting": {
                "default_style": "casual"
            }
        }
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(section, {}).get(key, default)


# Global config instance
config = SimpleConfig()
```

### 2. Tool Implementation

Create `src/tool_config.py`:

```python
"""
Tool Configuration for Hello Simple MCP Server

All tools are defined here using simple functions that return dictionaries.
The mcp-commons framework handles all MCP protocol details automatically.
"""

from typing import Dict, Any
import datetime
from config import config

def say_hello(name: str, style: str = "casual") -> Dict[str, Any]:
    """Generate a personalized greeting for someone.
    
    Args:
        name: The name of the person to greet
        style: The style of greeting (formal, casual, enthusiastic)
    """
    # Validate inputs
    if not name or not isinstance(name, str):
        return {"error": "Name must be a non-empty string", "success": False}
    
    name = name.strip()
    if not name:
        return {"error": "Name cannot be empty", "success": False}
    
    # Greeting templates
    templates = {
        "formal": "Good day, {name}. I hope this message finds you well.",
        "casual": "Hey {name}! How's it going?",
        "enthusiastic": "Hello there, {name}! Great to see you! 🎉"
    }
    
    # Get template (default to casual if invalid style)
    template = templates.get(style.lower(), templates["casual"])
    message = template.format(name=name)
    
    return {
        "greeting": message,
        "recipient": name,
        "style": style,
        "timestamp": datetime.datetime.now().isoformat(),
        "success": True
    }

def get_greeting_styles() -> Dict[str, Any]:
    """Get all available greeting styles and their descriptions."""
    styles = {
        "formal": {
            "name": "Formal",
            "description": "Professional and respectful greetings",
            "example": "Good day, John. I hope this message finds you well."
        },
        "casual": {
            "name": "Casual", 
            "description": "Friendly and relaxed greetings",
            "example": "Hey John! How's it going?"
        },
        "enthusiastic": {
            "name": "Enthusiastic",
            "description": "Energetic and excited greetings",
            "example": "Hello there, John! Great to see you! 🎉"
        }
    }
    
    return {
        "available_styles": styles,
        "default_style": config.get("greeting", "default_style", "casual"),
        "total_styles": len(styles)
    }

# Tool configuration - single source of truth
HELLO_SIMPLE_TOOLS: Dict[str, Dict[str, Any]] = {
    'say_hello': {
        'function': say_hello,
        'description': 'Generate a personalized greeting for someone with customizable style (formal, casual, enthusiastic)'
    },
    
    'get_greeting_styles': {
        'function': get_greeting_styles,  
        'description': 'Get all available greeting styles with descriptions and examples'
    }
}

def get_tools_config() -> Dict[str, Dict[str, Any]]:
    """Get the tools configuration for mcp-commons registration."""
    return HELLO_SIMPLE_TOOLS

def get_tool_names() -> list[str]:
    """Get list of all tool names."""
    return list(HELLO_SIMPLE_TOOLS.keys())

def get_tool_count() -> int:
    """Get the total number of configured tools."""
    return len(HELLO_SIMPLE_TOOLS)
```

### 3. Main Entry Point

Create `src/main.py`:

```python
"""
Main entry point for the Hello Simple MCP Server.

Uses mcp-commons for standardized server startup with minimal boilerplate.
"""

import sys
from mcp_commons import run_mcp_server, create_mcp_app, print_mcp_help

from config import config
from tool_config import get_tools_config

def main() -> None:
    """Process command-line arguments and start the server appropriately."""
    if len(sys.argv) <= 1 or sys.argv[1] in ["help", "--help", "-h"]:
        print_mcp_help("Hello Simple MCP", "- Simple greeting server")
        return
    
    # Get config values
    server_name = config.get("server", "name", default="hello-simple-mcp")
    host = config.get("server", "host", default="localhost")
    port = config.get("server", "port", default=7501)
    
    if sys.argv[1] == "sse":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="sse",
            host=host,
            port=port
        )
    elif sys.argv[1] == "stdio":
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="stdio"
        )
    else:
        print(f"Unknown transport mode: {sys.argv[1]}")
        print("Use 'sse', 'stdio', or 'help' for usage information.")
        sys.exit(1)

def create_app():
    """Create an ASGI application for use with an external ASGI server."""
    server_name = config.get("server", "name", default="hello-simple-mcp")
    
    return create_mcp_app(
        server_name=server_name,
        tools_config=get_tools_config()
    )

if __name__ == "__main__":
    main()
```

## Simple Configuration

Create `config.yaml.example`:

```yaml
# Hello Simple MCP Server Configuration

# Server settings
server:
  name: "hello-simple-mcp"
  host: "localhost"
  port: 7501

# Greeting settings
greeting:
  default_style: "casual"
```

## Testing Simple Servers

Create `tests/test_tools.py`:

```python
import pytest
from src.tool_config import say_hello, get_greeting_styles

def test_say_hello_casual():
    result = say_hello("Alice", "casual")
    
    assert result["success"] is True
    assert result["recipient"] == "Alice"
    assert result["style"] == "casual"
    assert "Alice" in result["greeting"]

def test_say_hello_formal():
    result = say_hello("Bob", "formal")
    
    assert result["success"] is True
    assert result["style"] == "formal"
    assert "Good day, Bob" in result["greeting"]

def test_say_hello_empty_name():
    result = say_hello("", "casual")
    
    assert result["success"] is False
    assert "error" in result

def test_get_greeting_styles():
    result = get_greeting_styles()
    
    assert "available_styles" in result
    assert len(result["available_styles"]) == 3
    assert "formal" in result["available_styles"]
    assert "casual" in result["available_styles"]
    assert "enthusiastic" in result["available_styles"]
```

---

# Hexagonal Architecture Approach

## Hexagonal Architecture Overview

## Architecture Overview

We'll build a "Hello World" MCP server that demonstrates all three MCP capabilities:
- **Tool**: `say_hello` - Takes a name and returns a personalized greeting
- **Prompt**: `greeting_template` - Provides greeting templates for different occasions
- **Resource**: `greetings.txt` - A static resource with greeting examples

### Architectural Patterns from jira-helper

The jira-helper server uses **Hexagonal Architecture** (Ports and Adapters) with **Domain-Driven Design**:

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Adapter Layer                        │
│  (Handles MCP protocol - tools, prompts, resources)        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                 Application Layer                           │
│     (Use cases, validation, orchestration)                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   Domain Layer                              │
│  (Business logic, models, services - framework agnostic)   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Infrastructure Layer                         │
│    (External services, file system, databases)             │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefits:**
- **Testable**: Business logic is isolated from frameworks
- **Maintainable**: Clear separation of concerns
- **Extensible**: Easy to add new features or change external dependencies
- **Framework-agnostic**: Core logic doesn't depend on MCP or any specific framework

## 🚫 ABSOLUTE IMPORT REQUIREMENT

**RELATIVE IMPORTS ARE COMPLETELY BANNED** - There is no valid use case for relative imports in MCP servers. They will break when installed with pipx and cause "attempted relative import beyond top-level package" errors.

**✅ ALWAYS USE:** `from domain.models import SomeModel`  
**❌ NEVER USE:** `from .models import SomeModel` or `from ..domain.models import SomeModel`

This rule applies to ALL imports across ALL layers of your MCP server. No exceptions.

## Project Setup

### 1. Create Project Structure

Create a new directory for your MCP server:

```
hello-world-mcp/
├── pyproject.toml              # Package configuration for pipx
├── config.yaml.example        # Configuration template
├── src/                        # Source code (src/ layout)
│   ├── main.py                # Entry point and CLI
│   ├── config.py              # Configuration management
│   ├── domain/                # Business logic (framework-agnostic)
│   │   ├── __init__.py
│   │   ├── models.py          # Domain models
│   │   ├── services.py        # Business logic
│   │   └── results.py         # Result types for error handling
│   ├── application/           # Use cases and validation
│   │   ├── __init__.py
│   │   ├── use_cases.py       # Application use cases
│   │   └── validation.py      # Input validation
│   ├── infrastructure/        # External services
│   │   ├── __init__.py
│   │   ├── file_adapter.py    # File system operations
│   │   └── config_adapter.py  # Configuration loading
│   └── adapters/              # Framework adapters
│       ├── __init__.py
│       └── mcp_adapter.py     # MCP protocol implementation
├── resources/                  # Static resources
│   └── greetings.txt          # Example resource file
└── tests/                     # Test files
    └── test_domain.py         # Domain tests
```

### 2. Package Configuration

Create `pyproject.toml` for pipx compatibility:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "hello-world-mcp"
version = "1.0.0"
description = "Hello World MCP server demonstrating tools, prompts, and resources"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "mcp>=1.15.0",
    "pydantic>=2.15.0",
    "pyyaml>=6.0.2"
]
requires-python = ">=3.11"

[project.scripts]
hello-world-mcp = "main:app"

[tool.setuptools]
packages = ["domain", "application", "infrastructure", "adapters"]
package-dir = {"" = "src"}
```

### 3. Install Dependencies

Use `uv pip` for fast dependency installation:

```bash
# Install dependencies for development
uv pip install -e .

# Or install specific dependencies
uv pip install "mcp>=1.15.0" "pydantic>=2.15.0" "pyyaml>=6.0.2"
```

## Implementing the Domain Layer

### 1. Result Types for Error Handling

Create `src/domain/results.py`:

```python
from typing import TypeVar, Generic, Optional
from dataclasses import dataclass
from enum import Enum

T = TypeVar('T')

class ErrorType(Enum):
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND_ERROR = "not_found_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class Error:
    type: ErrorType
    message: str
    details: Optional[dict] = None

@dataclass
class Result(Generic[T]):
    """Result type for operations that can succeed or fail."""
    success: bool
    data: Optional[T] = None
    error: Optional[Error] = None
    
    @classmethod
    def ok(cls, data: T) -> 'Result[T]':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: Error) -> 'Result[T]':
        return cls(success=False, error=error)
```

### 2. Domain Models

Create `src/domain/models.py`:

```python
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
```

### 3. Domain Services

Create `src/domain/services.py`:

```python
from typing import List
from domain.models import Greeting, GreetingTemplate, GreetingStyle
from domain.results import Result, Error, ErrorType

class GreetingService:
    """Core business logic for greetings."""
    
    def __init__(self):
        self.templates = {
            GreetingStyle.FORMAL: "Good day, {name}. I hope this message finds you well.",
            GreetingStyle.CASUAL: "Hey {name}! How's it going?",
            GreetingStyle.ENTHUSIASTIC: "Hello there, {name}! Great to see you! 🎉"
        }
    
    def create_greeting(self, name: str, style: GreetingStyle = GreetingStyle.CASUAL) -> Result[Greeting]:
        """Create a personalized greeting."""
        if not name or not name.strip():
            return Result.fail(Error(
                type=ErrorType.VALIDATION_ERROR,
                message="Name cannot be empty"
            ))
        
        name = name.strip()
        template = self.templates.get(style, self.templates[GreetingStyle.CASUAL])
        message = template.format(name=name)
        
        greeting = Greeting(
            message=message,
            style=style,
            recipient=name
        )
        
        return Result.ok(greeting)
    
    def get_available_templates(self) -> List[GreetingTemplate]:
        """Get all available greeting templates."""
        templates = []
        
        for style, template in self.templates.items():
            templates.append(GreetingTemplate(
                name=f"{style.value}_greeting",
                template=template,
                style=style,
                description=f"A {style.value} greeting template",
                variables=["name"]
            ))
        
        return templates
    
    def validate_greeting_style(self, style_str: str) -> Result[GreetingStyle]:
        """Validate and convert string to GreetingStyle."""
        try:
            return Result.ok(GreetingStyle(style_str.lower()))
        except ValueError:
            valid_styles = [style.value for style in GreetingStyle]
            return Result.fail(Error(
                type=ErrorType.VALIDATION_ERROR,
                message=f"Invalid style '{style_str}'. Valid styles: {', '.join(valid_styles)}"
            ))
```

## Building the Infrastructure Layer

### 1. File System Adapter

Create `src/infrastructure/file_adapter.py`:

```python
from pathlib import Path
from typing import List
from domain.results import Result, Error, ErrorType

class FileAdapter:
    """Adapter for file system operations."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    def read_text_file(self, filename: str) -> Result[str]:
        """Read a text file and return its contents."""
        try:
            file_path = self.base_path / filename
            if not file_path.exists():
                return Result.fail(Error(
                    type=ErrorType.NOT_FOUND_ERROR,
                    message=f"File not found: {filename}"
                ))
            
            content = file_path.read_text(encoding='utf-8')
            return Result.ok(content)
            
        except Exception as e:
            return Result.fail(Error(
                type=ErrorType.UNKNOWN_ERROR,
                message=f"Failed to read file {filename}: {str(e)}"
            ))
    
    def list_files(self, pattern: str = "*") -> Result[List[str]]:
        """List files matching a pattern."""
        try:
            if not self.base_path.exists():
                return Result.ok([])
            
            files = [f.name for f in self.base_path.glob(pattern) if f.is_file()]
            return Result.ok(files)
            
        except Exception as e:
            return Result.fail(Error(
                type=ErrorType.UNKNOWN_ERROR,
                message=f"Failed to list files: {str(e)}"
            ))
```

### 2. Configuration Adapter

Create `src/infrastructure/config_adapter.py`:

```python
import yaml
from pathlib import Path
from typing import Dict, Any
from domain.models import ServerConfig, GreetingStyle
from domain.results import Result, Error, ErrorType

class ConfigAdapter:
    """Adapter for configuration management."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
    
    def load_config(self) -> Result[ServerConfig]:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                # Return default configuration
                return Result.ok(ServerConfig(
                    name="hello-world-mcp",
                    version="1.0.0",
                    greetings_file="greetings.txt",
                    default_style=GreetingStyle.CASUAL
                ))
            
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            return Result.ok(ServerConfig(
                name=config_data.get("name", "hello-world-mcp"),
                version=config_data.get("version", "1.0.0"),
                greetings_file=config_data.get("greetings_file", "greetings.txt"),
                default_style=GreetingStyle(config_data.get("default_style", "casual"))
            ))
            
        except Exception as e:
            return Result.fail(Error(
                type=ErrorType.UNKNOWN_ERROR,
                message=f"Failed to load configuration: {str(e)}"
            ))
```

## Creating the Application Layer

### 1. Input Validation

Create `src/application/validation.py`:

```python
from typing import Dict, Any
from domain.results import Result, Error, ErrorType

def validate_say_hello_input(arguments: Dict[str, Any]) -> Result[None]:
    """Validate input for the say_hello tool."""
    if "name" not in arguments:
        return Result.fail(Error(
            type=ErrorType.VALIDATION_ERROR,
            message="Missing required parameter: name"
        ))
    
    name = arguments["name"]
    if not isinstance(name, str):
        return Result.fail(Error(
            type=ErrorType.VALIDATION_ERROR,
            message="Name must be a string"
        ))
    
    if not name.strip():
        return Result.fail(Error(
            type=ErrorType.VALIDATION_ERROR,
            message="Name cannot be empty"
        ))
    
    if len(name.strip()) > 100:
        return Result.fail(Error(
            type=ErrorType.VALIDATION_ERROR,
            message="Name must be 100 characters or less"
        ))
    
    return Result.ok(None)
```

### 2. Use Cases

Create `src/application/use_cases.py`:

```python
from typing import Dict, Any
from domain.services import GreetingService
from domain.models import GreetingStyle
from domain.results import Result
from application.validation import validate_say_hello_input

class SayHelloUseCase:
    """Use case for saying hello to someone."""
    
    def __init__(self, greeting_service: GreetingService):
        self.greeting_service = greeting_service
    
    async def execute(self, arguments: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """Execute the say hello use case."""
        # Validate input
        validation_result = validate_say_hello_input(arguments)
        if not validation_result.success:
            return validation_result
        
        # Extract parameters
        name = arguments["name"].strip()
        style_str = arguments.get("style", "casual")
        
        # Validate style
        style_result = self.greeting_service.validate_greeting_style(style_str)
        if not style_result.success:
            return style_result
        
        # Create greeting
        greeting_result = self.greeting_service.create_greeting(name, style_result.data)
        if not greeting_result.success:
            return greeting_result
        
        # Return formatted response
        greeting = greeting_result.data
        response = {
            "greeting": greeting.message,
            "recipient": greeting.recipient,
            "style": greeting.style.value,
            "success": True
        }
        
        return Result.ok(response)
```

## Implementing the MCP Adapter

### 1. Main Entry Point

Create `src/main.py`:

```python
#!/usr/bin/env python3
"""
Hello World MCP Server

A simple MCP server demonstrating tools, prompts, and resources.
"""

import logging
import sys
from pathlib import Path
import typer

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from adapters.mcp_adapter import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def main(transport: str = typer.Argument("stdio", help="The transport to use (stdio or sse)")):
    """Main entry point for the Hello World MCP server."""
    try:
        logger.info(f"Starting Hello World MCP server with transport: {transport}")
        # The mcp object will be configured to use the specified transport
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    app()
```

### 2. MCP Protocol Implementation with FastMCP

Create `src/adapters/mcp_adapter.py`:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict
import json

from mcp.server.fastmcp import FastMCP

# Import our application layers
from domain.services import GreetingService
from application.use_cases import SayHelloUseCase
from infrastructure.file_adapter import FileAdapter
from infrastructure.config_adapter import ConfigAdapter


class HelloWorldContext:
    """Context object containing all initialized services."""

    def __init__(
        self,
        greeting_service: GreetingService,
        say_hello_use_case: SayHelloUseCase,
        file_adapter: FileAdapter,
        config_adapter: ConfigAdapter,
    ):
        self.greeting_service = greeting_service
        self.say_hello_use_case = say_hello_use_case
        self.file_adapter = file_adapter
        self.config_adapter = config_adapter


@asynccontextmanager
async def hello_world_lifespan(server: FastMCP) -> AsyncIterator[HelloWorldContext]:
    """Manage application lifecycle with dependency injection."""
    
    # Initialize services
    greeting_service = GreetingService()
    say_hello_use_case = SayHelloUseCase(greeting_service)
    
    # Initialize infrastructure
    current_dir = Path(__file__).parent.parent.parent
    resources_dir = current_dir / "resources"
    file_adapter = FileAdapter(resources_dir)
    config_adapter = ConfigAdapter(current_dir / "config.yaml")
    
    # Create context
    context = HelloWorldContext(
        greeting_service=greeting_service,
        say_hello_use_case=say_hello_use_case,
        file_adapter=file_adapter,
        config_adapter=config_adapter,
    )
    
    # Register tools with the server
    register_tools(server, context)
    
    yield context


def register_tools(server: FastMCP, context: HelloWorldContext):
    """Register all MCP tools with the server."""
    
    @server.tool()
    async def say_hello(name: str, style: str = "casual") -> Dict[str, Any]:
        """Generate a personalized greeting for someone.
        
        Args:
            name: The name of the person to greet
            style: The style of greeting (formal, casual, enthusiastic)
        """
        arguments = {"name": name, "style": style}
        result = await context.say_hello_use_case.execute(arguments)
        
        if result.success:
            return result.data
        else:
            return {"error": result.error.message, "success": False}
    
    @server.prompt()
    async def greeting_template(occasion: str = "general", style: str = "casual") -> str:
        """Generate greeting templates for different occasions.
        
        Args:
            occasion: The occasion for the greeting (e.g., 'meeting', 'email', 'birthday')
            style: The style of greeting (formal, casual, enthusiastic)
        """
        templates = context.greeting_service.get_available_templates()
        
        # Find template matching the requested style
        selected_template = None
        for template in templates:
            if template.style.value == style:
                selected_template = template
                break
        
        if not selected_template:
            selected_template = templates[0]  # Default to first template
        
        return f"""Here's a {selected_template.style.value} greeting template for {occasion}:

Template: {selected_template.template}
Variables: {', '.join(selected_template.variables)}
Style: {selected_template.style.value}
Description: {selected_template.description}

You can customize this template by replacing the variables with actual values.
For example, replace {{name}} with the person's actual name.
"""
    
    @server.resource("file://greetings.txt")
    async def greetings_resource() -> str:
        """A collection of greeting examples in different styles."""
        result = context.file_adapter.read_text_file("greetings.txt")
        
        if result.success:
            return result.data
        else:
            # Return default content if file doesn't exist
            return """# Greeting Examples

## Formal Greetings
- Good morning, [Name]. I hope this message finds you well.
- Dear [Name], I trust you are having a productive day.
- Greetings, [Name]. It's a pleasure to connect with you.

## Casual Greetings
- Hey [Name]! How's it going?
- Hi [Name], hope you're doing well!
- What's up, [Name]?

## Enthusiastic Greetings
- Hello there, [Name]! Great to see you! 🎉
- Hey [Name]! Fantastic to connect with you! ✨
- Hi [Name]! Hope you're having an amazing day! 🌟

## Tips
- Match the greeting style to the context and relationship
- Consider cultural differences when choosing greeting styles
- Personalize greetings when possible for better connection
"""


# Create the FastMCP server with lifespan management
mcp = FastMCP("Hello World MCP", lifespan=hello_world_lifespan)
```

## Configuration Management

### 1. Configuration Template

Create `config.yaml.example`:

```yaml
# Hello World MCP Server Configuration

# Server settings
name: "hello-world-mcp"
version: "1.0.0"

# Resource settings
greetings_file: "greetings.txt"

# Default greeting style (formal, casual, enthusiastic)
default_style: "casual"
```

### 2. Static Resource

Create `resources/greetings.txt`:

```txt
# Greeting Examples

## Formal Greetings
- Good morning, [Name]. I hope this message finds you well.
- Dear [Name], I trust you are having a productive day.
- Greetings, [Name]. It's a pleasure to connect with you.

## Casual Greetings
- Hey [Name]! How's it going?
- Hi [Name], hope you're doing well!
- What's up, [Name]?

## Enthusiastic Greetings
- Hello there, [Name]! Great to see you! 🎉
- Hey [Name]! Fantastic to connect with you! ✨
- Hi [Name]! Hope you're having an amazing day! 🌟

## Tips
- Match the greeting style to the context and relationship
- Consider cultural differences when choosing greeting styles
- Personalize greetings when possible for better connection
```

## Testing Your Server

### 1. Basic Domain Tests

Create `tests/test_domain.py`:

```python
import pytest
from domain.services import GreetingService
from domain.models import GreetingStyle

def test_greeting_service_creates_casual_greeting():
    service = GreetingService()
    result = service.create_greeting("Alice", GreetingStyle.CASUAL)
    
    assert result.success
    assert result.data.recipient == "Alice"
    assert result.data.style == GreetingStyle.CASUAL
    assert "Alice" in result.data.message

def test_greeting_service_validates_empty_name():
    service = GreetingService()
    result = service.create_greeting("", GreetingStyle.CASUAL)
    
    assert not result.success
    assert "empty" in result.error.message.lower()

def test_greeting_service_provides_templates():
    service = GreetingService()
    templates = service.get_available_templates()
    
    assert len(templates) == 3
    assert any(t.style == GreetingStyle.FORMAL for t in templates)
    assert any(t.style == GreetingStyle.CASUAL for t in templates)
    assert any(t.style == GreetingStyle.ENTHUSIASTIC for t in templates)
```

### 2. Manual Testing

Test your server manually:

```bash
# Install in development mode
pip install -e .

# Run the server
python src/main.py stdio

# Test with mcp-manager
mcp-manager install local hello-world-mcp --source . --pipx --force
mcp-manager configure vscode
```

## Integration with mcp-manager

### 1. Install Your Server

```bash
# Install mcp-manager if you haven't already
pipx install ./utils/mcp_manager

# Install your hello-world server
mcp-manager install local hello-world-mcp --source ./hello-world-mcp --pipx --force

# Configure for VSCode/Cline
mcp-manager configure vscode
```

### 2. Test in Cline

Once configured, you can test your server in Cline:

**Tool Usage:**
```
Use the say_hello tool with name "Alice" and style "enthusiastic"
```

**Prompt Usage:**
```
Use the greeting_template prompt for a "birthday" occasion with "formal" style
```

**Resource Access:**
```
Show me the greetings.txt resource
```

## Key Architectural Benefits

This architecture provides several advantages:

1. **Separation of Concerns**: Each layer has a clear responsibility
2. **Testability**: Business logic is isolated and easily testable
3. **Maintainability**: Changes to external dependencies don't affect core logic
4. **Extensibility**: Easy to add new tools, prompts, or resources
5. **Error Handling**: Consistent error handling throughout the application
6. **Type Safety**: Strong typing with Pydantic models and type hints

## Next Steps

To extend this server:

1. **Add More Tools**: Create new use cases and domain services
2. **Add External APIs**: Implement new infrastructure adapters
3. **Add Configuration**: Extend the configuration system
4. **Add Persistence**: Add database adapters to the infrastructure layer
5. **Add Authentication**: Implement security in the infrastructure layer

The hexagonal architecture makes all of these extensions straightforward while keeping your core business logic clean and testable.

---

# Adding Tools to Existing Servers

This section explains how to add new tools to existing MCP servers, covering both architectural approaches.

## Adding Tools to Simple Architecture Servers

### Example: Adding a Farewell Tool to worldcontext-style Server

**Step 1: Add the Tool Function**

In your `tool_config.py`, add the new tool function:

```python
def say_goodbye(name: str, style: str = "casual") -> Dict[str, Any]:
    """Generate a personalized farewell for someone.
    
    Args:
        name: The name of the person to bid farewell
        style: The style of farewell (formal, casual, enthusiastic)
    """
    # Validate inputs
    if not name or not isinstance(name, str):
        return {"error": "Name must be a non-empty string", "success": False}
    
    name = name.strip()
    if not name:
        return {"error": "Name cannot be empty", "success": False}
    
    # Farewell templates
    templates = {
        "formal": "Farewell, {name}. It has been a pleasure working with you.",
        "casual": "See you later, {name}! Take care!",
        "enthusiastic": "Goodbye, {name}! Thanks for everything! 🎉"
    }
    
    template = templates.get(style.lower(), templates["casual"])
    message = template.format(name=name)
    
    return {
        "farewell": message,
        "recipient": name,
        "style": style,
        "timestamp": datetime.datetime.now().isoformat(),
        "success": True
    }
```

**Step 2: Register the Tool**

Add to your `TOOLS` dictionary:

```python
HELLO_SIMPLE_TOOLS: Dict[str, Dict[str, Any]] = {
    'say_hello': {
        'function': say_hello,
        'description': 'Generate a personalized greeting for someone with customizable style'
    },
    
    'get_greeting_styles': {
        'function': get_greeting_styles,  
        'description': 'Get all available greeting styles with descriptions and examples'
    },
    
    # NEW TOOL
    'say_goodbye': {
        'function': say_goodbye,
        'description': 'Generate a personalized farewell for someone with customizable style (formal, casual, enthusiastic)'
    }
}
```

**Step 3: Test the New Tool**

Add tests for your new tool:

```python
def test_say_goodbye_casual():
    result = say_goodbye("Alice", "casual")
    
    assert result["success"] is True
    assert result["recipient"] == "Alice"
    assert result["style"] == "casual"
    assert "Alice" in result["farewell"]

def test_say_goodbye_formal():
    result = say_goodbye("Bob", "formal")
    
    assert result["success"] is True
    assert result["style"] == "formal"
    assert "Farewell, Bob" in result["farewell"]
```

**Step 4: Deploy**

```bash
# Reinstall the server with updated tools
mcp-manager install local your-server --source . --force

# Sync with Cline
mcp-manager config cline
```

## Adding Tools to Hexagonal Architecture Servers

### Example: Adding a Meeting Scheduler Tool to jira-helper-style Server

**Step 1: Extend Domain Models**

Add to `src/domain/models.py`:

```python
@dataclass
class Meeting:
    """Represents a meeting."""
    title: str
    participant: str
    duration_minutes: int
    style: GreetingStyle
    timestamp: Optional[str] = None

@dataclass
class MeetingInvitation:
    """Represents a meeting invitation."""
    meeting: Meeting
    invitation_message: str
    meeting_id: str
```

**Step 2: Extend Domain Services**

Add to `src/domain/services.py`:

```python
class MeetingService:
    """Business logic for meeting management."""
    
    def __init__(self, greeting_service: GreetingService):
        self.greeting_service = greeting_service
    
    def schedule_meeting(self, title: str, participant: str, 
                        duration: int, style: GreetingStyle) -> Result[MeetingInvitation]:
        """Schedule a meeting and generate invitation."""
        if not title or not title.strip():
            return Result.fail(Error(
                type=ErrorType.VALIDATION_ERROR,
                message="Meeting title cannot be empty"
            ))
        
        if duration < 15 or duration > 480:  # 15 min to 8 hours
            return Result.fail(Error(
                type=ErrorType.VALIDATION_ERROR,
                message="Meeting duration must be between 15 and 480 minutes"
            ))
        
        # Create meeting
        meeting = Meeting(
            title=title.strip(),
            participant=participant,
            duration_minutes=duration,
            style=style,
            timestamp=datetime.datetime.now().isoformat()
        )
        
        # Generate greeting for invitation
        greeting_result = self.greeting_service.create_greeting(participant, style)
        if not greeting_result.success:
            return greeting_result
        
        invitation_message = f"{greeting_result.data.message}\n\nI'd like to schedule a meeting with you:\n" \
                           f"Title: {title}\nDuration: {duration} minutes\n" \
                           f"Please let me know your availability."
        
        invitation = MeetingInvitation(
            meeting=meeting,
            invitation_message=invitation_message,
            meeting_id=f"mtg_{hash(title + participant)}"
        )
        
        return Result.ok(invitation)
```

**Step 3: Create Use Case**

Add to `src/application/use_cases.py`:

```python
class ScheduleMeetingUseCase:
    """Use case for scheduling meetings."""
    
    def __init__(self, meeting_service: MeetingService):
        self.meeting_service = meeting_service
    
    async def execute(self, arguments: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """Execute the schedule meeting use case."""
        # Validate required parameters
        required_params = ["title", "participant", "duration"]
        for param in required_params:
            if param not in arguments:
                return Result.fail(Error(
                    type=ErrorType.VALIDATION_ERROR,
                    message=f"Missing required parameter: {param}"
                ))
        
        # Extract and validate parameters
        title = arguments["title"]
        participant = arguments["participant"]
        duration = arguments["duration"]
        style_str = arguments.get("style", "casual")
        
        # Validate types
        if not isinstance(duration, int):
            return Result.fail(Error(
                type=ErrorType.VALIDATION_ERROR,
                message="Duration must be an integer (minutes)"
            ))
        
        # Convert style
        if isinstance(style_str, str):
            try:
                style = GreetingStyle(style_str.lower())
            except ValueError:
                style = GreetingStyle.CASUAL
        else:
            style = GreetingStyle.CASUAL
        
        # Schedule meeting
        result = self.meeting_service.schedule_meeting(title, participant, duration, style)
        if not result.success:
            return result
        
        # Format response
        invitation = result.data
        response = {
            "meeting_id": invitation.meeting_id,
            "title": invitation.meeting.title,
            "participant": invitation.meeting.participant,
            "duration_minutes": invitation.meeting.duration_minutes,
            "invitation_message": invitation.invitation_message,
            "scheduled_at": invitation.meeting.timestamp,
            "success": True
        }
        
        return Result.ok(response)
```

**Step 4: Update MCP Adapter**

Modify `src/adapters/mcp_adapter.py`:

```python
# Update the context class
class HelloWorldContext:
    def __init__(
        self,
        greeting_service: GreetingService,
        meeting_service: MeetingService,  # Add this
        say_hello_use_case: SayHelloUseCase,
        schedule_meeting_use_case: ScheduleMeetingUseCase,  # Add this
        file_adapter: FileAdapter,
        config_adapter: ConfigAdapter,
    ):
        self.greeting_service = greeting_service
        self.meeting_service = meeting_service  # Add this
        self.say_hello_use_case = say_hello_use_case
        self.schedule_meeting_use_case = schedule_meeting_use_case  # Add this
        self.file_adapter = file_adapter
        self.config_adapter = config_adapter

# Update the lifespan function
@asynccontextmanager
async def hello_world_lifespan(server: FastMCP) -> AsyncIterator[HelloWorldContext]:
    # Initialize services
    greeting_service = GreetingService()
    meeting_service = MeetingService(greeting_service)  # Add this
    say_hello_use_case = SayHelloUseCase(greeting_service)
    schedule_meeting_use_case = ScheduleMeetingUseCase(meeting_service)  # Add this
    
    # ... rest of initialization
    
    context = HelloWorldContext(
        greeting_service=greeting_service,
        meeting_service=meeting_service,  # Add this
        say_hello_use_case=say_hello_use_case,
        schedule_meeting_use_case=schedule_meeting_use_case,  # Add this
        file_adapter=file_adapter,
        config_adapter=config_adapter,
    )

# Add the new tool to register_tools function
def register_tools(server: FastMCP, context: HelloWorldContext):
    # ... existing tools ...
    
    @server.tool()
    async def schedule_meeting(title: str, participant: str, duration: int, style: str = "casual") -> Dict[str, Any]:
        """Schedule a meeting with someone and generate an invitation.
        
        Args:
            title: The title/subject of the meeting
            participant: The name of the person to meet with
            duration: Duration of the meeting in minutes (15-480)
            style: The invitation style (formal, casual, enthusiastic)
        """
        arguments = {
            "title": title,
            "participant": participant,
            "duration": duration,
            "style": style
        }
        result = await context.schedule_meeting_use_case.execute(arguments)
        
        if result.success:
            return result.data
        else:
            return {"error": result.error.message, "success": False}
```

**Step 5: Test the New Tool**

Add tests in `tests/test_domain.py`:

```python
def test_meeting_service_schedules_meeting():
    greeting_service = GreetingService()
    meeting_service = MeetingService(greeting_service)
    
    result = meeting_service.schedule_meeting("Project Review", "Alice", 60, GreetingStyle.FORMAL)
    
    assert result.success
    assert result.data.meeting.title == "Project Review"
    assert result.data.meeting.participant == "Alice"
    assert result.data.meeting.duration_minutes == 60
```

## Best Practices for Adding Tools

### 1. Planning Your Tool

**Before writing code, consider:**

- **Input Parameters**: What data does the tool need?
- **Validation**: What inputs are invalid? How will you handle them?
- **Business Logic**: What operations need to be performed?
- **Error Cases**: What can go wrong? How will you communicate errors?
- **Output Format**: What information should be returned?

### 2. Simple Architecture Guidelines

**✅ DO:**
- Keep tool functions pure (no side effects when possible)
- Use consistent error response format
- Validate all inputs thoroughly
- Return structured data with success indicators
- Add comprehensive tests for each tool

**❌ DON'T:**
- Mix business logic with MCP protocol concerns
- Skip input validation
- Return inconsistent response formats
- Forget to handle error cases
- Skip testing new tools

### 3. Hexagonal Architecture Guidelines

**✅ DO:**
- Place business logic in domain services
- Use the Result pattern for error handling
- Validate inputs in the application layer
- Keep use cases focused on single responsibilities
- Test each layer independently

**❌ DON'T:**
- Put business logic in MCP adapters
- Skip the domain layer for "simple" tools
- Use exceptions for business logic errors
- Mix concerns across layers
- Skip integration tests

### 4. Error Handling Best Practices

**Consistent Error Format:**

```python
# Simple Architecture
{
    "error": "Clear error message",
    "success": False,
    "details": {...}  # Optional additional context
}

# Hexagonal Architecture  
Result.fail(Error(
    type=ErrorType.VALIDATION_ERROR,
    message="Clear error message",
    details={"field": "value"}  # Optional context
))
```

### 5. Testing Your Tools

**Essential Tests:**
- **Happy Path**: Tool works with valid inputs
- **Validation**: Tool rejects invalid inputs gracefully
- **Edge Cases**: Boundary conditions, empty values, etc.
- **Error Handling**: Proper error responses
- **Integration**: Tool works within the MCP server

**Example Test Structure:**

```python
def test_tool_name_happy_path():
    """Test tool with valid inputs."""
    result = tool_function("valid", "inputs")
    assert result["success"] is True
    assert "expected_field" in result

def test_tool_name_validation():
    """Test tool validates inputs."""
    result = tool_function("", "invalid")
    assert result["success"] is False
    assert "error" in result

def test_tool_name_edge_cases():
    """Test tool handles edge cases."""
    result = tool_function("boundary", "case") 
    # Assert expected behavior
```

---

# Best Practices

## Architectural Decision Guidelines

### When to Choose Simple Architecture

**Choose Simple if:**
- Your server has < 10 tools
- Tools are mostly independent utility functions
- No complex business rules or workflows  
- Rapid prototyping or personal projects
- Team is new to MCP development
- Simple external API integrations

**Example Use Cases:**
- Utility servers (date/time, calculations)
- Simple API wrappers
- Personal productivity tools
- Quick prototypes

### When to Choose Hexagonal Architecture

**Choose Hexagonal if:**
- Your server has > 10 tools
- Complex business logic or workflows
- Multiple external integrations
- Enterprise or production systems
- Long-term maintenance requirements
- Team collaboration

**Example Use Cases:**
- Project management integrations (Jira, GitHub)
- Business process automation
- Multi-step workflows
- Data processing pipelines
- External API orchestration

## Code Quality Standards

### 1. Naming Conventions

**Functions and Variables:**
```python
# ✅ Clear, descriptive names
def create_user_greeting(name: str, style: GreetingStyle) -> Result[Greeting]:
    user_name = name.strip()
    
# ❌ Unclear abbreviations
def cr_usr_gr(n: str, s: GreetingStyle) -> Result[Greeting]:
    usr_n = n.strip()
```

**Classes and Models:**
```python
# ✅ Clear domain concepts
class GreetingService:
    def validate_greeting_style(self, style: str) -> Result[GreetingStyle]:

# ❌ Technical jargon without context
class GrHandler:
    def val_st(self, s: str) -> Result[GreetingStyle]:
```

### 2. Error Messages

**✅ Good Error Messages:**
```python
"Name cannot be empty"
"Invalid greeting style 'xyz'. Valid styles: formal, casual, enthusiastic"
"Meeting duration must be between 15 and 480 minutes"
```

**❌ Poor Error Messages:**
```python
"Invalid input"
"Error"
"Bad request"
```

### 3. Documentation Standards

**Tool Documentation:**
```python
def schedule_meeting(title: str, participant: str, duration: int) -> Dict[str, Any]:
    """Schedule a meeting with someone and generate an invitation.
    
    Creates a meeting invitation with personalized greeting and details.
    Validates input parameters and returns structured meeting data.
    
    Args:
        title: The meeting subject/title (required, non-empty)
        participant: Name of person to meet with (required, non-empty)
        duration: Meeting length in minutes (15-480 minutes)
        
    Returns:
        Dictionary containing:
        - meeting_id: Unique identifier for the meeting
        - invitation_message: Formatted invitation text
        - scheduled_at: ISO timestamp when meeting was created
        - success: Boolean indicating operation success
        
    Example:
        >>> schedule_meeting("Project Review", "Alice", 60)
        {
            "meeting_id": "mtg_12345",
            "invitation_message": "Hi Alice! I'd like to schedule...",
            "scheduled_at": "2023-10-01T14:30:00",
            "success": True
        }
    """
```

### 4. Configuration Management

**Environment-Specific Settings:**
```python
# ✅ Environment-aware configuration
class Config:
    def __init__(self):
        self.api_timeout = int(os.getenv("API_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

# ❌ Hard-coded values
class Config:
    def __init__(self):
        self.api_timeout = 30
        self.max_retries = 3
        self.debug_mode = True
```

### 5. Performance Considerations

**Async/Await for I/O Operations:**
```python
# ✅ Non-blocking I/O
async def fetch_user_data(user_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/users/{user_id}")
        return response.json()

# ✅ Concurrent operations when possible
async def fetch_multiple_users(user_ids: List[str]) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(f"/users/{uid}") for uid in user_ids]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

**Caching for Expensive Operations:**
```python
# ✅ Simple cache for repeated calls
from functools import lru_cache

@lru_cache(maxsize=100)
def get_greeting_templates() -> List[GreetingTemplate]:
    # Expensive operation
    return load_templates_from_file()
```

### 6. Security Considerations

**Input Sanitization:**
```python
# ✅ Validate and sanitize inputs
def create_greeting(name: str) -> Result[str]:
    if not isinstance(name, str):
        return Result.fail("Name must be a string")
    
    name = name.strip()[:100]  # Limit length
    if not name:
        return Result.fail("Name cannot be empty")
    
    # Remove potentially dangerous characters
    safe_name = re.sub(r'[<>"\'\{\}]', '', name)
    return Result.ok(safe_name)
```

**Secrets Management:**
```python
# ✅ Load secrets from environment
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")

# ❌ Hard-code secrets
API_KEY = "sk-1234567890abcdef"  # Never do this!
```

## Deployment Best Practices

### 1. Package Configuration

**Modern pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "your-mcp-server"
version = "1.0.0"
description = "Clear description of what your server does"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "mcp>=1.13.1",
    # Pin major versions, allow minor updates
    "httpx>=0.24.0,<1.0.0",
    "pydantic>=2.0.0,<3.0.0"
]
requires-python = ">=3.11"

[project.scripts]
your-mcp-server = "main:main"

[tool.setuptools]
packages = ["your_package"]
package-dir = {"your_package" = "src"}
```

### 2. Development Workflow

**Testing Before Deployment:**
```bash
# 1. Run unit tests
pytest tests/

# 2. Test installation with uv pip for faster installs
uv pip install -e .

# 3. Test MCP server manually
python -m your_mcp_server stdio

# 4. Install with mcp-manager
mcp-manager install local your-server --source . --force

# 5. Test in Cline
# Verify tools work as expected
```

### 3. Version Management

**Semantic Versioning:**
- `1.0.0`: Initial release
- `1.0.1`: Bug fixes
- `1.1.0`: New features (backward compatible)
- `2.0.0`: Breaking changes

**Change Tracking:**
```python
# Keep a CHANGELOG.md
## [1.1.0] - 2023-10-01
### Added
- New tool: schedule_meeting
- Support for meeting invitations

### Changed  
- Improved error messages for validation

### Fixed
- Handle empty names gracefully
```

## Maintenance and Monitoring

### 1. Logging Best Practices

```python
import logging
import sys

# Configure logging to stderr (not stdout - used for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

# Log important events
logger.info(f"Starting MCP server {server_name}")
logger.warning(f"Invalid input received: {invalid_input}")
logger.error(f"External API call failed: {error}")
```

### 2. Error Monitoring

```python
# Track error patterns
class ErrorMetrics:
    def __init__(self):
        self.error_counts = defaultdict(int)
    
    def record_error(self, error_type: str, tool_name: str):
        key = f"{tool_name}:{error_type}"
        self.error_counts[key] += 1
        
        # Log if errors are frequent
        if self.error_counts[key] % 10 == 0:
            logger.warning(f"Tool {tool_name} has {error_type} error #{self.error_counts[key]}")
```

### 3. Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            if duration > 5.0:  # Log slow operations
                logger.warning(f"{func.__name__} took {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Use on slow tools
@monitor_performance
async def complex_tool(data: str) -> Dict[str, Any]:
    # ... complex processing
```

This comprehensive guide should help you build, extend, and maintain high-quality MCP servers using both architectural approaches!
