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
