"""
Configuration validation framework for MCP Manager 3.0.

Provides comprehensive validation for server configurations, environment
variables, and other settings with clear error messages and fix suggestions.
"""

import re
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
import json
import yaml

from mcp_manager.core.models import (
    ValidationResult, ValidationError, Server, ServerType, 
    TransportType, InstallationType, SourceType
)
from mcp_manager.core.logging import get_logger


logger = get_logger("validation")


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, field: str, message: str, suggestion: Optional[str] = None):
        self.field = field
        self.message = message
        self.suggestion = suggestion
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate a value. Return True if valid, False otherwise."""
        raise NotImplementedError("Subclasses must implement validate method")


class RequiredRule(ValidationRule):
    """Rule to check if a field is required and not None/empty."""
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True


class TypeRule(ValidationRule):
    """Rule to check if a field matches the expected type."""
    
    def __init__(self, field: str, expected_type: type, message: Optional[str] = None, 
                 suggestion: Optional[str] = None):
        self.expected_type = expected_type
        if message is None:
            message = f"Must be of type {expected_type.__name__}"
        if suggestion is None:
            suggestion = f"Provide a valid {expected_type.__name__} value"
        super().__init__(field, message, suggestion)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if value is None:
            return True  # Let RequiredRule handle None values
        return isinstance(value, self.expected_type)


class RegexRule(ValidationRule):
    """Rule to validate a string against a regular expression."""
    
    def __init__(self, field: str, pattern: str, message: str, 
                 suggestion: Optional[str] = None):
        self.pattern = re.compile(pattern)
        super().__init__(field, message, suggestion)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self.pattern.match(value))


class PathExistsRule(ValidationRule):
    """Rule to check if a path exists."""
    
    def __init__(self, field: str, must_be_dir: bool = False, must_be_file: bool = False,
                 message: Optional[str] = None, suggestion: Optional[str] = None):
        self.must_be_dir = must_be_dir
        self.must_be_file = must_be_file
        
        if message is None:
            if must_be_dir:
                message = "Directory does not exist"
            elif must_be_file:
                message = "File does not exist"
            else:
                message = "Path does not exist"
        
        if suggestion is None:
            suggestion = "Ensure the path exists and is accessible"
        
        super().__init__(field, message, suggestion)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if not isinstance(value, (str, Path)):
            return False
        
        path = Path(value)
        if not path.exists():
            return False
        
        if self.must_be_dir and not path.is_dir():
            return False
        if self.must_be_file and not path.is_file():
            return False
        
        return True


class URLRule(ValidationRule):
    """Rule to validate URL format."""
    
    def __init__(self, field: str, schemes: Optional[List[str]] = None,
                 message: Optional[str] = None, suggestion: Optional[str] = None):
        self.schemes = schemes or ['http', 'https']
        if message is None:
            message = f"Must be a valid URL with scheme: {', '.join(self.schemes)}"
        if suggestion is None:
            suggestion = f"Use format: {self.schemes[0]}://example.com/path"
        super().__init__(field, message, suggestion)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if not isinstance(value, str):
            return False
        
        try:
            parsed = urlparse(value)
            return (
                parsed.scheme in self.schemes and
                parsed.netloc != ""
            )
        except Exception:
            return False


class PortRule(ValidationRule):
    """Rule to validate port numbers."""
    
    def __init__(self, field: str, check_available: bool = False,
                 message: Optional[str] = None, suggestion: Optional[str] = None):
        self.check_available = check_available
        if message is None:
            message = "Must be a valid port number (1-65535)"
            if check_available:
                message += " and available"
        if suggestion is None:
            suggestion = "Choose a port between 1024-65535 for user applications"
        super().__init__(field, message, suggestion)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if not isinstance(value, int):
            return False
        
        if not (1 <= value <= 65535):
            return False
        
        if self.check_available:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    result = sock.connect_ex(('localhost', value))
                    return result != 0  # Port is available if connection fails
            except Exception:
                return False
        
        return True


class PythonVersionRule(ValidationRule):
    """Rule to validate Python version compatibility."""
    
    def __init__(self, field: str, min_version: str = "3.8",
                 message: Optional[str] = None, suggestion: Optional[str] = None):
        self.min_version = min_version
        if message is None:
            message = f"Python {min_version}+ is required"
        if suggestion is None:
            suggestion = f"Install Python {min_version} or later"
        super().__init__(field, message, suggestion)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if not isinstance(value, (str, Path)):
            return False
        
        python_path = Path(value)
        if not python_path.exists():
            return False
        
        try:
            result = subprocess.run(
                [str(python_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False
            
            # Parse version from output like "Python 3.11.0"
            version_str = result.stdout.strip().split()[1]
            version_parts = [int(x) for x in version_str.split('.')]
            min_parts = [int(x) for x in self.min_version.split('.')]
            
            return version_parts >= min_parts
            
        except Exception:
            return False


class CustomRule(ValidationRule):
    """Rule with custom validation function."""
    
    def __init__(self, field: str, validator: Callable[[Any, Optional[Dict[str, Any]]], bool],
                 message: str, suggestion: Optional[str] = None):
        self.validator = validator
        super().__init__(field, message, suggestion)
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        try:
            return self.validator(value, context)
        except Exception:
            return False


class ConfigValidator:
    """Main configuration validator class."""
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default validation rules for server configurations."""
        
        # Server name validation
        self.add_rule("name", RequiredRule("name", "Server name is required"))
        self.add_rule("name", RegexRule(
            "name", 
            r"^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$",
            "Server name must contain only letters, numbers, hyphens, and underscores",
            "Use format: my-server or my_server_123"
        ))
        
        # Server type validation
        self.add_rule("server_type", RequiredRule("server_type", "Server type is required"))
        self.add_rule("server_type", CustomRule(
            "server_type",
            lambda x, _: x in [t.value for t in ServerType],
            "Server type must be 'local' or 'remote'",
            "Use 'local' for locally installed servers or 'remote' for remote servers"
        ))
        
        # Transport validation
        self.add_rule("transport", CustomRule(
            "transport",
            lambda x, _: x in [t.value for t in TransportType],
            "Transport must be 'stdio' or 'sse'",
            "Use 'stdio' for development or 'sse' for network/production use"
        ))
        
        # Port validation (when transport is SSE)
        self.add_rule("port", CustomRule(
            "port",
            self._validate_port_when_sse,
            "Port is required when using SSE transport",
            "Provide a port number between 1024-65535"
        ))
        
        # Local server validation
        self.add_rule("source_dir", CustomRule(
            "source_dir",
            self._validate_source_dir,
            "Source directory is required for local servers",
            "Provide path to directory containing server code"
        ))
        
        # Remote server validation
        self.add_rule("url", CustomRule(
            "url",
            self._validate_url_for_remote,
            "URL is required for remote servers",
            "Provide full URL: https://example.com/mcp"
        ))
        
        self.add_rule("api_key", CustomRule(
            "api_key",
            self._validate_api_key_for_remote,
            "API key is required for remote servers",
            "Provide valid API key for authentication"
        ))
        
        # Virtual environment validation
        self.add_rule("venv_dir", PathExistsRule(
            "venv_dir", 
            must_be_dir=True,
            message="Virtual environment directory does not exist",
            suggestion="Create virtual environment or provide correct path"
        ))
    
    def _validate_port_when_sse(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate port is provided when transport is SSE."""
        if not context:
            return True
        
        transport = context.get("transport")
        if transport == TransportType.SSE.value:
            return value is not None and isinstance(value, int) and 1 <= value <= 65535
        
        return True  # Port not required for other transports
    
    def _validate_source_dir(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate source directory for local servers."""
        if not context:
            return True
        
        server_type = context.get("server_type")
        if server_type == ServerType.LOCAL.value:
            if value is None:
                return False
            path = Path(value)
            return path.exists() and path.is_dir()
        
        return True  # Not required for remote servers
    
    def _validate_url_for_remote(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate URL for remote servers."""
        if not context:
            return True
        
        server_type = context.get("server_type")
        if server_type == ServerType.REMOTE.value:
            if value is None:
                return False
            return URLRule("url", ["http", "https"]).validate(value)
        
        return True  # Not required for local servers
    
    def _validate_api_key_for_remote(self, value: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate API key for remote servers."""
        if not context:
            return True
        
        server_type = context.get("server_type")
        if server_type == ServerType.REMOTE.value:
            return value is not None and isinstance(value, str) and len(value.strip()) > 0
        
        return True  # Not required for local servers
    
    def add_rule(self, field: str, rule: ValidationRule):
        """Add a validation rule for a field."""
        if field not in self.rules:
            self.rules[field] = []
        self.rules[field].append(rule)
    
    def remove_rules(self, field: str):
        """Remove all rules for a field."""
        if field in self.rules:
            del self.rules[field]
    
    def validate_server(self, server: Server) -> ValidationResult:
        """Validate a complete server configuration."""
        logger.debug(f"Validating server configuration for {server.name}")
        
        result = ValidationResult(is_valid=True)
        
        # Convert server to dict for validation
        server_dict = server.model_dump()
        
        # Validate each field
        for field, rules in self.rules.items():
            value = server_dict.get(field)
            
            for rule in rules:
                if not rule.validate(value, server_dict):
                    result.add_error(field, rule.message, rule.suggestion)
        
        # Additional cross-field validations
        self._validate_server_consistency(server, result)
        
        logger.debug(f"Server validation result: {'valid' if result.is_valid else 'invalid'}")
        return result
    
    def _validate_server_consistency(self, server: Server, result: ValidationResult):
        """Perform cross-field validation checks."""
        
        # Check Python executable exists for venv installations
        if (server.is_local() and server.installation_type == InstallationType.VENV and
            server.venv_dir):
            python_path = server.get_python_executable()
            if python_path and not python_path.exists():
                result.add_error(
                    "venv_dir",
                    "Python executable not found in virtual environment",
                    "Recreate the virtual environment or check the path"
                )
        
        # Check main script exists for local servers
        if server.is_local() and server.source_dir:
            main_script = server.get_main_script_path()
            if not main_script:
                result.add_warning(
                    "source_dir",
                    "No main.py script found in source directory",
                    "Ensure main.py exists in the source directory or src/ subdirectory"
                )
        
        # Validate port availability for SSE transport
        if (server.transport == TransportType.SSE and server.port and
            not self._is_port_available(server.port)):
            result.add_warning(
                "port",
                f"Port {server.port} may be in use",
                "Choose a different port or stop the service using this port"
            )
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('localhost', port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return False
    
    def validate_config_file(self, config_path: Path) -> ValidationResult:
        """Validate a configuration file format."""
        result = ValidationResult(is_valid=True)
        
        if not config_path.exists():
            result.add_error(
                "config_file",
                "Configuration file does not exist",
                f"Create the configuration file at {config_path}"
            )
            return result
        
        try:
            content = config_path.read_text()
            
            # Try to parse as YAML or JSON
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                yaml.safe_load(content)
            elif config_path.suffix.lower() == '.json':
                json.loads(content)
            else:
                result.add_warning(
                    "config_file",
                    "Unknown configuration file format",
                    "Use .yaml, .yml, or .json extension"
                )
        
        except yaml.YAMLError as e:
            result.add_error(
                "config_file",
                f"Invalid YAML format: {e}",
                "Fix YAML syntax errors"
            )
        except json.JSONDecodeError as e:
            result.add_error(
                "config_file",
                f"Invalid JSON format: {e}",
                "Fix JSON syntax errors"
            )
        except Exception as e:
            result.add_error(
                "config_file",
                f"Could not read configuration file: {e}",
                "Ensure file is readable and not corrupted"
            )
        
        return result
    
    def validate_environment(self, env_vars: Dict[str, str], 
                           required_vars: Optional[List[str]] = None) -> ValidationResult:
        """Validate environment variables."""
        result = ValidationResult(is_valid=True)
        
        if required_vars:
            for var in required_vars:
                if var not in env_vars or not env_vars[var].strip():
                    result.add_error(
                        f"env.{var}",
                        f"Required environment variable {var} is missing or empty",
                        f"Set the {var} environment variable"
                    )
        
        # Validate common environment variable patterns
        for var, value in env_vars.items():
            if var.endswith("_URL") and value:
                url_rule = URLRule(f"env.{var}")
                if not url_rule.validate(value):
                    result.add_error(f"env.{var}", url_rule.message, url_rule.suggestion)
            
            elif var.endswith("_PORT") and value:
                try:
                    port = int(value)
                    port_rule = PortRule(f"env.{var}")
                    if not port_rule.validate(port):
                        result.add_error(f"env.{var}", port_rule.message, port_rule.suggestion)
                except ValueError:
                    result.add_error(
                        f"env.{var}",
                        "Port must be a valid integer",
                        "Provide a numeric port value"
                    )
        
        return result


# Global validator instance
_validator: Optional[ConfigValidator] = None


def get_validator() -> ConfigValidator:
    """Get the global configuration validator instance."""
    global _validator
    if _validator is None:
        _validator = ConfigValidator()
    return _validator


def validate_server_config(server: Server) -> ValidationResult:
    """Validate a server configuration (convenience function)."""
    return get_validator().validate_server(server)


def validate_config_file(config_path: Path) -> ValidationResult:
    """Validate a configuration file (convenience function)."""
    return get_validator().validate_config_file(config_path)


def validate_environment(env_vars: Dict[str, str], 
                        required_vars: Optional[List[str]] = None) -> ValidationResult:
    """Validate environment variables (convenience function)."""
    return get_validator().validate_environment(env_vars, required_vars)
