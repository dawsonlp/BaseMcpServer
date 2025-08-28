"""
Diagnostics and health checking commands for MCP Manager 3.0.

Provides comprehensive health monitoring, troubleshooting, and system diagnostics.
"""

import typer
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.text import Text

from mcp_manager.core.models import Server, HealthStatus, HealthReport, SystemInfo
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.health import HealthChecker
from mcp_manager.core.process_manager import ProcessManager
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError


app = typer.Typer(help="Health checking and diagnostics")
output = get_output_manager()
state = get_state_manager()
health_checker = HealthChecker()
process_manager = ProcessManager()


@app.command("check")
def health_check(
    name: Optional[str] = typer.Argument(None, help="Server name (checks all if not specified)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed health information"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Health check timeout in seconds"),
    format: str = typer.Option("human", "--format", "-f", help="Output format (human|json)"),
):
    """Perform health checks on servers."""
    try:
        if name:
            # Check specific server
            server = state.get_server(name)
            if not server:
                raise MCPManagerError(f"Server '{name}' not found")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
            ) as progress:
                
                task = progress.add_task(f"Checking health of '{name}'...", total=None)
                
                health_report = health_checker.check_server_health(name, timeout=timeout)
                
                progress.update(task, description=f"Health check complete for '{name}'")
            
            if format == "json":
                # JSON output
                json_data = {
                    "server": name,
                    "overall_status": health_report.overall_status.value,
                    "health_score": health_report.health_score,
                    "timestamp": health_report.timestamp.isoformat(),
                    "checks": []
                }
                
                for check in health_report.checks:
                    check_data = {
                        "name": check.name,
                        "status": check.status.value,
                        "message": check.message,
                        "response_time_ms": check.response_time_ms
                    }
                    if detailed:
                        check_data["details"] = check.details
                    json_data["checks"].append(check_data)
                
                output.console.print(json.dumps(json_data, indent=2))
                
            else:
                # Human-readable output
                status_color = {
                    HealthStatus.HEALTHY: "green",
                    HealthStatus.DEGRADED: "yellow",
                    HealthStatus.UNHEALTHY: "red",
                    HealthStatus.UNKNOWN: "dim"
                }.get(health_report.overall_status, "white")
                
                title = f"Health Report: {name} ([{status_color}]{health_report.overall_status.value}[/{status_color}])"
                
                table = Table(title=title)
                table.add_column("Check", style="cyan")
                table.add_column("Status", style="yellow")
                table.add_column("Message", style="white")
                if detailed:
                    table.add_column("Response Time", style="dim")
                
                for check in health_report.checks:
                    check_status_color = {
                        HealthStatus.HEALTHY: "green",
                        HealthStatus.DEGRADED: "yellow", 
                        HealthStatus.UNHEALTHY: "red",
                        HealthStatus.UNKNOWN: "dim"
                    }.get(check.status, "white")
                    
                    row_data = [
                        check.name,
                        f"[{check_status_color}]{check.status.value}[/{check_status_color}]",
                        check.message
                    ]
                    
                    if detailed:
                        response_time = f"{check.response_time_ms:.1f}ms" if check.response_time_ms else "N/A"
                        row_data.append(response_time)
                    
                    table.add_row(*row_data)
                
                output.console.print(table)
                
                # Show summary
                output.info(f"Health Score: {health_report.health_score:.1%}")
                if health_report.overall_status != HealthStatus.HEALTHY:
                    failed_checks = [c for c in health_report.checks if c.status != HealthStatus.HEALTHY]
                    output.warning(f"Failed Checks: {len(failed_checks)}/{len(health_report.checks)}")
        
        else:
            # Check all servers
            servers = state.get_servers()
            if not servers:
                output.info("No servers to check")
                return
            
            health_results = {}
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
            ) as progress:
                
                for server_name in servers.keys():
                    task = progress.add_task(f"Checking '{server_name}'...", total=None)
                    
                    try:
                        health_report = health_checker.check_server_health(server_name, timeout=timeout)
                        health_results[server_name] = health_report
                    except Exception as e:
                        output.warning(f"Health check failed for '{server_name}': {e}")
                        health_results[server_name] = None
                    
                    progress.remove_task(task)
            
            if format == "json":
                # JSON output for all servers
                json_data = {}
                for server_name, health_report in health_results.items():
                    if health_report:
                        json_data[server_name] = {
                            "overall_status": health_report.overall_status.value,
                            "health_score": health_report.health_score,
                            "timestamp": health_report.timestamp.isoformat(),
                            "check_count": len(health_report.checks)
                        }
                    else:
                        json_data[server_name] = {"error": "Health check failed"}
                
                output.console.print(json.dumps(json_data, indent=2))
                
            else:
                # Human-readable summary
                summary_table = Table(title="Health Check Summary")
                summary_table.add_column("Server", style="cyan")
                summary_table.add_column("Status", style="yellow")
                summary_table.add_column("Health Score", style="green")
                summary_table.add_column("Issues", style="red")
                
                healthy_count = 0
                total_count = len(health_results)
                
                for server_name, health_report in health_results.items():
                    if health_report:
                        status_color = {
                            HealthStatus.HEALTHY: "green",
                            HealthStatus.DEGRADED: "yellow",
                            HealthStatus.UNHEALTHY: "red",
                            HealthStatus.UNKNOWN: "dim"
                        }.get(health_report.overall_status, "white")
                        
                        failed_checks = len([c for c in health_report.checks if c.status != HealthStatus.HEALTHY])
                        
                        if health_report.overall_status == HealthStatus.HEALTHY:
                            healthy_count += 1
                        
                        summary_table.add_row(
                            server_name,
                            f"[{status_color}]{health_report.overall_status.value}[/{status_color}]",
                            f"{health_report.health_score:.1%}",
                            str(failed_checks) if failed_checks > 0 else "-"
                        )
                    else:
                        summary_table.add_row(
                            server_name,
                            "[red]ERROR[/red]",
                            "N/A",
                            "Check failed"
                        )
                
                output.console.print(summary_table)
                output.info(f"Overall: {healthy_count}/{total_count} servers healthy")
        
    except Exception as e:
        handle_error(e, "Failed to perform health check")


