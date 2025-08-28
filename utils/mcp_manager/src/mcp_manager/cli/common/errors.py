"""
Error handling framework for MCP Manager CLI.

This module provides comprehensive error handling, custom exceptions,
error reporting, and user-friendly error messages with suggested fixes.
"""

import sys
import traceback
from enum import Enum
from typing import Optional, Dict, Any, List, Union, Callable
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.traceback import Traceback

from mcp_manager.core.logging import MCPManagerLogger
from mcp_manager.cli.common.output import RichOutputManager, StatusIcon, OutputTheme


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PERMISSION = "permission"
    VALIDATION = "validation"
    PROCESS = "process"
    PLATFORM = "platform"
    INSTALLATION = "installation"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class MCPManagerError(Exception):
    """Base exception for MCP Manager errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        suggestions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        exit_code: int = 1
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.suggestions = suggestions or []
        self.details = details or {}
        self.exit_code = exit_code
        super().__init__(message)


class ConfigurationError(MCPManagerError):
    """Error related to configuration issues."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            **kwargs
        )


class ValidationError(MCPManagerError):
    """Error related to input validation."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )


class NetworkError(MCPManagerError):
    """Error related to network operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            **kwargs
        )


class PermissionError(MCPManagerError):
    """Error related to file/directory permissions."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.PERMISSION,
            **kwargs
        )


class ProcessError(MCPManagerError):
    """Error related to process management."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.PROCESS,
            **kwargs
        )


class PlatformError(MCPManagerError):
    """Error related to platform integration."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.PLATFORM,
            **kwargs
        )


class InstallationError(MCPManagerError):
    """Error related to server installation."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.INSTALLATION,
            **kwargs
        )


class ServerNotFoundError(MCPManagerError):
    """Error when a server cannot be found."""
    
    def __init__(self, server_name: str, **kwargs):
        message = f"Server '{server_name}' not found"
        suggestions = [
            f"Check server name spelling",
            f"List available servers with 'mcp-manager list'",
            f"Install server if it doesn't exist"
        ]
        super().__init__(
            message,
            category=ErrorCategory.USER_INPUT,
            suggestions=suggestions,
            details={"server_name": server_name},
            **kwargs
        )


