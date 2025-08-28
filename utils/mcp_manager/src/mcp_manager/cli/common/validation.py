"""
Input validation utilities for MCP Manager CLI.

This module provides CLI-specific validation functions, interactive input handling,
and user-friendly validation with suggestions and auto-completion.
"""

import re
import socket
from pathlib import Path
from typing import Any, Callable, List, Optional, Union, Dict, Tuple
from urllib.parse import urlparse

import typer
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.console import Console

from mcp_manager.core.models import ServerType, TransportType
from mcp_manager.core.validation import ValidationRule, ValidationResult
from mcp_manager.cli.common.output import RichOutputManager
from mcp_manager.cli.common.errors import ValidationError, ErrorHandler


class CLIValidator:
    """CLI-specific validation utilities."""
    
    def __init__(
        self,
        output_manager: Optional[RichOutputManager] = None,
        error_handler: Optional[ErrorHandler] = None
    ):
        self.output = output_manager or RichOutputManager()
        self.error_handler = error_handler or ErrorHandler()
    
    def validate_server_name(self, name: str) -> ValidationResult:
        """Validate a server name."""
        errors = []
        warnings = []
        
        # Check basic format
        if not name:
            errors.append("Server name cannot be empty")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', name):
            errors.append("Server name can only contain letters, numbers, hyphens, and underscores")
        elif len(name) > 50:
            warnings.append("Server name is quite long (>50 characters)")
        elif name.startswith('-') or name.endswith('-'):
            errors.append("Server name cannot start or end with a hyphen")
        elif name.startswith('_') or name.endswith('_'):
            warnings.append("Server names starting/ending with underscore may cause issues")
        
        # Check for reserved names
        reserved_names = {
            'all', 'none', 'null', 'true', 'false', 'help', 'version',
            'config', 'status', 'list', 'install', 'uninstall'
        }
        if name.lower() in reserved_names:
            errors.append(f"'{name}' is a reserved name and cannot be used")
        
        return ValidationResult(
            field="server_name",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_port(self, port: Union[int, str]) -> ValidationResult:
        """Validate a port number."""
        errors = []
        warnings = []
        
        try:
            port_int = int(port)
        except (ValueError, TypeError):
            errors.append("Port must be a valid integer")
            return ValidationResult("port", False, errors, warnings)
        
        if port_int < 1 or port_int > 65535:
            errors.append("Port must be between 1 and 65535")
        elif port_int < 1024:
            warnings.append("Using privileged port (<1024) may require elevated permissions")
        elif port_int in [22, 80, 443, 3389, 5432, 3306]:
            warnings.append(f"Port {port_int} is commonly used by other services")
        
        return ValidationResult(
            field="port",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_host(self, host: str) -> ValidationResult:
        """Validate a hostname or IP address."""
        errors = []
        warnings = []
        
        if not host:
            errors.append("Host cannot be empty")
            return ValidationResult("host", False, errors, warnings)
        
        # Check if it's an IP address
        try:
            socket.inet_aton(host)
            # Valid IP address
            if host == "0.0.0.0":
                warnings.append("0.0.0.0 binds to all interfaces - ensure this is intended")
            elif host.startswith("127."):
                # Localhost IP - this is fine
                pass
            elif host.startswith("10.") or host.startswith("192.168.") or host.startswith("172."):
                # Private IP - this is usually fine
                pass
            else:
                warnings.append("Using public IP address - ensure firewall is configured")
        except socket.error:
            # Not a valid IP, check if it's a valid hostname
            if not re.match(r'^[a-zA-Z0-9.-]+$', host):
                errors.append("Host contains invalid characters")
            elif host.startswith('.') or host.endswith('.'):
                errors.append("Host cannot start or end with a period")
            elif '..' in host:
                errors.append("Host cannot contain consecutive periods")
            elif len(host) > 253:
                errors.append("Host name is too long (max 253 characters)")
        
        return ValidationResult(
            field="host",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_url(self, url: str) -> ValidationResult:
        """Validate a URL."""
        errors = []
        warnings = []
        
        if not url:
            errors.append("URL cannot be empty")
            return ValidationResult("url", False, errors, warnings)
        
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                errors.append("URL must include a scheme (http:// or https://)")
            elif parsed.scheme not in ['http', 'https']:
                errors.append("URL scheme must be http or https")
            
            if not parsed.netloc:
                errors.append("URL must include a host")
            
            if parsed.scheme == 'http' and not parsed.port:
                warnings.append("HTTP URLs without explicit port may be insecure")
            
        except Exception as e:
            errors.append(f"Invalid URL format: {str(e)}")
        
        return ValidationResult(
            field="url",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_file_path(
        self,
        path: Union[str, Path],
        must_exist: bool = False,
        must_be_file: bool = True,
        must_be_executable: bool = False
    ) -> ValidationResult:
        """Validate a file path."""
        errors = []
        warnings = []
        
        try:
            path_obj = Path(path)
        except Exception as e:
            errors.append(f"Invalid path format: {str(e)}")
            return ValidationResult("file_path", False, errors, warnings)
        
        if must_exist and not path_obj.exists():
            errors.append(f"Path does not exist: {path}")
        elif path_obj.exists():
            if must_be_file and not path_obj.is_file():
                errors.append(f"Path is not a file: {path}")
            elif must_be_executable and not path_obj.stat().st_mode & 0o111:
                errors.append(f"File is not executable: {path}")
        
        # Check for common path issues
        if str(path_obj).startswith('~') and not path_obj.expanduser().exists():
            warnings.append("Tilde (~) in path - ensure it expands correctly")
        
        return ValidationResult(
            field="file_path",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_directory_path(
        self,
        path: Union[str, Path],
        must_exist: bool = False,
        create_if_missing: bool = False
    ) -> ValidationResult:
        """Validate a directory path."""
        errors = []
        warnings = []
        
        try:
            path_obj = Path(path)
        except Exception as e:
            errors.append(f"Invalid path format: {str(e)}")
            return ValidationResult("directory_path", False, errors, warnings)
        
        if must_exist and not path_obj.exists():
            if create_if_missing:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    warnings.append(f"Created directory: {path}")
                except Exception as e:
                    errors.append(f"Cannot create directory {path}: {str(e)}")
            else:
                errors.append(f"Directory does not exist: {path}")
        elif path_obj.exists() and not path_obj.is_dir():
            errors.append(f"Path exists but is not a directory: {path}")
        
        return ValidationResult(
            field="directory_path",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_command_args(self, args: List[str]) -> ValidationResult:
        """Validate command arguments."""
        errors = []
        warnings = []
        
        for i, arg in enumerate(args):
            if not arg.strip():
                warnings.append(f"Argument {i+1} is empty or whitespace only")
            
            # Check for potentially dangerous arguments
            dangerous_patterns = ['rm -rf', '> /dev/', 'sudo ', 'chmod 777']
            for pattern in dangerous_patterns:
                if pattern in arg.lower():
                    warnings.append(f"Argument {i+1} contains potentially dangerous pattern: {pattern}")
        
        return ValidationResult(
            field="command_args",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def interactive_server_name_input(
        self,
        prompt: str = "Server name",
        default: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ) -> str:
        """Interactive server name input with validation."""
        while True:
            try:
                name = Prompt.ask(
                    prompt,
                    default=default,
                    console=self.output.console
                )
                
                result = self.validate_server_name(name)
                
                if result.valid:
                    if result.warnings:
                        for warning in result.warnings:
                            self.output.print_warning(warning)
                        
                        if not Confirm.ask("Continue anyway?", console=self.output.console):
                            continue
                    
                    return name
                else:
                    for error in result.errors:
                        self.output.print_error(error)
                    
                    if suggestions:
                        self.output.console.print("\nSuggestions:")
                        for suggestion in suggestions:
                            self.output.console.print(f"  • {suggestion}")
                    
            except (KeyboardInterrupt, EOFError):
                self.output.console.print("\nOperation cancelled")
                raise typer.Abort()
    
    def interactive_port_input(
        self,
        prompt: str = "Port number",
        default: Optional[int] = None
    ) -> int:
        """Interactive port input with validation."""
        while True:
            try:
                port = IntPrompt.ask(
                    prompt,
                    default=default,
                    console=self.output.console
                )
                
                result = self.validate_port(port)
                
                if result.valid:
                    if result.warnings:
                        for warning in result.warnings:
                            self.output.print_warning(warning)
                        
                        if not Confirm.ask("Continue anyway?", console=self.output.console):
                            continue
                    
                    return port
                else:
                    for error in result.errors:
                        self.output.print_error(error)
                    
            except (KeyboardInterrupt, EOFError):
                self.output.console.print("\nOperation cancelled")
                raise typer.Abort()
    
    def interactive_path_input(
        self,
        prompt: str = "Path",
        default: Optional[str] = None,
        must_exist: bool = False,
        path_type: str = "file"  # "file" or "directory"
    ) -> Path:
        """Interactive path input with validation."""
        while True:
            try:
                path_str = Prompt.ask(
                    prompt,
                    default=default,
                    console=self.output.console
                )
                
                if path_type == "directory":
                    result = self.validate_directory_path(path_str, must_exist)
                else:
                    result = self.validate_file_path(path_str, must_exist)
                
                if result.valid:
                    if result.warnings:
                        for warning in result.warnings:
                            self.output.print_warning(warning)
                        
                        if not Confirm.ask("Continue anyway?", console=self.output.console):
                            continue
                    
                    return Path(path_str)
                else:
                    for error in result.errors:
                        self.output.print_error(error)
                    
            except (KeyboardInterrupt, EOFError):
                self.output.console.print("\nOperation cancelled")
                raise typer.Abort()
    
    def interactive_choice_input(
        self,
        prompt: str,
        choices: List[str],
        default: Optional[str] = None,
        case_sensitive: bool = False
    ) -> str:
        """Interactive choice input with validation."""
        choices_display = "/".join(choices)
        if default:
            choices_display = choices_display.replace(default, f"[{default}]")
        
        while True:
            try:
                choice = Prompt.ask(
                    f"{prompt} ({choices_display})",
                    default=default,
                    console=self.output.console
                )
                
                # Validate choice
                valid_choices = choices if case_sensitive else [c.lower() for c in choices]
                check_choice = choice if case_sensitive else choice.lower()
                
                if check_choice in valid_choices:
                    # Return the original case from choices
                    if not case_sensitive:
                        for i, c in enumerate(valid_choices):
                            if c == check_choice:
                                return choices[i]
                    return choice
                else:
                    self.output.print_error(f"Invalid choice. Please choose from: {', '.join(choices)}")
                    
            except (KeyboardInterrupt, EOFError):
                self.output.console.print("\nOperation cancelled")
                raise typer.Abort()
    
    def validate_server_config(
        self,
        name: str,
        server_type: ServerType,
        transport: TransportType,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        url: Optional[str] = None
    ) -> List[ValidationResult]:
        """Validate complete server configuration."""
        results = []
        
        # Validate name
        results.append(self.validate_server_name(name))
        
        # Validate transport-specific fields
        if transport == TransportType.STDIO:
            if not command:
                results.append(ValidationResult(
                    "command",
                    False,
                    ["Command is required for stdio transport"],
                    []
                ))
            else:
                # Validate command exists (basic check)
                if not Path(command).exists() and not any(
                    Path(p) / command for p in Path("/usr/bin").iterdir() if Path(p).is_dir()
                ):
                    results.append(ValidationResult(
                        "command",
                        True,
                        [],
                        [f"Command '{command}' not found in common locations"]
                    ))
            
            if args:
                results.append(self.validate_command_args(args))
                
        elif transport == TransportType.SSE:
            if url:
                results.append(self.validate_url(url))
            else:
                if host:
                    results.append(self.validate_host(host))
                if port:
                    results.append(self.validate_port(port))
                else:
                    results.append(ValidationResult(
                        "port",
                        False,
                        ["Port is required for SSE transport"],
                        []
                    ))
        
        return results
    
    def display_validation_results(self, results: List[ValidationResult]) -> bool:
        """Display validation results and return whether all passed."""
        self.output.print_validation_results(results)
        return all(result.valid for result in results)


# Validation helper functions
def is_valid_server_name(name: str) -> bool:
    """Quick server name validation check."""
    if not name or len(name) > 50:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))


def is_valid_port(port: Union[int, str]) -> bool:
    """Quick port validation check."""
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def is_valid_host(host: str) -> bool:
    """Quick host validation check."""
    if not host:
        return False
    
    # Try as IP address
    try:
        socket.inet_aton(host)
        return True
    except socket.error:
        pass
    
    # Try as hostname
    return bool(re.match(r'^[a-zA-Z0-9.-]+$', host)) and not (
        host.startswith('.') or host.endswith('.') or '..' in host
    )


def suggest_server_name(base_name: str) -> List[str]:
    """Generate server name suggestions."""
    suggestions = []
    
    # Clean up the base name
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name.lower())
    
    if clean_name != base_name:
        suggestions.append(clean_name)
    
    # Add variations
    suggestions.extend([
        f"{clean_name}_server",
        f"mcp_{clean_name}",
        f"{clean_name}_mcp",
        f"{clean_name}1"
    ])
    
    return suggestions[:5]  # Limit to 5 suggestions


# Global CLI validator instance
cli_validator = CLIValidator()


def set_cli_validator(validator: CLIValidator) -> None:
    """Set the global CLI validator."""
    global cli_validator
    cli_validator = validator


def get_cli_validator() -> CLIValidator:
    """Get the global CLI validator."""
    return cli_validator
