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
