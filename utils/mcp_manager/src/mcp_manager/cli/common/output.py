"""
Output formatting utilities for MCP Manager CLI.

This module provides Rich-based console output formatting, including
tables, status displays, progress indicators, and consistent styling.
"""

import json
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path

from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
from rich.tree import Tree
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.status import Status
from rich.markup import escape
from rich.json import JSON
from rich.syntax import Syntax
from rich.rule import Rule
from rich import box
from pydantic import BaseModel

from mcp_manager.core.models import (
    Server, ProcessInfo, HealthStatus, HealthReport, 
    ServerState, PlatformType, ValidationResult
)


class OutputFormat(str, Enum):
    """Output format options."""
    TABLE = "table"
    JSON = "json"
    YAML = "yaml" 
    PLAIN = "plain"
    TREE = "tree"


class StatusIcon(str, Enum):
    """Status icons for consistent display."""
    SUCCESS = "✅"
    ERROR = "❌"  
    WARNING = "⚠️"
    INFO = "ℹ️"
    RUNNING = "🟢"
    STOPPED = "🔴"
    UNKNOWN = "❓"
    HEALTHY = "💚"
    UNHEALTHY = "💔"
    DEGRADED = "🟡"


class OutputTheme:
    """Color theme for console output."""
    
    # Status colors
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "blue"
    MUTED = "dim"
    
    # Server status colors
    RUNNING = "bright_green"
    STOPPED = "bright_red"
    UNKNOWN = "dim"
    
    # Health status colors
    HEALTHY = "green"
    UNHEALTHY = "red"
    DEGRADED = "yellow"
    
    # UI elements
    HEADER = "bold blue"
    SUBHEADER = "bold"
    HIGHLIGHT = "cyan"
    ACCENT = "magenta"
    BORDER = "dim"


