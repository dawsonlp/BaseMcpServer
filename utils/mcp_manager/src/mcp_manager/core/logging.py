"""
Logging infrastructure for MCP Manager.

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
            logs_dir.mkdir(parents=True, exist_ok=True)
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

