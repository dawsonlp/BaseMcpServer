# Building a New MCP Server: A Complete Guide

This guide teaches you how to build production-ready MCP (Model Context Protocol) servers using proven architectural patterns from the `jira-helper` server, demonstrated through a simple "Hello World" example that includes tools, prompts, and resources.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Setup](#project-setup)
3. [Implementing the Domain Layer](#implementing-the-domain-layer)
4. [Building the Infrastructure Layer](#building-the-infrastructure-layer)
5. [Creating the Application Layer](#creating-the-application-layer)
6. [Implementing the MCP Adapter](#implementing-the-mcp-adapter)
7. [Configuration Management](#configuration-management)
8. [Testing Your Server](#testing-your-server)
9. [Integration with mcp-manager](#integration-with-mcp-manager)

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
├── requirements.txt            # Dependencies
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
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "typer>=0.9.0",
    "rich>=13.0.0"
]
requires-python = ">=3.11"

[project.scripts]
hello-world-mcp = "main:app"

[tool.setuptools]
packages = ["domain", "application", "infrastructure", "adapters"]
package-dir = {"" = "src"}
```

### 3. Dependencies

Create `requirements.txt`:

```txt
mcp>=1.12.1
pydantic>=2.11.7
pyyaml>=6.0
typer>=0.16.0
rich>=14.0.0
httpx>=0.28.1 
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

import asyncio
import sys
from pathlib import Path
import typer
from mcp.server.stdio import stdio_server

# Import our MCP server instance
from adapters.mcp_adapter import mcp

app = typer.Typer(help="Hello World MCP Server")

@app.command()
def main(
    transport: str = typer.Argument("stdio", help="Transport type (stdio or sse)")
):
    """Run the Hello World MCP server."""
    if transport == "stdio":
        # Run with stdio transport (for Cline/VSCode)
        asyncio.run(stdio_server())
    elif transport == "sse":
        # Run with SSE transport (for web/HTTP clients)
        from mcp.server.sse import sse_server
        asyncio.run(sse_server(host="0.0.0.0", port=8000))
    else:
        typer.echo(f"Unknown transport: {transport}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
```

### 2. MCP Protocol Implementation

Create `src/adapters/mcp_adapter.py`:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent, Prompt, PromptMessage, Resource
from typing import Any, Dict, List
import json
from pathlib import Path

# Import our application layers
from domain.services import GreetingService
from application.use_cases import SayHelloUseCase
from infrastructure.file_adapter import FileAdapter
from infrastructure.config_adapter import ConfigAdapter

# Create the MCP server instance
mcp = Server("hello-world-mcp")

# Initialize services
greeting_service = GreetingService()
say_hello_use_case = SayHelloUseCase(greeting_service)

# Initialize infrastructure
current_dir = Path(__file__).parent.parent.parent
resources_dir = current_dir / "resources"
file_adapter = FileAdapter(resources_dir)
config_adapter = ConfigAdapter(current_dir / "config.yaml")

@mcp.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="say_hello",
            description="Generate a personalized greeting for someone",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the person to greet"
                    },
                    "style": {
                        "type": "string",
                        "enum": ["formal", "casual", "enthusiastic"],
                        "description": "The style of greeting (default: casual)"
                    }
                },
                "required": ["name"]
            }
        )
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle MCP tool calls."""
    try:
        if name == "say_hello":
            result = await say_hello_use_case.execute(arguments)
            
            if result.success:
                return [TextContent(
                    type="text",
                    text=json.dumps(result.data, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: {result.error.message}"
                )]
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {str(e)}"
        )]

@mcp.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List all available prompts."""
    return [
        Prompt(
            name="greeting_template",
            description="Generate greeting templates for different occasions",
            arguments=[
                {
                    "name": "occasion",
                    "description": "The occasion for the greeting (e.g., 'meeting', 'email', 'birthday')",
                    "required": False
                },
                {
                    "name": "style",
                    "description": "The style of greeting (formal, casual, enthusiastic)",
                    "required": False
                }
            ]
        )
    ]

@mcp.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, Any]) -> PromptMessage:
    """Handle prompt requests."""
    if name == "greeting_template":
        occasion = arguments.get("occasion", "general")
        style = arguments.get("style", "casual")
        
        templates = greeting_service.get_available_templates()
        
        # Find template matching the requested style
        selected_template = None
        for template in templates:
            if template.style.value == style:
                selected_template = template
                break
        
        if not selected_template:
            selected_template = templates[0]  # Default to first template
        
        prompt_text = f"""Here's a {selected_template.style.value} greeting template for {occasion}:

Template: {selected_template.template}
Variables: {', '.join(selected_template.variables)}
Style: {selected_template.style.value}
Description: {selected_template.description}

You can customize this template by replacing the variables with actual values.
For example, replace {{name}} with the person's actual name.
"""
        
        return PromptMessage(
            role="user",
            content=TextContent(type="text", text=prompt_text)
        )
    else:
        return PromptMessage(
            role="user",
            content=TextContent(type="text", text=f"Unknown prompt: {name}")
        )

@mcp.list_resources()
async def list_resources() -> List[Resource]:
    """List all available resources."""
    return [
        Resource(
            uri="file://greetings.txt",
            name="Greeting Examples",
            description="A collection of greeting examples in different styles",
            mimeType="text/plain"
        )
    ]

@mcp.read_resource()
async def read_resource(uri: str) -> str:
    """Handle resource requests."""
    if uri == "file://greetings.txt":
        result = file_adapter.read_text_file("greetings.txt")
        
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
    else:
        return f"Unknown resource: {uri}"
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
from src.domain.services import GreetingService
from src.domain.models import GreetingStyle

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
