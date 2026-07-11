"""
Removal commands for MCP Manager.

Provides commands for removing MCP servers from various locations.
"""

import typer
from typing import Optional
from rich.panel import Panel
from rich.table import Table

from mcp_manager.core.removal import get_removal_manager
from mcp_manager.core.models import PlatformType
from mcp_manager.cli.common.output import get_output_manager
from mcp_manager.cli.common.errors import handle_error, MCPManagerError


output = get_output_manager()
removal_manager = get_removal_manager()


def format_size(size_mb: float) -> str:
    """Format size in human-readable format."""
    if size_mb < 0.01:
        return "< 0.01 MB"
    elif size_mb < 1:
        return f"{size_mb:.2f} MB"
    elif size_mb < 1024:
        return f"{size_mb:.1f} MB"
    else:
        return f"{size_mb / 1024:.2f} GB"


def confirm_removal(
    server_name: str,
    impact: object,
    require_typing: bool = True
) -> bool:
    """
    Show removal impact and get user confirmation.
    
    Args:
        server_name: Name of server to remove
        impact: RemovalImpact object
        require_typing: If True, require user to type server name
    
    Returns:
        True if user confirmed, False otherwise
    """
    # Build impact message
    lines = []
    lines.append(f"⚠️  About to remove server '[bold]{server_name}[/bold]'")
    lines.append("")
    lines.append("This will remove:")
    
    if impact.registry_exists:
        lines.append("  • mcp-manager registry entry")
    
    for platform, exists in impact.platform_configs.items():
        if exists:
            lines.append(f"  • {platform.title()} configuration")
    
    if impact.files_to_remove:
        lines.append(f"  • {len(impact.files_to_remove)} files/directories")
        for file_info in impact.files_to_remove[:3]:  # Show first 3
            if file_info.exists:
                lines.append(f"    - {file_info.type}: {format_size(file_info.size_mb)}")
        if len(impact.files_to_remove) > 3:
            lines.append(f"    ... and {len(impact.files_to_remove) - 3} more")
    
    lines.append("")
    lines.append(f"Total space to recover: [bold green]{format_size(impact.total_size_mb)}[/bold green]")
    
    if impact.warnings:
        lines.append("")
        lines.append("[bold yellow]Warnings:[/bold yellow]")
        for warning in impact.warnings:
            lines.append(f"  ⚠  {warning}")
    
    output.console.print(Panel(
        "\n".join(lines),
        title="⚠️  Removal Confirmation",
        expand=False
    ))
    
    if require_typing:
        # Require typing server name for extra safety
        typed_name = typer.prompt(
            f"\nType the server name '{server_name}' to confirm",
            default=""
        )
        return typed_name == server_name
    else:
        # Simple yes/no confirmation
        return typer.confirm("\nContinue?", default=False)


def show_removal_result(result: object):
    """Display removal result in formatted output."""
    if result.success:
        output.success(f"Successfully removed server '{result.server_name}'")
        
        if result.removed_from:
            output.info("Removed from:")
            for location in result.removed_from:
                output.info(f"  • {location}")
        
        if result.cleaned_files:
            output.info(f"Cleaned up {len(result.cleaned_files)} files")
        
        if result.space_freed_mb > 0:
            output.success(f"Space recovered: {format_size(result.space_freed_mb)}")
        
        if result.backups_created:
            output.info(f"Created {len(result.backups_created)} backup(s)")
        
        if result.warnings:
            output.warning("Warnings:")
            for warning in result.warnings:
                output.warning(f"  • {warning}")
    else:
        output.error(f"Failed to remove server '{result.server_name}'")
        for error in result.errors:
            output.error(f"  • {error}")


def show_dry_run_result(result: object, server_name: str):
    """Display dry-run result."""
    output.info("🔍 Dry run mode - no changes made")
    output.console.print()
    
    # Build table of what would be removed
    table = Table(title=f"Removal Plan for '{server_name}'")
    table.add_column("Location", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Details", style="white")
    
    for location in result.removed_from:
        table.add_row(location, "Would remove", "")
    
    if result.cleaned_files:
        table.add_row(
            "Files",
            "Would cleanup",
            f"{len(result.cleaned_files)} files ({format_size(result.space_freed_mb)})"
        )
    
    output.console.print(table)
    output.console.print()
    output.info(f"Run without --dry-run to proceed")


def remove_server(
    name: str = typer.Argument(..., help="Server name to remove"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed"),
    keep_files: bool = typer.Option(False, "--keep-files", help="Keep files (only remove configs)"),
):
    """
    Remove a server completely from all locations.
    
    This removes the server from:
    - mcp-manager registry
    - VS Code Cline configuration
    - Claude Desktop configuration
    - All associated files (unless --keep-files)
    """
    try:
        # Calculate impact
        impact = removal_manager.calculate_removal_impact(name)
        if not impact:
            raise MCPManagerError(f"Server '{name}' not found")
        
        # Show dry-run if requested
        if dry_run:
            result = removal_manager.remove_server(
                name,
                cleanup_files=not keep_files,
                dry_run=True
            )
            show_dry_run_result(result, name)
            return
        
        # Get confirmation unless --yes
        if not yes:
            if not confirm_removal(name, impact, require_typing=True):
                output.info("Removal cancelled")
                return
        
        # Perform removal
        result = removal_manager.remove_server(
            name,
            cleanup_files=not keep_files,
            dry_run=False
        )
        
        # Show result
        show_removal_result(result)
        
        if not result.success:
            raise typer.Exit(1)
    
    except Exception as e:
        handle_error(e, f"Failed to remove server '{name}'")