class ErrorHandler:
    """Comprehensive error handler for the CLI."""
    
    def __init__(
        self,
        output_manager: Optional[RichOutputManager] = None,
        logger: Optional[MCPManagerLogger] = None,
        debug: bool = False
    ):
        self.output = output_manager or RichOutputManager()
        self.logger = logger or MCPManagerLogger()
        self.debug = debug
        self._error_suggestions = self._build_error_suggestions()
    
    def _build_error_suggestions(self) -> Dict[str, List[str]]:
        """Build a database of error patterns and suggested fixes."""
        return {
            # Configuration errors
            "config file not found": [
                "Run 'mcp-manager configure' to create initial configuration",
                "Check if the config file path is correct",
                "Verify file permissions"
            ],
            "invalid configuration": [
                "Run 'mcp-manager config validate' to check for errors",
                "Use 'mcp-manager configure' to fix configuration interactively",
                "Check configuration file syntax"
            ],
            "permission denied": [
                "Check file/directory permissions",
                "Run with appropriate privileges if necessary",
                "Verify ownership of files and directories"
            ],
            
            # Network errors
            "connection refused": [
                "Check if the server is running",
                "Verify the host and port configuration",
                "Check firewall settings"
            ],
            "timeout": [
                "Check network connectivity",
                "Increase timeout values if appropriate",
                "Verify server responsiveness"
            ],
            
            # Process errors
            "process not found": [
                "Check if the server process is actually running",
                "Verify process ID is correct",
                "Try restarting the server"
            ],
            "failed to start": [
                "Check server command and arguments",
                "Verify all dependencies are installed",
                "Check server logs for detailed error information"
            ],
            
            # Installation errors
            "command not found": [
                "Verify the command exists and is executable",
                "Check PATH environment variable",
                "Install required dependencies"
            ],
            "virtual environment": [
                "Ensure Python is properly installed",
                "Check virtual environment creation permissions",
                "Try recreating the virtual environment"
            ]
        }
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[str] = None,
        exit_on_error: bool = True
    ) -> None:
        """Handle an error with appropriate user messaging."""
        
        if isinstance(error, MCPManagerError):
            self._handle_mcp_manager_error(error, context)
        else:
            self._handle_generic_error(error, context)
        
        # Log the error
        self.logger.error(f"Error: {str(error)}", exc_info=True)
        
        if exit_on_error:
            exit_code = getattr(error, 'exit_code', 1)
            sys.exit(exit_code)
    
    def _handle_mcp_manager_error(
        self,
        error: MCPManagerError,
        context: Optional[str] = None
    ) -> None:
        """Handle MCP Manager specific errors."""
        
        # Determine severity styling
        severity_styles = {
            ErrorSeverity.LOW: self.output.theme.INFO,
            ErrorSeverity.MEDIUM: self.output.theme.WARNING,
            ErrorSeverity.HIGH: self.output.theme.ERROR,
            ErrorSeverity.CRITICAL: self.output.theme.ERROR
        }
        
        severity_icons = {
            ErrorSeverity.LOW: StatusIcon.INFO,
            ErrorSeverity.MEDIUM: StatusIcon.WARNING,
            ErrorSeverity.HIGH: StatusIcon.ERROR,
            ErrorSeverity.CRITICAL: StatusIcon.ERROR
        }
        
        style = severity_styles.get(error.severity, self.output.theme.ERROR)
        icon = severity_icons.get(error.severity, StatusIcon.ERROR)
        
        # Build error message
        title = f"{icon} {error.category.value.title()} Error"
        if context:
            title += f" ({context})"
        
        # Create error panel content
        content_lines = [error.message]
        
        # Add details if available
        if error.details:
            content_lines.append("")
            content_lines.append("Details:")
            for key, value in error.details.items():
                content_lines.append(f"  • {key}: {value}")
        
        # Add suggestions
        suggestions = error.suggestions or self._get_suggestions_for_error(str(error))
        if suggestions:
            content_lines.append("")
            content_lines.append("Suggested fixes:")
            for suggestion in suggestions:
                content_lines.append(f"  • {suggestion}")
        
        # Display error panel
        error_panel = Panel(
            "\n".join(content_lines),
            title=title,
            border_style=style,
            padding=(1, 2)
        )
        
        self.output.console.print(error_panel)
        
        # Show debug info if enabled
        if self.debug:
            self.output.console.print("\n[dim]Debug information:[/dim]")
            if hasattr(error, '__traceback__') and error.__traceback__:
                traceback_obj = Traceback.from_exception(
                    type(error),
                    error,
                    error.__traceback__,
                    show_locals=True
                )
                self.output.console.print(traceback_obj)
    
    def _handle_generic_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ) -> None:
        """Handle generic Python exceptions."""
        
        # Map common exceptions to user-friendly messages
        error_type = type(error).__name__
        error_message = str(error)
        
        user_message = self._get_user_friendly_message(error_type, error_message)
        suggestions = self._get_suggestions_for_error(error_message)
        
        title = f"{StatusIcon.ERROR} {error_type}"
        if context:
            title += f" ({context})"
        
        # Build content
        content_lines = [user_message or error_message]
        
        # Add suggestions
        if suggestions:
            content_lines.append("")
            content_lines.append("Suggested fixes:")
            for suggestion in suggestions:
                content_lines.append(f"  • {suggestion}")
        
        # Display error panel
        error_panel = Panel(
            "\n".join(content_lines),
            title=title,
            border_style=self.output.theme.ERROR,
            padding=(1, 2)
        )
        
        self.output.console.print(error_panel)
        
        # Show debug info if enabled
        if self.debug:
            self.output.console.print("\n[dim]Debug information:[/dim]")
            if hasattr(error, '__traceback__') and error.__traceback__:
                traceback_obj = Traceback.from_exception(
                    type(error),
                    error,
                    error.__traceback__,
                    show_locals=True
                )
                self.output.console.print(traceback_obj)
    
    def _get_user_friendly_message(self, error_type: str, error_message: str) -> Optional[str]:
        """Convert technical error messages to user-friendly ones."""
        
        friendly_messages = {
            "FileNotFoundError": "File or directory not found",
            "PermissionError": "Permission denied - insufficient access rights",
            "ConnectionRefusedError": "Cannot connect to server - connection refused",
            "TimeoutError": "Operation timed out",
            "ValueError": "Invalid value provided",
            "TypeError": "Invalid data type",
            "KeyError": "Required configuration key missing",
            "ImportError": "Required module not installed",
            "OSError": "Operating system error occurred"
        }
        
        base_message = friendly_messages.get(error_type)
        
        if base_message:
            # Add specific details from the error message when helpful
            if error_type == "FileNotFoundError" and "No such file or directory" in error_message:
                # Extract filename from error message if possible
                import re
                filename_match = re.search(r"'([^']+)'", error_message)
                if filename_match:
                    filename = filename_match.group(1)
                    return f"{base_message}: {filename}"
            
            return base_message
        
        return None
    
    def _get_suggestions_for_error(self, error_message: str) -> List[str]:
        """Get suggestions based on error message patterns."""
        error_lower = error_message.lower()
        suggestions = []
        
        for pattern, pattern_suggestions in self._error_suggestions.items():
            if pattern in error_lower:
                suggestions.extend(pattern_suggestions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]  # Limit to 5 suggestions
    
    def wrap_typer_command(self, func: Callable) -> Callable:
        """Decorator to wrap Typer commands with error handling."""
        
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.handle_error(e, context=func.__name__)
        
        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__ = getattr(func, '__annotations__', {})
        
        return wrapper
    
    def set_debug_mode(self, debug: bool) -> None:
        """Enable or disable debug mode."""
        self.debug = debug
    
    def validate_and_suggest(
        self,
        value: Any,
        validators: List[Callable[[Any], bool]],
        field_name: str,
        suggestions: Optional[List[str]] = None
    ) -> Any:
        """Validate a value and provide suggestions if validation fails."""
        
        for validator in validators:
            try:
                if not validator(value):
                    raise ValidationError(
                        f"Invalid {field_name}: {value}",
                        suggestions=suggestions or [
                            f"Check {field_name} format and try again",
                            f"Use 'mcp-manager help' for more information"
                        ],
                        details={"field": field_name, "value": str(value)}
                    )
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise
                else:
                    raise ValidationError(
                        f"Validation failed for {field_name}: {str(e)}",
                        suggestions=suggestions or [
                            f"Check {field_name} format and try again"
                        ],
                        details={"field": field_name, "value": str(value), "error": str(e)}
                    )
        
        return value


# Global error handler instance
error_handler = ErrorHandler()


def set_error_handler(handler: ErrorHandler) -> None:
    """Set the global error handler."""
    global error_handler
    error_handler = handler


def get_error_handler() -> ErrorHandler:
    """Get the global error handler."""
    return error_handler


def handle_error(
    error: Exception,
    context: Optional[str] = None,
    exit_on_error: bool = True
) -> None:
    """Handle an error using the global error handler."""
    error_handler.handle_error(error, context, exit_on_error)


def error_boundary(context: Optional[str] = None):
    """Decorator for error boundary around functions."""
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context or func.__name__)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__ = getattr(func, '__annotations__', {})
        
        return wrapper
    
    return decorator


def typer_error_handler(func: Callable) -> Callable:
    """Decorator specifically for Typer commands."""
    return error_handler.wrap_typer_command(func)
