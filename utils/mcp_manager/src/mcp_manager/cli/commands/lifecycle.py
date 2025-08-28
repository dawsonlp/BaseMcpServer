"""
Server lifecycle management commands for MCP Manager 3.0.

Handles starting, stopping, restarting, and monitoring MCP servers.
"""

import typer
import time
import signal
from pathlib import Path
from typing import Optional, List
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.table import Table

from mcp_manager.core.models import Server, TransportType, ProcessStatus
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.process_manager import ProcessManager
from mcp_manager.core.health import HealthChecker
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError
from mcp_manager.cli.common.validation import CLIValidator


app = typer.Typer(help="Server lifecycle management")
output = get_output_manager()
validator = CLIValidator()
state = get_state_manager()
process_manager = ProcessManager()
health_checker = HealthChecker()


@app.command("start")
def start_server(
    name: str = typer.Argument(..., help="Server name to start"),
    transport: Optional[str] = typer.Option(None, "--transport", "-t", help="Override transport protocol"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Override port for SSE transport"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
):
    """Start a server."""
    try:
        # Get server configuration
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found. Install it first.")
        
        # Check if already running
        server_state = state.get_server_state(name)
        if server_state and server_state.is_running():
            output.info(f"Server '{name}' is already running")
            return
        
        # Override transport if specified
        if transport:
            try:
                server.transport = TransportType(transport)
            except ValueError:
                raise MCPManagerError(f"Invalid transport: {transport}")
        
        # Override port if specified
        if port:
            server.port = port
        
        # Validate configuration before starting
        from mcp_manager.core.validation import validate_server_config
        validation_result = validate_server_config(server)
        if not validation_result.is_valid:
            output.error("Server configuration is invalid:")
            for error in validation_result.errors:
                output.error(f"  • {error.message}")
            raise typer.Exit(1)
        
        # Start server with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            
            task = progress.add_task("Starting server...", total=None)
            
            # Start the server process
            process_info = process_manager.start_server(server)
            
            progress.update(task, description="Verifying startup...")
            time.sleep(2)  # Give server time to start
            
            # Verify server started successfully
            if not process_info.is_running():
                raise MCPManagerError("Server failed to start or crashed immediately")
        
        output.success(f"Server '{name}' started successfully")
        output.info(f"PID: {process_info.pid}")
        output.info(f"Transport: {server.transport.value}")
        if server.port:
            output.info(f"Port: {server.port}")
        
        if not background:
            output.info("Press Ctrl+C to stop the server")
            try:
                # Keep running until interrupted
                while process_info.is_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                output.info("\nStopping server...")
                stop_server(name, force=False)
        
    except Exception as e:
        handle_error(e, f"Failed to start server '{name}'")


@app.command("stop")
def stop_server(
    name: str = typer.Argument(..., help="Server name to stop"),
    force: bool = typer.Option(False, "--force", "-f", help="Force stop if graceful shutdown fails"),
):
    """Stop a running server."""
    try:
        # Get server configuration
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Check if running
        server_state = state.get_server_state(name)
        if not server_state or not server_state.is_running():
            output.info(f"Server '{name}' is not running")
            return
        
        # Stop the server
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            
            task = progress.add_task("Stopping server...", total=None)
            
            success = process_manager.stop_server(name, force=force)
            
            if success:
                progress.update(task, description="Server stopped")
                output.success(f"Server '{name}' stopped successfully")
            else:
                raise MCPManagerError("Failed to stop server gracefully")
        
    except Exception as e:
        handle_error(e, f"Failed to stop server '{name}'")


@app.command("restart")
def restart_server(
    name: str = typer.Argument(..., help="Server name to restart"),
    transport: Optional[str] = typer.Option(None, "--transport", "-t", help="Override transport protocol"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Override port for SSE transport"),
):
    """Restart a server."""
    try:
        # Get server configuration
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Stop if running
        server_state = state.get_server_state(name)
        if server_state and server_state.is_running():
            output.info(f"Stopping server '{name}'...")
            stop_server(name, force=False)
            time.sleep(1)  # Brief pause between stop and start
        
        # Start the server
        output.info(f"Starting server '{name}'...")
        start_server(name, transport, port, background=True)
        
    except Exception as e:
        handle_error(e, f"Failed to restart server '{name}'")


@app.command("status")
def show_server_status(
    name: str = typer.Argument(..., help="Server name"),
):
    """Show detailed status for a specific server."""
    try:
        # Get server configuration
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Get server state
        server_state = state.get_server_state(name)
        
        # Create status table
        table = Table(title=f"Server Status: {name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", name)
        table.add_row("Type", server.server_type.value)
        table.add_row("Transport", server.transport.value)
        
        if server.port:
            table.add_row("Port", str(server.port))
        
        if server_state:
            table.add_row("Status", server_state.process_status.value)
            table.add_row("Health", server_state.health_status.value)
            
            if server_state.process_info:
                table.add_row("PID", str(server_state.process_info.pid))
                if server_state.uptime:
                    table.add_row("Uptime", str(server_state.uptime))
                if server_state.memory_usage_mb:
                    table.add_row("Memory", f"{server_state.memory_usage_mb} MB")
        else:
            table.add_row("Status", "Stopped")
        
        if server.is_local():
            table.add_row("Source", str(server.source_dir) if server.source_dir else "N/A")
            table.add_row("Virtual Env", str(server.venv_dir) if server.venv_dir else "N/A")
        else:
            table.add_row("URL", str(server.url) if server.url else "N/A")
        
        output.console.print(table)
        
    except Exception as e:
        handle_error(e, f"Failed to get status for server '{name}'")


@app.command("logs")
def show_logs(
    name: str = typer.Argument(..., help="Server name"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    level: str = typer.Option("info", "--level", help="Minimum log level"),
):
    """Show server logs."""
    try:
        # Get server configuration
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Get log file path
        from mcp_manager.core.state import get_logs_dir
        log_file = get_logs_dir() / f"{name}.log"
        
        if not log_file.exists():
            output.info(f"No log file found for server '{name}'")
            return
        
        if follow:
            output.info(f"Following logs for '{name}' (Ctrl+C to stop)...")
            try:
                # Simple tail -f implementation
                with log_file.open("r") as f:
                    # Seek to end minus some lines
                    f.seek(0, 2)  # Go to end
                    pos = f.tell()
                    line_count = 0
                    
                    # Read backwards to get last N lines
                    while pos > 0 and line_count < lines:
                        pos -= 1
                        f.seek(pos)
                        if f.read(1) == '\n':
                            line_count += 1
                    
                    # Print existing lines
                    for line in f:
                        output.console.print(line.rstrip())
                    
                    # Follow new lines
                    while True:
                        line = f.readline()
                        if line:
                            output.console.print(line.rstrip())
                        else:
                            time.sleep(0.1)
                            
            except KeyboardInterrupt:
                output.info("Stopped following logs")
        else:
            # Show last N lines
            with log_file.open("r") as f:
                lines_list = f.readlines()[-lines:]
                for line in lines_list:
                    output.console.print(line.rstrip())
        
    except Exception as e:
        handle_error(e, f"Failed to show logs for server '{name}'")


@app.command("kill")
def kill_server(
    name: str = typer.Argument(..., help="Server name to kill"),
):
    """Forcefully kill a server process."""
    try:
        # Get server configuration
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Get process info
        process_info = state.get_process(name)
        if not process_info:
            output.info(f"Server '{name}' is not running")
            return
        
        # Kill the process
        try:
            import os
            os.kill(process_info.pid, signal.SIGKILL)
            
            # Clean up process tracking
            state.remove_process(name)
            
            output.success(f"Server '{name}' killed (PID: {process_info.pid})")
            
        except ProcessLookupError:
            output.info(f"Server '{name}' process no longer exists")
            state.remove_process(name)
        
    except Exception as e:
        handle_error(e, f"Failed to kill server '{name}'")


if __name__ == "__main__":
    app()
