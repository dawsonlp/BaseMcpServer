"""
Advanced operations for MCP Manager 3.0.

Provides specialized operations for development, maintenance, and system administration.
"""

import typer
import shutil
import json
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text

from mcp_manager.core.models import Server, ServerState, SystemInfo
from mcp_manager.core.state import get_state_manager, get_logs_dir, get_config_dir, get_mcp_home
from mcp_manager.core.process_manager import ProcessManager
from mcp_manager.core.platforms import PlatformManager
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError
from mcp_manager.cli.common.validation import CLIValidator


app = typer.Typer(help="Advanced operations")
output = get_output_manager()
validator = CLIValidator()
state = get_state_manager()
process_manager = ProcessManager()
platform_manager = PlatformManager()


@app.command("cleanup")
def cleanup_system(
    logs: bool = typer.Option(True, "--logs/--no-logs", help="Clean up old log files"),
    backups: bool = typer.Option(True, "--backups/--no-backups", help="Clean up old backup files"),
    processes: bool = typer.Option(True, "--processes/--no-processes", help="Clean up stale process entries"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be cleaned without making changes"),
    age_days: int = typer.Option(30, "--age-days", help="Age in days for files to be considered old"),
):
    """Clean up old files and stale data."""
    try:
        cleanup_stats = {
            "logs_cleaned": 0,
            "backups_cleaned": 0,
            "processes_cleaned": 0,
            "space_freed_mb": 0
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ) as progress:
            
            total_steps = sum([logs, backups, processes])
            main_task = progress.add_task("Cleaning up system...", total=total_steps)
            
            # Clean up old log files
            if logs:
                progress.update(main_task, description="Cleaning log files...")
                
                logs_dir = get_logs_dir()
                if logs_dir.exists():
                    cutoff_date = datetime.now() - timedelta(days=age_days)
                    
                    for log_file in logs_dir.glob("*.log*"):
                        try:
                            # Check file age
                            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                            if file_time < cutoff_date:
                                file_size = log_file.stat().st_size
                                
                                if dry_run:
                                    output.info(f"Would delete: {log_file.name} ({file_size // 1024} KB)")
                                else:
                                    log_file.unlink()
                                    output.info(f"Deleted log: {log_file.name}")
                                
                                cleanup_stats["logs_cleaned"] += 1
                                cleanup_stats["space_freed_mb"] += file_size // (1024 * 1024)
                        
                        except Exception as e:
                            output.warning(f"Failed to process log file {log_file}: {e}")
                
                progress.advance(main_task)
            
            # Clean up old backup files
            if backups:
                progress.update(main_task, description="Cleaning backup files...")
                
                backup_dir = get_config_dir() / "backups"
                if backup_dir.exists():
                    # Keep only the latest 10 backups
                    backup_files = sorted(backup_dir.glob("mcp_config_backup_*.yaml"))
                    if len(backup_files) > 10:
                        old_backups = backup_files[:-10]
                        
                        for backup_file in old_backups:
                            try:
                                file_size = backup_file.stat().st_size
                                
                                if dry_run:
                                    output.info(f"Would delete: {backup_file.name} ({file_size // 1024} KB)")
                                else:
                                    backup_file.unlink()
                                    output.info(f"Deleted backup: {backup_file.name}")
                                
                                cleanup_stats["backups_cleaned"] += 1
                                cleanup_stats["space_freed_mb"] += file_size // (1024 * 1024)
                            
                            except Exception as e:
                                output.warning(f"Failed to delete backup {backup_file}: {e}")
                
                progress.advance(main_task)
            
            # Clean up stale process entries
            if processes:
                progress.update(main_task, description="Cleaning stale processes...")
                
                cleaned_processes = state.cleanup_stale_processes()
                cleanup_stats["processes_cleaned"] = len(cleaned_processes)
                
                for process_name in cleaned_processes:
                    output.info(f"Cleaned stale process entry: {process_name}")
                
                progress.advance(main_task)
        
        # Display summary
        summary_table = Table(title="Cleanup Summary")
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Items Cleaned", style="green")
        summary_table.add_column("Details", style="white")
        
        summary_table.add_row("Log Files", str(cleanup_stats["logs_cleaned"]), f"Older than {age_days} days")
        summary_table.add_row("Backup Files", str(cleanup_stats["backups_cleaned"]), "Keeping latest 10")
        summary_table.add_row("Process Entries", str(cleanup_stats["processes_cleaned"]), "Stale processes removed")
        
        if cleanup_stats["space_freed_mb"] > 0:
            summary_table.add_row("Space Freed", f"{cleanup_stats['space_freed_mb']} MB", "Approximate")
        
        output.console.print(summary_table)
        
        if dry_run:
            output.info("Dry run complete - no actual changes made")
        else:
            total_cleaned = sum(cleanup_stats[key] for key in ["logs_cleaned", "backups_cleaned", "processes_cleaned"])
            if total_cleaned > 0:
                output.success(f"Cleanup complete - {total_cleaned} items processed")
            else:
                output.info("No cleanup needed")
        
    except Exception as e:
        handle_error(e, "Failed to cleanup system")


@app.command("reset")
def reset_system(
    confirm: bool = typer.Option(False, "--confirm", help="Confirm the reset operation"),
    keep_servers: bool = typer.Option(False, "--keep-servers", help="Keep server registrations"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before reset"),
):
    """Reset MCP Manager to initial state (DANGEROUS)."""
    try:
        if not confirm:
            output.error("This operation will reset MCP Manager to its initial state!")
            output.error("All server registrations, logs, and configurations will be lost!")
            output.info("Use --confirm flag if you really want to proceed")
            output.info("Use --keep-servers to preserve server registrations")
            raise typer.Exit(1)
        
        # Create backup if requested
        if backup:
            output.info("Creating backup before reset...")
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path.home() / f"mcp_manager_reset_backup_{timestamp}.yaml"
            
            try:
                # Export current configuration
                all_servers = state.get_servers()
                backup_data = {
                    "reset_backup": {
                        "version": "3.0",
                        "created_at": datetime.now().isoformat(),
                        "reason": "Pre-reset backup"
                    },
                    "servers": {}
                }
                
                for name, server in all_servers.items():
                    server_data = server.model_dump(mode='json')
                    for key, value in server_data.items():
                        if isinstance(value, Path):
                            server_data[key] = str(value)
                    backup_data["servers"][name] = server_data
                
                backup_file.write_text(yaml.dump(backup_data, default_flow_style=False))
                output.success(f"Backup created: {backup_file}")
                
            except Exception as e:
                output.warning(f"Failed to create backup: {e}")
                output.info("Continuing with reset anyway...")
        
        # Stop all running servers first
        output.info("Stopping all running servers...")
        servers = state.get_servers()
        for server_name in servers.keys():
            try:
                server_state = state.get_server_state(server_name)
                if server_state and server_state.is_running():
                    process_manager.stop_server(server_name, force=True)
                    output.info(f"Stopped server: {server_name}")
            except Exception as e:
                output.warning(f"Failed to stop server {server_name}: {e}")
        
        # Reset components
        mcp_home = get_mcp_home()
        
        if keep_servers:
            # Remove only specific directories, keep servers
            dirs_to_remove = [
                get_logs_dir(),
                get_config_dir() / "processes.json",
                get_config_dir() / "backups"
            ]
            
            output.info("Resetting MCP Manager (keeping server registrations)...")
            
            for item in dirs_to_remove:
                try:
                    if item.exists():
                        if item.is_dir():
                            shutil.rmtree(item)
                            output.info(f"Removed directory: {item.name}")
                        else:
                            item.unlink()
                            output.info(f"Removed file: {item.name}")
                except Exception as e:
                    output.warning(f"Failed to remove {item}: {e}")
        
        else:
            # Complete reset - remove everything
            output.info("Performing complete reset...")
            
            if mcp_home.exists():
                try:
                    shutil.rmtree(mcp_home)
                    output.info("Removed MCP home directory")
                except Exception as e:
                    output.error(f"Failed to remove MCP home directory: {e}")
                    raise typer.Exit(1)
        
        # Reinitialize directory structure
        from mcp_manager.core.state import create_directory_structure
        create_directory_structure()
        
        output.success("Reset complete!")
        if keep_servers:
            output.info("Server registrations have been preserved")
        else:
            output.info("MCP Manager has been reset to initial state")
        
        if backup:
            output.info(f"Backup available at: {backup_file}")
        
    except Exception as e:
        handle_error(e, "Failed to reset system")


@app.command("migrate")
def migrate_data(
    from_version: str = typer.Option("2.0", "--from", help="Source version to migrate from"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be migrated without making changes"),
):
    """Migrate data from older MCP Manager versions."""
    try:
        output.info(f"Migrating data from MCP Manager {from_version}...")
        
        if from_version == "2.0":
            # Migrate from version 2.0 structure
            old_home = Path.home() / ".mcp_servers"
            new_home = get_mcp_home()
            
            if not old_home.exists():
                output.info(f"No data found to migrate from {old_home}")
                return
            
            if new_home.exists() and any(new_home.iterdir()):
                output.warning("Current MCP Manager data exists. Migration may overwrite existing data.")
                confirm = typer.confirm("Continue with migration?")
                if not confirm:
                    output.info("Migration cancelled")
                    return
            
            migration_stats = {
                "servers_migrated": 0,
                "configs_migrated": 0,
                "files_migrated": 0
            }
            
            if dry_run:
                output.info("Dry run - showing what would be migrated:")
                
                # Check for servers
                servers_dir = old_home / "servers"
                if servers_dir.exists():
                    server_dirs = [d for d in servers_dir.iterdir() if d.is_dir()]
                    output.info(f"  Would migrate {len(server_dirs)} servers:")
                    for server_dir in server_dirs:
                        output.info(f"    • {server_dir.name}")
                    migration_stats["servers_migrated"] = len(server_dirs)
                
                # Check for configs
                config_dir = old_home / "config"
                if config_dir.exists():
                    config_files = list(config_dir.glob("*.json"))
                    output.info(f"  Would migrate {len(config_files)} config files")
                    migration_stats["configs_migrated"] = len(config_files)
                
            else:
                # Perform actual migration
                output.info("Performing migration...")
                
                # Create new directory structure
                from mcp_manager.core.state import create_directory_structure
                create_directory_structure()
                
                # Migrate servers
                servers_dir = old_home / "servers"
                if servers_dir.exists():
                    new_servers_dir = new_home / "servers"
                    
                    for server_dir in servers_dir.iterdir():
                        if server_dir.is_dir():
                            try:
                                dest_dir = new_servers_dir / server_dir.name
                                shutil.copytree(server_dir, dest_dir, dirs_exist_ok=True)
                                output.info(f"Migrated server: {server_dir.name}")
                                migration_stats["servers_migrated"] += 1
                            except Exception as e:
                                output.warning(f"Failed to migrate server {server_dir.name}: {e}")
                
                # Migrate configurations
                config_dir = old_home / "config"
                if config_dir.exists():
                    new_config_dir = new_home / "config"
                    
                    for config_file in config_dir.glob("*.json"):
                        try:
                            dest_file = new_config_dir / config_file.name
                            shutil.copy2(config_file, dest_file)
                            output.info(f"Migrated config: {config_file.name}")
                            migration_stats["configs_migrated"] += 1
                        except Exception as e:
                            output.warning(f"Failed to migrate config {config_file.name}: {e}")
                
                output.success("Migration completed successfully!")
            
            # Show summary
            summary_table = Table(title="Migration Summary")
            summary_table.add_column("Category", style="cyan")
            summary_table.add_column("Count", style="green")
            
            summary_table.add_row("Servers", str(migration_stats["servers_migrated"]))
            summary_table.add_row("Config Files", str(migration_stats["configs_migrated"]))
            
            output.console.print(summary_table)
            
            if not dry_run and migration_stats["servers_migrated"] > 0:
                output.info("Note: You may need to reconfigure server settings for version 3.0 compatibility")
        
        else:
            output.error(f"Migration from version {from_version} is not supported")
            output.info("Supported versions: 2.0")
        
    except Exception as e:
        handle_error(e, "Failed to migrate data")


@app.command("analyze")
def analyze_performance(
    name: Optional[str] = typer.Argument(None, help="Server name (analyzes all if not specified)"),
    duration: int = typer.Option(60, "--duration", "-d", help="Analysis duration in seconds"),
    interval: int = typer.Option(5, "--interval", "-i", help="Sampling interval in seconds"),
):
    """Analyze server performance and resource usage."""
    try:
        servers_to_analyze = []
        if name:
            server = state.get_server(name)
            if not server:
                raise MCPManagerError(f"Server '{name}' not found")
            servers_to_analyze = [name]
        else:
            servers = state.get_servers()
            # Only analyze running servers
            for server_name in servers.keys():
                server_state = state.get_server_state(server_name)
                if server_state and server_state.is_running():
                    servers_to_analyze.append(server_name)
        
        if not servers_to_analyze:
            output.info("No running servers to analyze")
            return
        
        output.info(f"Analyzing {len(servers_to_analyze)} server(s) for {duration}s...")
        
        # Collect performance data
        performance_data = {server_name: [] for server_name in servers_to_analyze}
        
        samples_to_take = duration // interval
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ) as progress:
            
            task = progress.add_task("Collecting performance data...", total=samples_to_take)
            
            import time
            for sample in range(samples_to_take):
                timestamp = datetime.now()
                
                for server_name in servers_to_analyze:
                    try:
                        server_state = state.get_server_state(server_name)
                        if server_state and server_state.process_info:
                            memory_mb = server_state.process_info.get_memory_usage()
                            
                            sample_data = {
                                "timestamp": timestamp,
                                "memory_mb": memory_mb,
                                "uptime": server_state.uptime.total_seconds() if server_state.uptime else 0
                            }
                            
                            performance_data[server_name].append(sample_data)
                        
                    except Exception as e:
                        output.warning(f"Failed to collect data for {server_name}: {e}")
                
                progress.advance(task)
                
                if sample < samples_to_take - 1:  # Don't sleep after last sample
                    time.sleep(interval)
        
        # Analyze and display results
        analysis_table = Table(title="Performance Analysis")
        analysis_table.add_column("Server", style="cyan")
        analysis_table.add_column("Avg Memory (MB)", style="green")
        analysis_table.add_column("Max Memory (MB)", style="yellow")
        analysis_table.add_column("Memory Trend", style="blue")
        analysis_table.add_column("Uptime", style="white")
        
        for server_name, data_points in performance_data.items():
            if not data_points:
                analysis_table.add_row(server_name, "N/A", "N/A", "N/A", "N/A")
                continue
            
            # Calculate statistics
            memory_values = [dp["memory_mb"] for dp in data_points if dp["memory_mb"] is not None]
            
            if memory_values:
                avg_memory = sum(memory_values) / len(memory_values)
                max_memory = max(memory_values)
                
                # Calculate trend (simple linear regression slope)
                if len(memory_values) > 1:
                    n = len(memory_values)
                    x_vals = list(range(n))
                    sum_x = sum(x_vals)
                    sum_y = sum(memory_values)
                    sum_xy = sum(x * y for x, y in zip(x_vals, memory_values))
                    sum_x2 = sum(x * x for x in x_vals)
                    
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    
                    if slope > 0.1:
                        trend = "↗ Increasing"
                    elif slope < -0.1:
                        trend = "↘ Decreasing"
                    else:
                        trend = "→ Stable"
                else:
                    trend = "→ Single sample"
                
                # Get latest uptime
                latest_uptime = data_points[-1]["uptime"]
                uptime_str = str(timedelta(seconds=int(latest_uptime)))
                
                analysis_table.add_row(
                    server_name,
                    f"{avg_memory:.1f}",
                    f"{max_memory:.1f}",
                    trend,
                    uptime_str
                )
            else:
                analysis_table.add_row(server_name, "N/A", "N/A", "N/A", "N/A")
        
        output.console.print(analysis_table)
        
        # Provide recommendations
        output.info("\nPerformance Recommendations:")
        
        for server_name, data_points in performance_data.items():
            if not data_points:
                continue
            
            memory_values = [dp["memory_mb"] for dp in data_points if dp["memory_mb"] is not None]
            if not memory_values:
                continue
            
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            
            recommendations = []
            
            if avg_memory > 500:
                recommendations.append("High average memory usage - consider optimization")
            
            if max_memory > 1000:
                recommendations.append("Very high peak memory usage - investigate memory leaks")
            
            if len(memory_values) > 1:
                memory_variance = sum((x - avg_memory) ** 2 for x in memory_values) / len(memory_values)
                if memory_variance > 10000:  # High variance
                    recommendations.append("Unstable memory usage - investigate periodic operations")
            
            if recommendations:
                output.info(f"  {server_name}:")
                for rec in recommendations:
                    output.info(f"    • {rec}")
            else:
                output.info(f"  {server_name}: Performance looks good")
        
    except Exception as e:
        handle_error(e, "Failed to analyze performance")


@app.command("export-diagnostics")
def export_diagnostics(
    output_file: Path = typer.Argument(..., help="Output file path"),
    include_logs: bool = typer.Option(False, "--include-logs", help="Include recent log entries"),
    include_configs: bool = typer.Option(True, "--include-configs", help="Include server configurations"),
):
    """Export comprehensive diagnostic information."""
    try:
        output.info("Collecting diagnostic information...")
        
        diagnostic_data = {
            "export_info": {
                "version": "3.0",
                "exported_at": datetime.now().isoformat(),
                "hostname": None,
                "platform": None
            },
            "system_info": {},
            "servers": {},
            "platform_status": {},
            "recent_logs": {} if include_logs else None
        }
        
        # System information
        try:
            import platform
            import socket
            diagnostic_data["export_info"]["hostname"] = socket.gethostname()
            diagnostic_data["export_info"]["platform"] = platform.platform()
            
            system_info = state.get_system_info()
            diagnostic_data["system_info"] = {
                "python_version": system_info.python_version,
                "platform": system_info.platform,
                "mcp_home": str(system_info.mcp_home),
                "total_servers": system_info.total_servers,
                "running_servers": system_info.running_servers,
                "disk_usage_mb": system_info.disk_usage_mb
            }
        except Exception as e:
            output.warning(f"Failed to collect system info: {e}")
        
        # Server information
        try:
            servers = state.get_servers()
            server_states = state.get_all_server_states()
            
            for name, server in servers.items():
                server_data = {
                    "configuration": server.model_dump(mode='json') if include_configs else {"name": name},
                    "state": None
                }
                
                # Convert Path objects to strings
                if include_configs:
                    for key, value in server_data["configuration"].items():
                        if isinstance(value, Path):
                            server_data["configuration"][key] = str(value)
                        
                    # Remove sensitive data
                    server_data["configuration"].pop("api_key", None)
                
                # Add state information
                server_state = server_states.get(name)
                if server_state:
                    server_data["state"] = {
                        "process_status": server_state.process_status.value,
                        "health_status": server_state.health_status.value,
                        "health_score": server_state.health_score,
                        "uptime": str(server_state.uptime) if server_state.uptime else None,
                        "memory_mb": server_state.memory_usage_mb,
                        "last_error": server_state.last_error
                    }
                
                diagnostic_data["servers"][name] = server_data
        except Exception as e:
            output.warning(f"Failed to collect server info: {e}")
        
        # Platform status
        try:
            system_info = state.get_system_info()
            for platform in system_info.platforms:
                diagnostic_data["platform_status"][platform.name] = {
                    "display_name": platform.display_name,
                    "installed": platform.installed,
                    "available": platform.is_available(),
                    "config_path": str(platform.config_path) if platform.config_path else None,
                    "server_count": platform.server_count,
                    "sync_status": platform.sync_status.value
                }
        except Exception as e:
            output.warning(f"Failed to collect platform status: {e}")
        
        # Recent logs
        if include_logs:
            try:
                logs_dir = get_logs_dir()
                if logs_dir.exists():
                    for log_file in logs_dir.glob("*.log"):
                        try:
                            # Get last 100 lines of each log file
                            lines = log_file.read_text().strip().split('\n')[-100:]
                            diagnostic_data["recent_logs"][log_file.name] = lines
                        except Exception as e:
                            diagnostic_data["recent_logs"][log_file.name] = [f"Error reading log: {e}"]
            except Exception as e:
                output.warning(f"Failed to collect logs: {e}")
        
        # Write diagnostic file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if output_file.suffix.lower() == '.json':
            output_file.write_text(json.dumps(diagnostic_data, indent=2, default=str))
        else:
            output_file.write_text(yaml.dump(diagnostic_data, default_flow_style=False))
        
        output.success(f"Diagnostic information exported to: {output_file}")
        output.info(f"File size: {output_file.stat().st_size // 1024} KB")
        
        # Show summary
        summary_info = []
        summary_info.append(f"System info: {'✓' if diagnostic_data['system_info'] else '✗'}")
        summary_info.append(f"Servers: {len(diagnostic_data['servers'])}")
        summary_info.append(f"Platforms: {len(diagnostic_data['platform_status'])}")
        if include_logs:
            log_count = len(diagnostic_data.get("recent_logs", {}))
            summary_info.append(f"Log files: {log_count}")
        
        output.info("Export contents: " + " | ".join(summary_info))
        
    except Exception as e:
        handle_error(e, "Failed to export diagnostics")


if __name__ == "__main__":
    app()
