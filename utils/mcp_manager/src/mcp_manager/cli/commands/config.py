"""
Configuration management commands for MCP Manager 3.0.

Handles server configuration, platform synchronization, and settings management.
"""

import typer
import json
import yaml
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from mcp_manager.core.models import Server, PlatformType, TransportType, ServerType, InstallationType
from mcp_manager.core.state import get_state_manager
from mcp_manager.core.platforms import PlatformManager
from mcp_manager.core.validation import validate_server_config
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError
from mcp_manager.cli.common.validation import CLIValidator


app = typer.Typer(help="Configuration management")
output = get_output_manager()
validator = CLIValidator()
state = get_state_manager()
platform_manager = PlatformManager()


@app.command("edit")
def edit_server_config(
    name: str = typer.Argument(..., help="Server name"),
    transport: Optional[TransportType] = typer.Option(None, "--transport", "-t", help="Set transport protocol"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Set port (for SSE transport)"),
    enabled: Optional[bool] = typer.Option(None, "--enabled", help="Enable/disable server"),
    add_auto_approve: List[str] = typer.Option([], "--add-auto-approve", help="Add auto-approve tools"),
    remove_auto_approve: List[str] = typer.Option([], "--remove-auto-approve", help="Remove auto-approve tools"),
    clear_auto_approve: bool = typer.Option(False, "--clear-auto-approve", help="Clear all auto-approve tools"),
):
    """Edit server configuration."""
    try:
        # Get existing server
        server = state.get_server(name)
        if not server:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Track changes
        changes = []
        
        # Update transport
        if transport is not None:
            old_transport = server.transport
            server.transport = transport
            changes.append(f"Transport: {old_transport.value} → {transport.value}")
        
        # Update port
        if port is not None:
            old_port = server.port
            server.port = port
            changes.append(f"Port: {old_port} → {port}")
        
        # Update enabled status
        if enabled is not None:
            old_enabled = server.enabled
            server.enabled = enabled
            changes.append(f"Enabled: {old_enabled} → {enabled}")
        
        # Handle auto-approve changes
        if clear_auto_approve:
            if server.auto_approve:
                changes.append("Auto-approve: Cleared all tools")
                server.auto_approve = []
        
        if add_auto_approve:
            for tool in add_auto_approve:
                if tool not in server.auto_approve:
                    server.auto_approve.append(tool)
                    changes.append(f"Auto-approve: Added '{tool}'")
        
        if remove_auto_approve:
            for tool in remove_auto_approve:
                if tool in server.auto_approve:
                    server.auto_approve.remove(tool)
                    changes.append(f"Auto-approve: Removed '{tool}'")
        
        if not changes:
            output.info(f"No changes specified for server '{name}'")
            return
        
        # Validate configuration
        validation_result = validate_server_config(server)
        if not validation_result.is_valid:
            output.error("Configuration validation failed:")
            for error in validation_result.errors:
                output.error(f"  • {error.message}")
            raise typer.Exit(1)
        
        # Save changes
        state.update_server(server)
        
        output.success(f"Updated configuration for server '{name}'")
        for change in changes:
            output.info(f"  • {change}")
        
    except Exception as e:
        handle_error(e, f"Failed to edit configuration for server '{name}'")


@app.command("validate")
def validate_config(
    name: Optional[str] = typer.Argument(None, help="Server name (optional, validates all if not specified)"),
):
    """Validate server configurations."""
    try:
        if name:
            # Validate specific server
            server = state.get_server(name)
            if not server:
                raise MCPManagerError(f"Server '{name}' not found")
            
            validation_result = validate_server_config(server)
            
            if validation_result.is_valid:
                output.success(f"Server '{name}' configuration is valid")
            else:
                output.error(f"Server '{name}' configuration is invalid:")
                for error in validation_result.errors:
                    output.error(f"  • {error.message}")
                    if error.suggestion:
                        output.info(f"    Suggestion: {error.suggestion}")
            
            # Show warnings if any
            if validation_result.warnings:
                output.warning(f"Warnings for server '{name}':")
                for warning in validation_result.warnings:
                    output.warning(f"  • {warning.message}")
                    if warning.suggestion:
                        output.info(f"    Suggestion: {warning.suggestion}")
        
        else:
            # Validate all servers
            servers = state.get_servers()
            if not servers:
                output.info("No servers to validate")
                return
            
            valid_count = 0
            total_count = len(servers)
            
            for server_name, server in servers.items():
                validation_result = validate_server_config(server)
                
                if validation_result.is_valid:
                    valid_count += 1
                    output.success(f"✓ {server_name}")
                else:
                    output.error(f"✗ {server_name}:")
                    for error in validation_result.errors:
                        output.error(f"    • {error.message}")
            
            output.info(f"Validation complete: {valid_count}/{total_count} servers valid")
        
    except Exception as e:
        handle_error(e, "Failed to validate configuration")


@app.command("sync")
def sync_platforms(
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Specific platform to sync (cline|claude)"),
    direction: str = typer.Option("both", "--direction", "-d", help="Sync direction (import|export|both)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be synced without making changes"),
):
    """Synchronize server configurations with AI platforms."""
    try:
        servers = state.get_servers()
        
        # Determine platforms to sync
        if platform:
            if platform == "cline":
                platforms = [PlatformType.CLINE]
            elif platform == "claude":
                platforms = [PlatformType.CLAUDE_DESKTOP]
            else:
                raise MCPManagerError(f"Unknown platform: {platform}")
        else:
            platforms = list(PlatformType)
        
        # Show what will be synced
        if dry_run:
            output.info("Dry run mode - showing what would be synced:")
            
            for platform_type in platforms:
                output.info(f"\nPlatform: {platform_type.value}")
                
                if direction in ["import", "both"]:
                    imported_servers = platform_manager.sync_from_platform(platform_type)
                    if imported_servers:
                        output.info(f"  Would import {len(imported_servers)} servers:")
                        for server in imported_servers:
                            output.info(f"    • {server.name}")
                    else:
                        output.info(f"  No servers to import from {platform_type.value}")
                
                if direction in ["export", "both"]:
                    output.info(f"  Would export {len(servers)} servers to {platform_type.value}")
            
            return
        
        # Perform actual sync
        sync_results = {}
        
        for platform_type in platforms:
            platform_name = platform_type.value
            output.info(f"Syncing with {platform_name}...")
            
            try:
                if direction in ["import", "both"]:
                    # Import from platform
                    imported_servers = platform_manager.sync_from_platform(platform_type)
                    if imported_servers:
                        for server in imported_servers:
                            # Check if server already exists
                            existing = state.get_server(server.name)
                            if existing:
                                output.warning(f"Server '{server.name}' already exists, skipping import")
                            else:
                                state.add_server(server)
                                output.success(f"Imported server '{server.name}' from {platform_name}")
                        
                        sync_results[f"{platform_name}_imported"] = len(imported_servers)
                    else:
                        output.info(f"No servers to import from {platform_name}")
                        sync_results[f"{platform_name}_imported"] = 0
                
                if direction in ["export", "both"]:
                    # Export to platform
                    server_list = list(servers.values())
                    success = platform_manager.sync_to_platform(platform_type, server_list)
                    
                    if success:
                        output.success(f"Exported {len(server_list)} servers to {platform_name}")
                        sync_results[f"{platform_name}_exported"] = len(server_list)
                    else:
                        output.error(f"Failed to export servers to {platform_name}")
                        sync_results[f"{platform_name}_exported"] = 0
                
            except Exception as e:
                output.error(f"Failed to sync with {platform_name}: {e}")
                sync_results[f"{platform_name}_error"] = str(e)
        
        # Show summary
        output.info("\nSync Summary:")
        for key, value in sync_results.items():
            if key.endswith("_error"):
                output.error(f"  {key}: {value}")
            else:
                output.info(f"  {key}: {value}")
        
    except Exception as e:
        handle_error(e, "Failed to sync platforms")


@app.command("export")
def export_config(
    output_file: Path = typer.Argument(..., help="Output file path"),
    format: str = typer.Option("yaml", "--format", "-f", help="Export format (yaml|json)"),
    include_sensitive: bool = typer.Option(False, "--include-sensitive", help="Include sensitive data like API keys"),
    servers: List[str] = typer.Option([], "--server", "-s", help="Specific servers to export (all if not specified)"),
):
    """Export server configurations to file."""
    try:
        all_servers = state.get_servers()
        
        # Filter servers if specified
        if servers:
            filtered_servers = {}
            for server_name in servers:
                if server_name in all_servers:
                    filtered_servers[server_name] = all_servers[server_name]
                else:
                    output.warning(f"Server '{server_name}' not found, skipping")
            export_servers = filtered_servers
        else:
            export_servers = all_servers
        
        if not export_servers:
            raise MCPManagerError("No servers to export")
        
        # Convert to export format
        export_data = {
            "version": "3.0",
            "exported_at": state.get_system_info().last_updated.isoformat(),
            "servers": {}
        }
        
        for name, server in export_servers.items():
            server_data = server.model_dump(mode='json')
            
            # Convert Path objects to strings
            for key, value in server_data.items():
                if isinstance(value, Path):
                    server_data[key] = str(value)
            
            # Remove sensitive data if requested
            if not include_sensitive:
                server_data.pop('api_key', None)
                server_data.pop('environment', None)
            
            export_data["servers"][name] = server_data
        
        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            output_file.write_text(json.dumps(export_data, indent=2, default=str))
        else:
            output_file.write_text(yaml.dump(export_data, default_flow_style=False))
        
        output.success(f"Exported {len(export_servers)} servers to {output_file}")
        output.info(f"Format: {format}")
        if not include_sensitive:
            output.info("Sensitive data excluded")
        
    except Exception as e:
        handle_error(e, "Failed to export configuration")


@app.command("import")
def import_config(
    input_file: Path = typer.Argument(..., help="Input file path"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing servers"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be imported without making changes"),
):
    """Import server configurations from file."""
    try:
        if not input_file.exists():
            raise MCPManagerError(f"Input file does not exist: {input_file}")
        
        # Read and parse file
        content = input_file.read_text()
        
        try:
            if input_file.suffix.lower() == '.json':
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)
        except Exception as e:
            raise MCPManagerError(f"Failed to parse input file: {e}")
        
        # Validate format
        if not isinstance(data, dict) or "servers" not in data:
            raise MCPManagerError("Invalid configuration file format")
        
        servers_data = data["servers"]
        if not isinstance(servers_data, dict):
            raise MCPManagerError("Invalid servers data format")
        
        # Process servers
        import_results = {
            "imported": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for name, server_data in servers_data.items():
            try:
                # Check if server exists
                existing = state.get_server(name)
                if existing and not overwrite:
                    output.warning(f"Server '{name}' already exists, skipping (use --overwrite to replace)")
                    import_results["skipped"] += 1
                    continue
                
                if dry_run:
                    output.info(f"Would import server '{name}'")
                    continue
                
                # Create server object
                server = Server.model_validate(server_data)
                
                # Validate configuration
                validation_result = validate_server_config(server)
                if not validation_result.is_valid:
                    output.error(f"Server '{name}' configuration is invalid:")
                    for error in validation_result.errors:
                        output.error(f"  • {error.message}")
                    import_results["errors"] += 1
                    continue
                
                # Add or update server
                if existing:
                    state.update_server(server)
                    output.success(f"Updated server '{name}'")
                else:
                    state.add_server(server)
                    output.success(f"Imported server '{name}'")
                
                import_results["imported"] += 1
                
            except Exception as e:
                output.error(f"Failed to import server '{name}': {e}")
                import_results["errors"] += 1
        
        # Show summary
        if dry_run:
            output.info(f"Dry run complete - would import {len(servers_data)} servers")
        else:
            output.info("Import Summary:")
            output.info(f"  Imported: {import_results['imported']}")
            output.info(f"  Skipped: {import_results['skipped']}")
            output.info(f"  Errors: {import_results['errors']}")
        
    except Exception as e:
        handle_error(e, "Failed to import configuration")


@app.command("backup")
def backup_config(
    backup_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Backup directory (default: ~/.config/mcp-manager/backups)"),
):
    """Create a backup of all configurations."""
    try:
        # Determine backup directory
        if not backup_dir:
            from mcp_manager.core.state import get_config_dir
            backup_dir = get_config_dir() / "backups"
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped backup file
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"mcp_config_backup_{timestamp}.yaml"
        
        # Export all configurations
        all_servers = state.get_servers()
        if not all_servers:
            output.info("No servers to backup")
            return
        
        # Create backup data
        backup_data = {
            "backup_info": {
                "version": "3.0",
                "created_at": datetime.now().isoformat(),
                "server_count": len(all_servers)
            },
            "servers": {}
        }
        
        for name, server in all_servers.items():
            server_data = server.model_dump(mode='json')
            
            # Convert Path objects to strings
            for key, value in server_data.items():
                if isinstance(value, Path):
                    server_data[key] = str(value)
            
            backup_data["servers"][name] = server_data
        
        # Write backup file
        backup_file.write_text(yaml.dump(backup_data, default_flow_style=False))
        
        output.success(f"Created backup: {backup_file}")
        output.info(f"Backed up {len(all_servers)} servers")
        
        # Clean up old backups (keep last 10)
        backup_files = sorted(backup_dir.glob("mcp_config_backup_*.yaml"))
        if len(backup_files) > 10:
            for old_backup in backup_files[:-10]:
                old_backup.unlink()
                output.info(f"Removed old backup: {old_backup.name}")
        
    except Exception as e:
        handle_error(e, "Failed to create backup")


@app.command("cline")
def configure_cline(
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before updating"),
):
    """Configure VS Code Cline integration."""
    try:
        # Get all servers
        all_servers = state.get_servers()
        if not all_servers:
            output.warning("No servers found to configure")
            return

        # Get Cline settings path
        settings_path = _get_cline_settings_path()
        settings_dir = settings_path.parent
        settings_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing settings
        if settings_path.exists() and backup:
            from datetime import datetime
            backup_path = settings_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}")
            import shutil
            shutil.copy2(settings_path, backup_path)
            output.info(f"Backed up existing settings to: {backup_path}")

        # Load existing settings or create new
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except json.JSONDecodeError:
                output.warning("Existing settings file is not valid JSON. Creating new settings.")
                settings = {}
        else:
            settings = {}

        # Ensure mcpServers exists
        if "mcpServers" not in settings:
            settings["mcpServers"] = {}

        # Configure each server
        configured_count = 0
        for name, server in all_servers.items():
            if server.server_type != ServerType.LOCAL:
                output.warning(f"Skipping remote server '{name}' - Cline only supports local servers")
                continue

            try:
                if server.installation_type == InstallationType.PIPX:
                    # Handle pipx-installed servers
                    if not server.venv_dir:
                        output.error(f"venv_dir not set for pipx server '{name}', skipping")
                        continue

                    import sys
                    executable_path = server.venv_dir / "bin" / name  # Use server name as executable
                    if not executable_path.exists():
                        output.error(f"Executable '{executable_path}' not found for server '{name}', skipping")
                        continue

                    settings["mcpServers"][name] = {
                        "command": str(executable_path),
                        "args": ["stdio"],
                        "disabled": not server.enabled if hasattr(server, 'enabled') else False,
                        "autoApprove": server.auto_approve or [],
                    }

                else:
                    # Handle venv-installed servers
                    if not server.venv_dir or not server.source_dir:
                        output.error(f"Required directories not set for server '{name}', skipping")
                        continue

                    import sys
                    python_exe = server.venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
                    main_script = server.source_dir / "main.py"

                    if not python_exe.exists():
                        output.error(f"Python executable not found for server '{name}' at '{python_exe}', skipping")
                        continue

                    if not main_script.exists():
                        output.error(f"main.py not found for server '{name}' at '{main_script}', skipping")
                        continue

                    settings["mcpServers"][name] = {
                        "command": str(python_exe),
                        "args": [str(main_script), "stdio"],
                        "options": {
                            "cwd": str(server.source_dir),
                            "env": {"PYTHONPATH": str(server.source_dir)},
                        },
                        "disabled": not server.enabled if hasattr(server, 'enabled') else False,
                        "autoApprove": server.auto_approve or [],
                    }

                configured_count += 1
                output.success(f"Configured server '{name}' for Cline")

            except Exception as e:
                output.error(f"Failed to configure server '{name}': {e}")

        # Save settings
        settings_path.write_text(json.dumps(settings, indent=2))
        
        output.success(f"Updated Cline settings at: {settings_path}")
        output.info(f"Configured {configured_count} servers")
        output.info("You may need to restart VS Code for the changes to take effect.")

    except Exception as e:
        handle_error(e, "Failed to configure Cline")


