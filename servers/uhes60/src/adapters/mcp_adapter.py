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


class UHES60Context:
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
async def uhes60_lifespan(server: FastMCP) -> AsyncIterator[UHES60Context]:
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
    context = UHES60Context(
        greeting_service=greeting_service,
        say_hello_use_case=say_hello_use_case,
        file_adapter=file_adapter,
        config_adapter=config_adapter,
    )
    
    # Register tools with the server
    register_tools(server, context)
    
    yield context


def register_tools(server: FastMCP, context: UHES60Context):
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
mcp = FastMCP("UHES60 MCP", lifespan=uhes60_lifespan)
