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