@app.command("claude")
def configure_claude_desktop(
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before updating"),
):
    """Configure Claude Desktop integration."""
    try:
        # Get all servers
        all_servers = state.get_servers()
        if not all_servers:
            output.warning("No servers found to configure")
            return

        # Get Claude Desktop settings path
        settings_path = _get_claude_desktop_settings_path()
        settings_dir = settings_path.parent
        settings_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing settings
        if settings_path.exists() and backup:
            from datetime import datetime
            backup_path = settings_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}")
            import shutil
            shutil.copy2(settings_path, backup_path)
            output.info(f"Backed up existing settings to: {backup_path}")

        # Load existing settings or create new
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except json.JSONDecodeError:
                output.warning("Existing settings file is not valid JSON. Creating new settings.")
                settings = {}
        else:
            settings = {}

        # Ensure mcpServers exists
        if "mcpServers" not in settings:
            settings["mcpServers"] = {}

        # Configure each server
        configured_count = 0
        for name, server in all_servers.items():
            if server.server_type != ServerType.LOCAL:
                output.warning(f"Skipping remote server '{name}' - Claude Desktop only supports local servers")
                continue

            try:
                if server.installation_type == InstallationType.PIPX:
                    # Handle pipx-installed servers
                    if not server.venv_dir:
                        output.error(f"venv_dir not set for pipx server '{name}', skipping")
                        continue

                    executable_path = server.venv_dir / "bin" / name  # Use server name as executable
                    if not executable_path.exists():
                        output.error(f"Executable '{executable_path}' not found for server '{name}', skipping")
                        continue

                    settings["mcpServers"][name] = {
                        "command": str(executable_path),
                        "args": ["stdio"]
                    }

                else:
                    # Handle venv-installed servers
                    if not server.venv_dir or not server.source_dir:
                        output.error(f"Required directories not set for server '{name}', skipping")
                        continue

                    import sys
                    python_exe = server.venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
                    main_script = server.source_dir / "main.py"

                    if not python_exe.exists():
                        output.error(f"Python executable not found for server '{name}' at '{python_exe}', skipping")
                        continue

                    if not main_script.exists():
                        output.error(f"main.py not found for server '{name}' at '{main_script}', skipping")
                        continue

                    settings["mcpServers"][name] = {
                        "command": str(python_exe),
                        "args": [str(main_script), "stdio"],
                        "env": {"PYTHONPATH": str(server.source_dir)}
                    }

                configured_count += 1
                output.success(f"Configured server '{name}' for Claude Desktop")

            except Exception as e:
                output.error(f"Failed to configure server '{name}': {e}")

        # Save settings
        settings_path.write_text(json.dumps(settings, indent=2))
        
        output.success(f"Updated Claude Desktop settings at: {settings_path}")
        output.info(f"Configured {configured_count} servers")
        output.info("You may need to restart Claude Desktop for the changes to take effect.")

    except Exception as e:
        handle_error(e, "Failed to configure Claude Desktop")


def _get_cline_settings_path() -> Path:
    """Get the VS Code Cline settings path."""
    import os
    home = Path.home()
    
    if os.name == 'nt':  # Windows
        return home / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    elif sys.platform == 'darwin':  # macOS
        return home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    else:  # Linux
        return home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"


def _get_claude_desktop_settings_path() -> Path:
    """Get the Claude Desktop settings path."""
    import os
    home = Path.home()
    
    if os.name == 'nt':  # Windows
        return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == 'darwin':  # macOS
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return home / ".config" / "Claude" / "claude_desktop_config.json"


if __name__ == "__main__":
    app()