class RichOutputManager:
    """Manages Rich-based console output formatting."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.theme = OutputTheme()
        self._current_progress: Optional[Progress] = None
        self._current_tasks: Dict[str, TaskID] = {}
    
    def success(self, message: str, **kwargs) -> None:
        """Print a success message."""
        self.console.print(f"{StatusIcon.SUCCESS} {message}", style=self.theme.SUCCESS, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Print an error message."""
        self.console.print(f"{StatusIcon.ERROR} {message}", style=self.theme.ERROR, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Print a warning message."""
        self.console.print(f"{StatusIcon.WARNING} {message}", style=self.theme.WARNING, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Print an info message."""
        self.console.print(f"{StatusIcon.INFO} {message}", style=self.theme.INFO, **kwargs)
    
    def print_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Print a formatted header."""
        header_text = Text(title, style=self.theme.HEADER)
        if subtitle:
            header_text.append(f"\n{subtitle}", style=self.theme.MUTED)
        
        panel = Panel(
            Align.center(header_text),
            box=box.DOUBLE,
            border_style=self.theme.BORDER,
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()
    
    def print_section(self, title: str) -> None:
        """Print a section separator."""
        rule = Rule(title, style=self.theme.SUBHEADER)
        self.console.print(rule)
    
    def print_key_value_pairs(self, pairs: Dict[str, Any], title: Optional[str] = None) -> None:
        """Print key-value pairs in a formatted table."""
        if title:
            self.print_section(title)
        
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column("Key", style=self.theme.HIGHLIGHT, no_wrap=True)
        table.add_column("Value", overflow="fold")
        
        for key, value in pairs.items():
            # Format the value based on type
            if isinstance(value, bool):
                formatted_value = "✓" if value else "✗"
                style = self.theme.SUCCESS if value else self.theme.ERROR
            elif isinstance(value, (list, dict)):
                formatted_value = json.dumps(value, indent=2)
                style = None
            elif value is None:
                formatted_value = "—"
                style = self.theme.MUTED
            else:
                formatted_value = str(value)
                style = None
            
            table.add_row(f"{key}:", formatted_value, style=style)
        
        self.console.print(table)
        self.console.print()
    
    def print_servers_table(
        self,
        servers: List[Server],
        states: Optional[Dict[str, ServerState]] = None,
        format_type: OutputFormat = OutputFormat.TABLE
    ) -> None:
        """Print servers in various formats."""
        if format_type == OutputFormat.JSON:
            self._print_servers_json(servers, states)
            return
        elif format_type == OutputFormat.TREE:
            self._print_servers_tree(servers, states)
            return
        
        # Table format (default)
        if not servers:
            self.info("No servers found")
            return
        
        table = Table(box=box.ROUNDED, show_lines=True)
        table.add_column("Name", style=self.theme.HIGHLIGHT, no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Type", style=self.theme.ACCENT)
        table.add_column("Transport", style=self.theme.INFO)
        table.add_column("Command/URL", overflow="ellipsis", max_width=40)
        table.add_column("Health", justify="center")
        
        for server in servers:
            # Get server state if available
            state = states.get(server.name) if states else None
            
            # Status column
            if state and state.process_info:
                status_icon = StatusIcon.RUNNING
                status_style = self.theme.RUNNING
                status_text = "Running"
            else:
                status_icon = StatusIcon.STOPPED
                status_style = self.theme.STOPPED
                status_text = "Stopped"
            
            # Health column
            if state and state.health_report:
                health = state.health_report.overall_status
                if health == HealthStatus.HEALTHY:
                    health_icon = StatusIcon.HEALTHY
                    health_style = self.theme.HEALTHY
                elif health == HealthStatus.UNHEALTHY:
                    health_icon = StatusIcon.UNHEALTHY
                    health_style = self.theme.UNHEALTHY
                else:
                    health_icon = StatusIcon.DEGRADED
                    health_style = self.theme.DEGRADED
            else:
                health_icon = StatusIcon.UNKNOWN
                health_style = self.theme.UNKNOWN
            
            # Command/URL column
            if server.command:
                cmd_display = f"{server.command}"
                if server.args:
                    cmd_display += f" {' '.join(server.args[:2])}"
                    if len(server.args) > 2:
                        cmd_display += "..."
            elif server.host and server.port:
                cmd_display = f"{server.host}:{server.port}"
            else:
                cmd_display = "—"
            
            table.add_row(
                server.name,
                f"{status_icon} {status_text}",
                server.type.value,
                server.transport.value,
                cmd_display,
                f"{health_icon}",
                style=status_style if state and state.process_info else self.theme.MUTED
            )
        
        self.console.print(table)
    
    def _print_servers_json(
        self,
        servers: List[Server],
        states: Optional[Dict[str, ServerState]] = None
    ) -> None:
        """Print servers in JSON format."""
        data = []
        for server in servers:
            server_data = server.dict()
            if states and server.name in states:
                server_data["state"] = states[server.name].dict()
            data.append(server_data)
        
        json_output = JSON.from_data(data)
        self.console.print(json_output)
    
    def _print_servers_tree(
        self,
        servers: List[Server],
        states: Optional[Dict[str, ServerState]] = None
    ) -> None:
        """Print servers in tree format."""
        tree = Tree("MCP Servers", style=self.theme.HEADER)
        
        for server in servers:
            state = states.get(server.name) if states else None
            
            # Create server node
            status_icon = StatusIcon.RUNNING if (state and state.process_info) else StatusIcon.STOPPED
            server_node = tree.add(f"{status_icon} {server.name}", style=self.theme.HIGHLIGHT)
            
            # Add server details
            server_node.add(f"Type: {server.type.value}")
            server_node.add(f"Transport: {server.transport.value}")
            
            if server.command:
                cmd = f"{server.command}"
                if server.args:
                    cmd += f" {' '.join(server.args)}"
                server_node.add(f"Command: {cmd}")
            
            if server.host and server.port:
                server_node.add(f"Address: {server.host}:{server.port}")
            
            # Add state information if available
            if state:
                if state.process_info:
                    proc_node = server_node.add("Process", style=self.theme.INFO)
                    proc_node.add(f"PID: {state.process_info.pid}")
                    proc_node.add(f"Status: {state.process_info.status}")
                
                if state.health_report:
                    health_node = server_node.add("Health", style=self.theme.ACCENT)
                    health_node.add(f"Status: {state.health_report.overall_status.value}")
                    health_node.add(f"Checks: {len(state.health_report.checks)}")
        
        self.console.print(tree)
    
    def print_health_report(self, report: HealthReport) -> None:
        """Print a detailed health report."""
        # Header
        status_icon = {
            HealthStatus.HEALTHY: StatusIcon.HEALTHY,
            HealthStatus.UNHEALTHY: StatusIcon.UNHEALTHY,
            HealthStatus.DEGRADED: StatusIcon.DEGRADED,
            HealthStatus.UNKNOWN: StatusIcon.UNKNOWN
        }.get(report.overall_status, StatusIcon.UNKNOWN)
        
        status_style = {
            HealthStatus.HEALTHY: self.theme.HEALTHY,
            HealthStatus.UNHEALTHY: self.theme.UNHEALTHY,
            HealthStatus.DEGRADED: self.theme.DEGRADED,
            HealthStatus.UNKNOWN: self.theme.UNKNOWN
        }.get(report.overall_status, self.theme.UNKNOWN)
        
        title = f"{status_icon} Health Report: {report.server_name}"
        self.print_section(title)
        
        # Overall status
        self.console.print(
            f"Overall Status: {report.overall_status.value.title()}",
            style=status_style
        )
        self.console.print(f"Report Duration: {report.duration_ms:.1f}ms")
        self.console.print(f"Timestamp: {report.timestamp}")
        self.console.print()
        
        # Individual checks
        if report.checks:
            table = Table(box=box.ROUNDED)
            table.add_column("Check", style=self.theme.HIGHLIGHT)
            table.add_column("Status", justify="center")
            table.add_column("Message", overflow="fold")
            table.add_column("Duration", justify="right")
            
            for check in report.checks:
                check_icon = {
                    HealthStatus.HEALTHY: StatusIcon.SUCCESS,
                    HealthStatus.UNHEALTHY: StatusIcon.ERROR,
                    HealthStatus.DEGRADED: StatusIcon.WARNING,
                    HealthStatus.UNKNOWN: StatusIcon.UNKNOWN
                }.get(check.status, StatusIcon.UNKNOWN)
                
                check_style = {
                    HealthStatus.HEALTHY: self.theme.SUCCESS,
                    HealthStatus.UNHEALTHY: self.theme.ERROR,
                    HealthStatus.DEGRADED: self.theme.WARNING,
                    HealthStatus.UNKNOWN: self.theme.UNKNOWN
                }.get(check.status, self.theme.UNKNOWN)
                
                table.add_row(
                    check.check_name,
                    f"{check_icon} {check.status.value}",
                    check.message,
                    f"{check.duration_ms:.1f}ms",
                    style=check_style
                )
            
            self.console.print(table)
    
    def print_platform_status(self, platform_status: Dict[str, Any]) -> None:
        """Print platform integration status."""
        self.print_section("Platform Integration Status")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Platform", style=self.theme.HIGHLIGHT)
        table.add_column("Installed", justify="center")
        table.add_column("Config Path", overflow="ellipsis", max_width=50)
        table.add_column("Servers", justify="right")
        
        for platform_name, status in platform_status.items():
            installed = status.get('installed', False)
            install_icon = StatusIcon.SUCCESS if installed else StatusIcon.ERROR
            install_style = self.theme.SUCCESS if installed else self.theme.ERROR
            
            config_path = status.get('config_path', '—')
            if config_path and config_path != '—':
                config_path = str(Path(config_path).name)  # Show just filename
            
            servers_count = status.get('servers_count', 0)
            
            table.add_row(
                platform_name.replace('_', ' ').title(),
                f"{install_icon} {'Yes' if installed else 'No'}",
                config_path,
                str(servers_count),
                style=install_style if installed else self.theme.MUTED
            )
        
        self.console.print(table)
    
    def print_validation_results(self, results: List[ValidationResult]) -> None:
        """Print validation results."""
        if not results:
            self.success("All validations passed")
            return
        
        has_errors = any(not result.valid for result in results)
        has_warnings = any(result.valid and result.warnings for result in results)
        
        # Summary
        if has_errors:
            self.error("Validation failed")
        elif has_warnings:
            self.warning("Validation passed with warnings")
        else:
            self.success("All validations passed")
        
        # Details table
        if results:
            table = Table(box=box.ROUNDED)
            table.add_column("Field", style=self.theme.HIGHLIGHT)
            table.add_column("Status", justify="center")
            table.add_column("Issues", overflow="fold")
            
            for result in results:
                if result.valid and not result.warnings:
                    status_icon = StatusIcon.SUCCESS
                    status_style = self.theme.SUCCESS
                    status_text = "Valid"
                    issues = "—"
                elif result.valid and result.warnings:
                    status_icon = StatusIcon.WARNING
                    status_style = self.theme.WARNING
                    status_text = "Warning"
                    issues = "; ".join(result.warnings)
                else:
                    status_icon = StatusIcon.ERROR
                    status_style = self.theme.ERROR
                    status_text = "Invalid"
                    issues = "; ".join(result.errors)
                
                table.add_row(
                    result.field,
                    f"{status_icon} {status_text}",
                    issues,
                    style=status_style
                )
            
            self.console.print(table)
    
    def create_progress(self, description: str = "Processing...") -> Progress:
        """Create a progress bar."""
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        )
        self._current_progress = progress
        return progress
    
    def start_spinner(self, text: str = "Working...") -> Status:
        """Start a spinner with text."""
        return Status(text, console=self.console, spinner="dots")
    
    def print_logs(
        self,
        log_lines: List[str],
        server_name: str,
        follow: bool = False,
        filter_pattern: Optional[str] = None
    ) -> None:
        """Print log output with formatting."""
        self.print_section(f"Logs: {server_name}")
        
        if filter_pattern:
            self.console.print(f"Filter: {filter_pattern}", style=self.theme.MUTED)
            self.console.print()
        
        if not log_lines:
            self.info("No logs available")
            return
        
        # Process and display log lines
        for line in log_lines:
            # Simple log level detection and coloring
            line_lower = line.lower()
            if 'error' in line_lower or 'critical' in line_lower:
                style = self.theme.ERROR
            elif 'warning' in line_lower or 'warn' in line_lower:
                style = self.theme.WARNING
            elif 'info' in line_lower:
                style = self.theme.INFO
            elif 'debug' in line_lower:
                style = self.theme.MUTED
            else:
                style = None
            
            self.console.print(line.rstrip(), style=style)
    
    def confirm(self, prompt: str, default: bool = False) -> bool:
        """Display a confirmation prompt."""
        default_char = "Y" if default else "N"
        other_char = "n" if default else "y"
        prompt_text = f"{prompt} [{default_char}/{other_char}]: "
        
        response = self.console.input(prompt_text).strip().lower()
        
        if not response:
            return default
        
        return response in ('y', 'yes', 'true', '1')
    
    def input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input with optional default."""
        if default:
            prompt_text = f"{prompt} [{default}]: "
        else:
            prompt_text = f"{prompt}: "
        
        response = self.console.input(prompt_text).strip()
        return response or default or ""
    
    def clear_screen(self) -> None:
        """Clear the console screen."""
        self.console.clear()
    
    def print_json(self, data: Any, title: Optional[str] = None) -> None:
        """Print JSON data with syntax highlighting."""
        if title:
            self.print_section(title)
        
        json_output = JSON.from_data(data, indent=2)
        self.console.print(json_output)
    
    def print_yaml(self, data: str, title: Optional[str] = None) -> None:
        """Print YAML data with syntax highlighting."""
        if title:
            self.print_section(title)
        
        yaml_output = Syntax(data, "yaml", theme="monokai", line_numbers=False)
        self.console.print(yaml_output)
    
    def get_console(self) -> Console:
        """Get the underlying Rich console."""
        return self.console


# Global output manager instance
output = RichOutputManager()


def set_output_manager(manager: RichOutputManager) -> None:
    """Set the global output manager."""
    global output
    output = manager


def get_output_manager() -> RichOutputManager:
    """Get the global output manager."""
    return output