@app.command("monitor")
def monitor_health(
    name: Optional[str] = typer.Argument(None, help="Server name (monitors all if not specified)"),
    interval: int = typer.Option(5, "--interval", "-i", help="Check interval in seconds"),
    threshold: float = typer.Option(0.8, "--threshold", "-t", help="Health score threshold (0.0-1.0)"),
):
    """Continuously monitor server health."""
    try:
        servers_to_monitor = []
        if name:
            server = state.get_server(name)
            if not server:
                raise MCPManagerError(f"Server '{name}' not found")
            servers_to_monitor = [name]
        else:
            servers = state.get_servers()
            servers_to_monitor = list(servers.keys())
        
        if not servers_to_monitor:
            output.info("No servers to monitor")
            return
        
        output.info(f"Monitoring {len(servers_to_monitor)} server(s) every {interval}s")
        output.info(f"Health threshold: {threshold:.1%}")
        output.info("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                # Create monitoring table
                monitor_table = Table(title="Server Health Monitor")
                monitor_table.add_column("Server", style="cyan")
                monitor_table.add_column("Status", style="yellow")
                monitor_table.add_column("Health Score", style="green")
                monitor_table.add_column("Last Check", style="dim")
                
                alerts = []
                
                for server_name in servers_to_monitor:
                    try:
                        health_report = health_checker.check_server_health(server_name, timeout=10)
                        
                        status_color = {
                            HealthStatus.HEALTHY: "green",
                            HealthStatus.DEGRADED: "yellow",
                            HealthStatus.UNHEALTHY: "red",
                            HealthStatus.UNKNOWN: "dim"
                        }.get(health_report.overall_status, "white")
                        
                        score_color = "green" if health_report.health_score >= threshold else "red"
                        
                        monitor_table.add_row(
                            server_name,
                            f"[{status_color}]{health_report.overall_status.value}[/{status_color}]",
                            f"[{score_color}]{health_report.health_score:.1%}[/{score_color}]",
                            health_report.timestamp.strftime("%H:%M:%S")
                        )
                        
                        # Check for alerts
                        if health_report.health_score < threshold:
                            alerts.append(f"⚠️  {server_name}: Health score below threshold ({health_report.health_score:.1%})")
                        
                    except Exception as e:
                        monitor_table.add_row(
                            server_name,
                            "[red]ERROR[/red]",
                            "N/A",
                            time.strftime("%H:%M:%S")
                        )
                        alerts.append(f"❌ {server_name}: Health check failed")
                
                # Clear screen and display
                output.console.clear()
                output.console.print(monitor_table)
                
                # Show alerts
                if alerts:
                    output.console.print()
                    for alert in alerts:
                        output.console.print(alert, style="bold red")
                
                # Wait for next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            output.info("\nHealth monitoring stopped")
        
    except Exception as e:
        handle_error(e, "Failed to monitor health")


@app.command("troubleshoot")
def troubleshoot_server(
    name: str = typer.Argument(..., help="Server name"),
    auto_fix: bool = typer.Option(False, "--auto-fix", help="Attempt to automatically fix common issues"),
):
    """Troubleshoot server issues and provide recommendations."""
    try:
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        output.info(f"Troubleshooting server '{name}'...")
        
        # Collect diagnostic information
        issues = []
        recommendations = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            
            # Check 1: Server configuration
            task = progress.add_task("Checking configuration...", total=None)
            
            from mcp_manager.core.validation import validate_server_config
            validation_result = validate_server_config(server)
            
            if not validation_result.is_valid:
                for error in validation_result.errors:
                    issues.append(f"Configuration: {error.message}")
                    if error.suggestion:
                        recommendations.append(f"Config: {error.suggestion}")
            
            # Check 2: File system
            progress.update(task, description="Checking file system...")
            
            if server.is_local():
                if server.source_dir and not server.source_dir.exists():
                    issues.append(f"Source directory missing: {server.source_dir}")
                    recommendations.append("Reinstall server or update source directory path")
                
                if server.venv_dir and not server.venv_dir.exists():
                    issues.append(f"Virtual environment missing: {server.venv_dir}")
                    recommendations.append("Reinstall server to recreate virtual environment")
                
                # Check for main script
                main_script = server.get_main_script_path()
                if not main_script:
                    issues.append("No main.py script found in source directory")
                    recommendations.append("Ensure main.py exists in source directory or src/ subdirectory")
                elif not main_script.exists():
                    issues.append(f"Main script missing: {main_script}")
                    recommendations.append("Restore main.py file or update source directory")
            
            # Check 3: Process status
            progress.update(task, description="Checking process status...")
            
            server_state = state.get_server_state(name)
            if server_state and server_state.process_info:
                if not server_state.process_info.is_running():
                    issues.append("Process not running (may have crashed)")
                    recommendations.append("Check logs and restart server")
            
            # Check 4: Port availability (for SSE)
            if server.transport.value == "sse" and server.port:
                progress.update(task, description="Checking port availability...")
                
                import socket
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        result = sock.connect_ex(('localhost', server.port))
                        if result == 0:
                            # Port is in use
                            process_info = state.get_process(name)
                            if not process_info or not process_info.is_running():
                                issues.append(f"Port {server.port} is in use by another process")
                                recommendations.append(f"Change port or stop process using port {server.port}")
                except Exception as e:
                    issues.append(f"Failed to check port {server.port}: {e}")
            
            # Check 5: Dependencies (for local servers)
            if server.is_local() and server.venv_dir and server.venv_dir.exists():
                progress.update(task, description="Checking dependencies...")
                
                python_exe = server.get_python_executable()
                if python_exe and python_exe.exists():
                    try:
                        import subprocess
                        result = subprocess.run(
                            [str(python_exe), "-m", "pip", "list"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode != 0:
                            issues.append("Failed to list installed packages")
                            recommendations.append("Reinstall server dependencies")
                        
                    except subprocess.TimeoutExpired:
                        issues.append("Timeout checking dependencies")
                    except Exception as e:
                        issues.append(f"Error checking dependencies: {e}")
        
        # Display results
        if issues:
            issues_table = Table(title="Issues Found")
            issues_table.add_column("Issue", style="red")
            issues_table.add_column("Recommendation", style="cyan")
            
            for i, issue in enumerate(issues):
                recommendation = recommendations[i] if i < len(recommendations) else "Manual investigation required"
                issues_table.add_row(issue, recommendation)
            
            output.console.print(issues_table)
            
            # Auto-fix attempt
            if auto_fix:
                output.info("Attempting automatic fixes...")
                fixes_applied = 0
                
                # Auto-fix 1: Recreate virtual environment if missing
                if server.is_local() and server.venv_dir and not server.venv_dir.exists():
                    try:
                        import subprocess
                        result = subprocess.run(
                            ["python", "-m", "venv", str(server.venv_dir)],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            output.success("✓ Recreated virtual environment")
                            fixes_applied += 1
                    except Exception as e:
                        output.error(f"Failed to recreate virtual environment: {e}")
                
                # Auto-fix 2: Reinstall dependencies if requirements file exists
                if (server.is_local() and server.requirements_file and 
                    server.requirements_file.exists() and server.venv_dir and server.venv_dir.exists()):
                    try:
                        python_exe = server.get_python_executable()
                        if python_exe and python_exe.exists():
                            result = subprocess.run(
                                [str(python_exe), "-m", "pip", "install", "-r", str(server.requirements_file)],
                                capture_output=True,
                                text=True
                            )
                            if result.returncode == 0:
                                output.success("✓ Reinstalled dependencies")
                                fixes_applied += 1
                    except Exception as e:
                        output.error(f"Failed to reinstall dependencies: {e}")
                
                output.info(f"Applied {fixes_applied} automatic fixes")
                
                if fixes_applied > 0:
                    output.info("Re-run troubleshoot to verify fixes")
        else:
            output.success(f"No issues found with server '{name}'")
        
    except Exception as e:
        handle_error(e, f"Failed to troubleshoot server '{name}'")


@app.command("system")
def system_diagnostics():
    """Run system-wide diagnostics."""
    try:
        output.info("Running system diagnostics...")
        
        # Get system information
        system_info = state.get_system_info()
        
        # Create diagnostics table
        diag_table = Table(title="System Diagnostics")
        diag_table.add_column("Component", style="cyan")
        diag_table.add_column("Status", style="yellow")
        diag_table.add_column("Details", style="white")
        
        # Python version check
        python_status = "✓ OK" if system_info.python_version >= "3.8" else "⚠ Warning"
        diag_table.add_row("Python Version", python_status, system_info.python_version)
        
        # MCP Home directory
        mcp_home_status = "✓ OK" if system_info.mcp_home.exists() else "✗ Missing"
        diag_table.add_row("MCP Home", mcp_home_status, str(system_info.mcp_home))
        
        # Disk usage
        disk_status = "✓ OK" if system_info.disk_usage_mb < 1000 else "⚠ High Usage"
        diag_table.add_row("Disk Usage", disk_status, f"{system_info.disk_usage_mb} MB")
        
        # Server count
        server_status = "✓ OK" if system_info.total_servers > 0 else "ℹ No Servers"
        diag_table.add_row("Total Servers", server_status, str(system_info.total_servers))
        
        # Running servers
        running_status = "✓ OK" if system_info.running_servers == 0 else f"ℹ {system_info.running_servers} Running"
        diag_table.add_row("Running Servers", running_status, str(system_info.running_servers))
        
        # Platform integrations
        for platform in system_info.platforms:
            platform_status = "✓ Available" if platform.is_available() else "⚠ Not Available"
            details = f"{platform.server_count} servers"
            if platform.config_path:
                details += f" | {platform.config_path.name}"
            diag_table.add_row(platform.display_name, platform_status, details)
        
        output.console.print(diag_table)
        
        # Check for common issues
        issues = []
        
        if not system_info.mcp_home.exists():
            issues.append("MCP home directory is missing")
        
        if system_info.total_servers == 0:
            issues.append("No servers registered")
        
        if system_info.disk_usage_mb > 1000:
            issues.append("High disk usage - consider cleaning up old logs or backups")
        
        if not any(p.is_available() for p in system_info.platforms):
            issues.append("No platform integrations available")
        
        if issues:
            output.warning("System Issues Found:")
            for issue in issues:
                output.warning(f"  • {issue}")
        else:
            output.success("System diagnostics passed - no issues found")
        
    except Exception as e:
        handle_error(e, "Failed to run system diagnostics")


if __name__ == "__main__":
    app()
