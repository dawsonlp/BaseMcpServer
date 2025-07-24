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
