"""
Core removal management for MCP Manager.

Orchestrates server removal across registry, platforms, and file cleanup.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

from mcp_manager.core.models import (
    Server,
    ServerState,
    RemovalResult,
    RemovalImpact,
    FileInfo,
    PlatformType
)
from mcp_manager.core.state import (
    get_state_manager,
    get_vscode_cline_settings_path,
    get_claude_desktop_settings_path
)
from mcp_manager.core.backup import get_backup_manager
from mcp_manager.core.cleanup import get_cleanup_manager


class RemovalManager:
    """Manages server removal operations across all layers."""
    
    def __init__(self):
        """Initialize removal manager."""
        self.state_manager = get_state_manager()
        self.backup_manager = get_backup_manager()
        self.cleanup_manager = get_cleanup_manager()
    
    def calculate_removal_impact(self, name: str) -> Optional[RemovalImpact]:
        """
        Calculate the impact of removing a server.
        
        Args:
            name: Server name
        
        Returns:
            RemovalImpact with analysis, or None if server not found
        """
        server = self.state_manager.get_server(name)
        if not server:
            return None
        
        # Check if server is running
        state = self.state_manager.get_server_state(name)
        is_running = state.is_running() if state else False
        
        # Check platform configurations
        platform_configs = self._get_platform_configurations(name)
        
        # Get files that would be removed
        files_to_remove = self._get_files_to_remove(server)
        
        # Create impact analysis
        impact = RemovalImpact(
            server_name=name,
            registry_exists=True,  # We know it exists since we found it
            platform_configs=platform_configs,
            files_to_remove=files_to_remove,
            total_size_mb=0.0,
            is_running=is_running,
            warnings=[]
        )
        
        # Calculate total size
        impact.calculate_total_size()
        
        # Add warnings
        if is_running:
            impact.warnings.append("Server is currently running")
        
        orphaned_platforms = [
            name for name, exists in platform_configs.items() if exists
        ]
        if orphaned_platforms:
            impact.warnings.append(
                f"Server configured in platforms: {', '.join(orphaned_platforms)}"
            )
        
        return impact
    
    def remove_server(
        self,
        name: str,
        from_registry: bool = True,
        from_platforms: Optional[List[str]] = None,
        cleanup_files: bool = True,
        force: bool = False,
        dry_run: bool = False
    ) -> RemovalResult:
        """
        Remove a server from all specified locations.
        
        Args:
            name: Server name to remove
            from_registry: Remove from mcp-manager registry
            from_platforms: List of platforms to remove from (None = all)
            cleanup_files: Whether to clean up associated files
            force: Force removal even if server is running
            dry_run: Don't actually perform removal
        
        Returns:
            RemovalResult with details of what was removed
        """
        result = RemovalResult(success=True, server_name=name)
        
        # Get server from registry
        server = self.state_manager.get_server(name)
        if not server:
            result.add_error(f"Server '{name}' not found in registry")
            return result
        
        # Check if server is running
        if not dry_run and not force:
            if self._check_if_running(name):
                result.add_error(
                    f"Server '{name}' is currently running. "
                    "Stop it first or use --force"
                )
                return result
        
        # Default to all platforms if not specified
        if from_platforms is None:
            from_platforms = ["cline", "claude"]
        
        # Remove from registry first (if requested)
        if from_registry and not dry_run:
            try:
                # Create backup before removal
                from mcp_manager.core.state import get_registry_file
                registry_file = get_registry_file()
                if registry_file.exists():
                    backup_path = self.backup_manager.create_backup(
                        registry_file,
                        prefix="before-removal"
                    )
                    result.add_backup(backup_path)
                
                # Remove from state manager
                self.state_manager.remove_server(name)
                result.add_removal("registry")
                
            except Exception as e:
                result.add_error(f"Failed to remove from registry: {e}")
                return result
        elif from_registry and dry_run:
            result.add_removal("registry (dry-run)")
        
        # Remove from platforms
        for platform in from_platforms:
            try:
                platform_result = self.remove_from_platform(
                    name,
                    PlatformType(platform),
                    dry_run=dry_run
                )
                if platform_result.success:
                    result.removed_from.extend(platform_result.removed_from)
                    result.backups_created.extend(platform_result.backups_created)
                else:
                    result.warnings.extend(platform_result.errors)
            except ValueError:
                result.add_warning(f"Unknown platform: {platform}")
        
        # Clean up files
        if cleanup_files:
            cleanup_result = self.cleanup_manager.cleanup_server_files(
                server,
                dry_run=dry_run
            )
            result.merge_cleanup_result(cleanup_result)
        
        # Cleanup old backups
        if not dry_run:
            try:
                self.backup_manager.cleanup_old_backups(keep_count=10)
            except Exception:
                # Non-critical, continue
                pass
        
        return result
    
    def remove_from_platform(
        self,
        name: str,
        platform: PlatformType,
        dry_run: bool = False
    ) -> RemovalResult:
        """
        Remove a server from a specific platform configuration.
        
        Args:
            name: Server name
            platform: Platform to remove from
            dry_run: Don't actually perform removal
        
        Returns:
            RemovalResult with details
        """
        result = RemovalResult(success=True, server_name=name)
        
        # Get platform config path
        if platform == PlatformType.CLINE:
            config_path = get_vscode_cline_settings_path()
            platform_name = "cline"
        elif platform == PlatformType.CLAUDE_DESKTOP:
            config_path = get_claude_desktop_settings_path()
            platform_name = "claude"
        else:
            result.add_error(f"Unknown platform: {platform}")
            return result
        
        # Check if config file exists
        if not config_path.exists():
            result.add_warning(f"{platform_name} config file not found")
            return result
        
        try:
            # Read current config
            config = json.loads(config_path.read_text())
            
            # Check if server exists in config
            if "mcpServers" not in config or name not in config["mcpServers"]:
                result.add_warning(f"Server '{name}' not found in {platform_name} config")
                return result
            
            if not dry_run:
                # Create backup
                backup_path = self.backup_manager.create_backup(
                    config_path,
                    prefix="before-removal"
                )
                result.add_backup(backup_path)
                
                # Remove server from config
                del config["mcpServers"][name]
                
                # Write updated config
                config_path.write_text(json.dumps(config, indent=2))
                result.add_removal(platform_name)
            else:
                result.add_removal(f"{platform_name} (dry-run)")
        
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON in {platform_name} config: {e}")
        except Exception as e:
            result.add_error(f"Failed to remove from {platform_name}: {e}")
        
        return result
    
    def remove_from_registry(
        self,
        name: str,
        cleanup_files: bool = False,
        dry_run: bool = False
    ) -> RemovalResult:
        """
        Remove a server from registry only, leaving platforms untouched.
        
        Args:
            name: Server name
            cleanup_files: Whether to also clean up files
            dry_run: Don't actually perform removal
        
        Returns:
            RemovalResult with details
        """
        result = RemovalResult(success=True, server_name=name)
        
        # Get server
        server = self.state_manager.get_server(name)
        if not server:
            result.add_error(f"Server '{name}' not found in registry")
            return result
        
        # Check for orphaned platform configs
        platform_configs = self._get_platform_configurations(name)
        orphaned = [name for name, exists in platform_configs.items() if exists]
        
        if orphaned:
            result.add_warning(
                f"Server will remain configured in: {', '.join(orphaned)}. "
                "These platforms may show errors after registry removal."
            )
        
        if not dry_run:
            # Create backup
            from mcp_manager.core.state import get_registry_file
            registry_file = get_registry_file()
            if registry_file.exists():
                try:
                    backup_path = self.backup_manager.create_backup(
                        registry_file,
                        prefix="before-removal"
                    )
                    result.add_backup(backup_path)
                except Exception as e:
                    result.add_error(f"Failed to create backup: {e}")
                    return result
            
            # Remove from registry
            try:
                self.state_manager.remove_server(name)
                result.add_removal("registry")
            except Exception as e:
                result.add_error(f"Failed to remove from registry: {e}")
                return result
            
            # Clean up files if requested
            if cleanup_files:
                cleanup_result = self.cleanup_manager.cleanup_server_files(
                    server,
                    dry_run=False
                )
                result.merge_cleanup_result(cleanup_result)
        else:
            result.add_removal("registry (dry-run)")
            if cleanup_files:
                cleanup_result = self.cleanup_manager.cleanup_server_files(
                    server,
                    dry_run=True
                )
                result.merge_cleanup_result(cleanup_result)
        
        return result
    
    def find_orphaned_servers(
        self,
        platform: Optional[PlatformType] = None
    ) -> Dict[str, List[str]]:
        """
        Find servers in platform configs that aren't in the registry.
        
        Args:
            platform: Specific platform to check (None = all)
        
        Returns:
            Dict mapping platform name to list of orphaned server names
        """
        orphaned = {}
        
        # Get all registered servers
        registered_servers = set(self.state_manager.get_servers().keys())
        
        # Check platforms
        platforms_to_check = []
        if platform:
            platforms_to_check = [platform]
        else:
            platforms_to_check = [PlatformType.CLINE, PlatformType.CLAUDE_DESKTOP]
        
        for plat in platforms_to_check:
            if plat == PlatformType.CLINE:
                config_path = get_vscode_cline_settings_path()
                platform_name = "cline"
            else:
                config_path = get_claude_desktop_settings_path()
                platform_name = "claude"
            
            if not config_path.exists():
                continue
            
            try:
                config = json.loads(config_path.read_text())
                platform_servers = set(config.get("mcpServers", {}).keys())
                
                # Find servers in platform but not in registry
                orphans = platform_servers - registered_servers
                if orphans:
                    orphaned[platform_name] = list(orphans)
            
            except (json.JSONDecodeError, OSError):
                # Skip if can't read config
                pass
        
        return orphaned
    
    def _check_if_running(self, name: str) -> bool:
        """Check if a server is currently running."""
        state = self.state_manager.get_server_state(name)
        return state.is_running() if state else False
    
    def _get_platform_configurations(self, name: str) -> Dict[str, bool]:
        """Get which platforms have this server configured."""
        configs = {}
        
        # Check Cline
        cline_path = get_vscode_cline_settings_path()
        if cline_path.exists():
            try:
                config = json.loads(cline_path.read_text())
                configs["cline"] = name in config.get("mcpServers", {})
            except (json.JSONDecodeError, OSError):
                configs["cline"] = False
        else:
            configs["cline"] = False
        
        # Check Claude Desktop
        claude_path = get_claude_desktop_settings_path()
        if claude_path.exists():
            try:
                config = json.loads(claude_path.read_text())
                configs["claude"] = name in config.get("mcpServers", {})
            except (json.JSONDecodeError, OSError):
                configs["claude"] = False
        else:
            configs["claude"] = False
        
        return configs
    
    def _get_files_to_remove(self, server: Server) -> List[FileInfo]:
        """Get list of files that would be removed for a server."""
        return self.cleanup_manager._get_server_files(server)


# Global removal manager instance
_removal_manager: Optional[RemovalManager] = None


def get_removal_manager() -> RemovalManager:
    """Get the global removal manager instance."""
    global _removal_manager
    if _removal_manager is None:
        _removal_manager = RemovalManager()
    return _removal_manager
