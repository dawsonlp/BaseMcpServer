"""
Logging infrastructure for MCP Manager 3.0.

Provides structured, configurable logging with multiple output formats
and log levels. Supports both file and console output with rich formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.highlighter import ReprHighlighter

from mcp_manager.core.state import get_logs_dir
import mcp_manager.core.globals as globals


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class MCPManagerLogger:
    """Centralized logger configuration for MCP Manager."""
    
    def __init__(self):
        self.console = Console(stderr=True)
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Set up the root logger configuration."""
        root_logger = logging.getLogger("mcp_manager")
        root_logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Add console handler with Rich formatting
        console_handler = self._create_console_handler()
        root_logger.addHandler(console_handler)
        
        # Add file handler with structured logging
        file_handler = self._create_file_handler()
        if file_handler:
            root_logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate messages
        root_logger.propagate = False
        
        self.loggers["root"] = root_logger
    
    def _create_console_handler(self) -> RichHandler:
        """Create a Rich console handler for beautiful terminal output."""
        handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=globals.VERBOSE,
            rich_tracebacks=True,
            tracebacks_show_locals=globals.VERBOSE,
        )
        
        # Set log level based on global settings
        if globals.QUIET:
            handler.setLevel(logging.WARNING)
        elif globals.VERBOSE:
            handler.setLevel(logging.DEBUG)
        else:
            handler.setLevel(logging.INFO)
        
        return handler
    
    def _create_file_handler(self) -> Optional[logging.FileHandler]:
        """Create a file handler for persistent logging."""
        try:
            logs_dir = get_logs_dir()
            log_file = logs_dir / "mcp-manager.log"
            
            handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            handler.setLevel(logging.DEBUG)
            
            # Use structured JSON formatting for file logs
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            
            return handler
        except Exception as e:
            # If we can't create file handler, log to console
            print(f"Warning: Could not create log file handler: {e}")
            return None
    
    def get_logger(self, name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """Get a logger instance with optional context."""
        full_name = f"mcp_manager.{name}" if name != "root" else "mcp_manager"
        
        if full_name in self.loggers:
            logger = self.loggers[full_name]
        else:
            logger = logging.getLogger(full_name)
            # Inherit from root logger configuration
            if not logger.handlers:
                logger.parent = self.loggers["root"]
            self.loggers[full_name] = logger
        
        # Add context if provided
        if context:
            logger = logging.LoggerAdapter(logger, context)
        
        return logger
    
    def get_server_logger(self, server_name: str) -> logging.Logger:
        """Get a dedicated logger for a specific server."""
        logger_name = f"server.{server_name}"
        logger = self.get_logger(logger_name, {"server": server_name})
        
        # Create separate log file for this server
        try:
            logs_dir = get_logs_dir()
            server_log_file = logs_dir / f"server-{server_name}.log"
            
            # Check if we already have a file handler for this server
            existing_handlers = [
                h for h in logger.handlers 
                if isinstance(h, logging.FileHandler) and 
                   h.baseFilename == str(server_log_file)
            ]
            
            if not existing_handlers:
                file_handler = logging.FileHandler(
                    server_log_file, mode='a', encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(StructuredFormatter())
                logger.addHandler(file_handler)
        
        except Exception as e:
            # Log to main logger if server-specific logging fails
            self.get_logger("core").warning(
                f"Could not create log file for server {server_name}: {e}"
            )
        
        return logger
    
    def set_log_level(self, level: str):
        """Set the global log level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        
        numeric_level = level_map.get(level.upper(), logging.INFO)
        
        # Update all existing loggers
        for logger in self.loggers.values():
            if isinstance(logger, logging.Logger):
                logger.setLevel(numeric_level)
                # Update console handlers
                for handler in logger.handlers:
                    if isinstance(handler, RichHandler):
                        handler.setLevel(numeric_level)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files."""
        try:
            logs_dir = get_logs_dir()
            if not logs_dir.exists():
                return
            
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            removed_count = 0
            
            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                self.get_logger("core").info(
                    f"Cleaned up {removed_count} old log files"
                )
        
        except Exception as e:
            self.get_logger("core").warning(f"Failed to cleanup old logs: {e}")
    
    def error(self, message: str, **kwargs):
        """Log an error message (compatibility method)."""
        self.get_logger("core").error(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message (compatibility method)."""
        self.get_logger("core").warning(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message (compatibility method)."""
        self.get_logger("core").info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message (compatibility method)."""
        self.get_logger("core").debug(message, **kwargs)


# Global logger instance
_logger_manager: Optional[MCPManagerLogger] = None


def get_logger_manager() -> MCPManagerLogger:
    """Get the global logger manager instance."""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = MCPManagerLogger()
    return _logger_manager


def get_logger(name: str = "core", context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Get a logger instance (convenience function)."""
    return get_logger_manager().get_logger(name, context)


def get_server_logger(server_name: str) -> logging.Logger:
    """Get a server-specific logger (convenience function)."""
    return get_logger_manager().get_server_logger(server_name)


def set_log_level(level: str):
    """Set global log level (convenience function)."""
    get_logger_manager().set_log_level(level)


def cleanup_old_logs(days_to_keep: int = 30):
    """Clean up old log files (convenience function)."""
    get_logger_manager().cleanup_old_logs(days_to_keep)


# Log helper functions for common patterns
def log_command_start(command: str, args: Dict[str, Any], logger: Optional[logging.Logger] = None):
    """Log the start of a command execution."""
    if logger is None:
        logger = get_logger("cli")
    
    logger.info(f"Starting command: {command}", extra={
        "command": command,
        "arguments": args,
        "event": "command_start"
    })


def log_command_end(command: str, success: bool, duration_ms: float, 
                   logger: Optional[logging.Logger] = None):
    """Log the end of a command execution."""
    if logger is None:
        logger = get_logger("cli")
    
    level = logging.INFO if success else logging.ERROR
    status = "completed" if success else "failed"
    
    logger.log(level, f"Command {command} {status} in {duration_ms:.1f}ms", extra={
        "command": command,
        "success": success,
        "duration_ms": duration_ms,
        "event": "command_end"
    })


def log_server_event(server_name: str, event: str, details: Optional[Dict[str, Any]] = None):
    """Log a server-related event."""
    logger = get_server_logger(server_name)
    
    extra_data = {
        "server": server_name,
        "event": event,
    }
    if details:
        extra_data.update(details)
    
    logger.info(f"Server {server_name}: {event}", extra=extra_data)


def log_error_with_context(error: Exception, context: Dict[str, Any], 
                          logger: Optional[logging.Logger] = None):
    """Log an error with additional context information."""
    if logger is None:
        logger = get_logger("error")
    
    logger.error(f"Error occurred: {str(error)}", extra={
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "event": "error"
    }, exc_info=True)


class LogContext:
    """Context manager for adding context to log messages."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.adapter = None
    
    def __enter__(self) -> logging.Logger:
        if isinstance(self.logger, logging.LoggerAdapter):
            # Merge contexts
            merged_context = {**self.logger.extra, **self.context}
            self.adapter = logging.LoggerAdapter(self.logger.logger, merged_context)
        else:
            self.adapter = logging.LoggerAdapter(self.logger, self.context)
        return self.adapter
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Usage example:
# logger = get_logger("install")
# with LogContext(logger, server="jira-helper", operation="install") as ctx_logger:
#     ctx_logger.info("Starting installation")  # Will include server and operation in log
