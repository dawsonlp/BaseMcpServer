# MCP Manager - Removal Commands Design Document

**Version:** 1.0  
**Date:** September 29, 2025  
**Status:** Design Approved - Ready for Implementation

## Executive Summary

This document defines the design for removal commands in mcp-manager, addressing the current gap where servers can be installed but not properly removed. The design provides a hierarchical, safe, and user-friendly approach to removing MCP servers at different configuration layers.

## Current State Analysis

### Configuration Layers

mcp-manager currently manages MCP server configurations across three layers:

1. **mcp-manager Registry** (`~/.config/mcp-manager/config/servers.json`)
   - Central state management
   - Tracks all server metadata
   - Source of truth for server information

2. **VS Code Cline** (Platform-specific)
   - macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   - Linux: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   - Windows: `%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

3. **Claude Desktop** (Platform-specific)
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%/Claude/claude_desktop_config.json`

### Current Gaps

- ✅ Installing servers at all layers
- ✅ Syncing servers to platforms
- ✅ Listing and viewing servers
- ❌ **No CLI commands for removal**
- ❌ **No selective platform removal**
- ❌ **No cleanup of associated files**
- ❌ **`StateManager.remove_server()` exists but unexposed**

## Design Objectives

1. **Safety First**: Prevent accidental data loss
2. **Granular Control**: Target specific configuration layers
3. **Clear Feedback**: Show exactly what will be affected
4. **Consistency**: Follow existing command patterns
5. **Discoverability**: Intuitive command structure

## Command Structure

### Command Group Hierarchy

```
mcp-manager remove
├── server              # Complete removal
├── from-cline          # Platform-specific removal
├── from-claude         # Platform-specific removal
├── from-registry       # Registry-only removal
├── servers             # Bulk removal
└── orphaned            # Cleanup orphaned entries
```

### Detailed Command Specifications

#### 1. Complete Server Removal

**Command:**
```bash
mcp-manager remove server <name> [options]
```

**Aliases:**
- `mcp-manager remove <name>` (shorthand)
- `mcp-manager uninstall <name>` (alternative)

**Options:**
- `--yes, -y`: Skip confirmation prompt
- `--dry-run`: Show what would be removed without making changes
- `--keep-files`: Remove from configs but keep files (venv, logs)
- `--force`: Force removal even if server is running

**Behavior:**
1. Checks if server exists in registry
2. Stops server if running (unless `--force`)
3. Removes from mcp-manager registry
4. Removes from all configured platforms (Cline, Claude Desktop)
5. Cleans up associated files (unless `--keep-files`):
   - Virtual environment
   - Log files
   - Configuration files
6. Shows summary of what was removed

**Exit Codes:**
- 0: Success
- 1: Server not found
- 2: Server is running (use --force)
- 3: Removal failed

**Example Output:**
```
✓ Stopped server 'my-server'
✓ Removed from mcp-manager registry
✓ Removed from VS Code Cline configuration
✓ Removed from Claude Desktop configuration
✓ Cleaned up virtual environment (45.2 MB)
✓ Cleaned up log files (1.3 MB)

Successfully removed server 'my-server' from all locations
Total space recovered: 46.5 MB
```

#### 2. Platform-Specific Removal

**Commands:**
```bash
mcp-manager remove from-cline <name> [options]
mcp-manager remove from-claude <name> [options]
```

**Options:**
- `--yes, -y`: Skip confirmation prompt
- `--dry-run`: Show what would be removed

**Behavior:**
1. Checks if server exists in specified platform config
2. Removes server entry from platform config file
3. Creates backup of config file (timestamped)
4. Leaves registry and other platforms untouched
5. Shows summary of changes

**Use Cases:**
- Temporarily disable server in one platform while keeping it configured
- Clean up platform-specific configurations
- Testing platform-specific behavior

**Example Output:**
```
✓ Backed up Cline settings to: cline_mcp_settings.backup.20250929141530.json
✓ Removed 'my-server' from VS Code Cline configuration

Server remains in:
• mcp-manager registry
• Claude Desktop configuration (if configured)
```

#### 3. Registry-Only Removal

**Command:**
```bash
mcp-manager remove from-registry <name> [options]
```

**Options:**
- `--yes, -y`: Skip confirmation prompt
- `--dry-run`: Show what would be removed
- `--cleanup-files`: Also remove associated files

**Behavior:**
1. Checks if server exists in registry
2. Removes from mcp-manager registry only
3. Leaves platform configurations untouched
4. Optionally cleans up files

**Use Cases:**
- Migrating to different management system
- Cleaning up registry without affecting running configs
- Testing and debugging

**Warning Message:**
```
⚠️  This will remove 'my-server' from mcp-manager registry only.
The server will remain configured in:
• VS Code Cline
• Claude Desktop

These platforms may show errors if files are removed.
Use 'mcp-manager remove server' for complete removal.

Continue? [y/N]: 
```

#### 4. Bulk Removal

**Command:**
```bash
mcp-manager remove servers [options]
```

**Options:**
- `--pattern <pattern>`: Glob pattern to match server names
- `--type <local|remote>`: Filter by server type
- `--status <running|stopped>`: Filter by status
- `--yes, -y`: Skip confirmation prompt
- `--dry-run`: Show what would be removed

**Behavior:**
1. Lists servers matching criteria
2. Shows interactive selection (unless --yes)
3. Removes selected servers
4. Shows summary for each server

**Example Usage:**
```bash
# Remove all test servers
mcp-manager remove servers --pattern "test-*" --dry-run

# Remove all stopped servers
mcp-manager remove servers --status stopped

# Remove all remote servers
mcp-manager remove servers --type remote
```

**Example Output:**
```
Found 3 servers matching pattern 'test-*':
  • test-server-1
  • test-server-2
  • test-api-server

Remove these servers? [y/N]: y

[1/3] Removing test-server-1...  ✓
[2/3] Removing test-server-2...  ✓
[3/3] Removing test-api-server... ✓

Summary:
  Successfully removed: 3
  Failed: 0
  Space recovered: 127.8 MB
```

#### 5. Orphan Cleanup

**Command:**
```bash
mcp-manager remove orphaned [options]
```

**Options:**
- `--platform <cline|claude|all>`: Target specific platform (default: all)
- `--yes, -y`: Skip confirmation prompt
- `--dry-run`: Show what would be removed

**Behavior:**
1. Scans platform configurations
2. Identifies servers not in mcp-manager registry
3. Optionally removes orphaned entries
4. Shows detailed report

**Use Cases:**
- Cleanup after manual configuration edits
- Removing servers deleted by other tools
- Synchronization maintenance

**Example Output:**
```
Scanning for orphaned servers...

Found 2 orphaned servers in VS Code Cline:
  • old-server-1 (not in registry)
  • deleted-server (not in registry)

Found 0 orphaned servers in Claude Desktop

Remove these orphaned entries? [y/N]: y

✓ Removed 2 orphaned entries from Cline configuration
✓ No orphaned entries in Claude Desktop

Cleanup complete.
```

## Safety Mechanisms

### 1. Confirmation Prompts

All removal operations require explicit confirmation unless `--yes` flag is used.

**Standard Prompt:**
```
⚠️  About to remove server 'my-server'

This will remove:
  ✓ mcp-manager registry entry
  ✓ VS Code Cline configuration
  ✓ Claude Desktop configuration
  ✓ Virtual environment (~/.config/mcp-manager/servers/my-server/.venv)
  ✓ Log files (~/.config/mcp-manager/logs/my-server.log)
  ✓ Configuration files

Total space to recover: 46.5 MB

Type the server name to confirm: _
```

### 2. Dry-Run Mode

All commands support `--dry-run` to preview changes without executing.

**Dry-Run Output:**
```
🔍 Dry run mode - no changes will be made

Would remove server 'my-server':

Registry:
  ✓ Entry in ~/.config/mcp-manager/config/servers.json

Platforms:
  ✓ VS Code Cline: Found at mcpServers["my-server"]
  ✗ Claude Desktop: Not found

Files:
  ✓ Virtual environment: ~/.config/mcp-manager/servers/my-server/.venv (45.2 MB)
  ✓ Log file: ~/.config/mcp-manager/logs/my-server.log (1.3 MB)
  ✓ Config file: ~/.config/mcp-manager/servers/my-server/config.yaml (0.5 KB)

Total cleanup: 46.5 MB

Run without --dry-run to proceed.
```

### 3. Automatic Backups

Before modifying any configuration files, create timestamped backups:

**Backup Location:** `~/.config/mcp-manager/backups/`

**Backup Naming:**
- Registry: `servers.backup.YYYYMMDD_HHMMSS.json`
- Cline: `cline_mcp_settings.backup.YYYYMMDD_HHMMSS.json`
- Claude: `claude_desktop_config.backup.YYYYMMDD_HHMMSS.json`

**Backup Retention:**
- Keep last 10 backups per configuration file
- Automatically clean up older backups

### 4. Running Server Protection

Prevent removal of running servers unless `--force` is used.

**Warning Message:**
```
⚠️  Server 'my-server' is currently running (PID: 12345)

Options:
  1. Stop the server and remove: mcp-manager remove server my-server
  2. Force remove without stopping: mcp-manager remove server my-server --force

Forced removal may leave orphaned processes.
```

### 5. Undo Capability

Provide quick undo for recent removals:

**Command:**
```bash
mcp-manager restore <name> [--from-backup <timestamp>]
```

**Behavior:**
1. Lists available backups
2. Restores server configuration
3. Re-syncs to platforms
4. Does NOT restore files (those must be recreated)

## Enhanced Info Commands

Add removal impact analysis to existing info commands:

```bash
mcp-manager info show my-server --removal-impact
```

**Output:**
```
Server: my-server
Type: local
Status: running

If removed, this would affect:
  Registry:
    • Entry in mcp-manager registry
  
  Platforms:
    • VS Code Cline: Currently configured
    • Claude Desktop: Currently configured
  
  Files:
    • Virtual environment: 45.2 MB
    • Log files: 1.3 MB
    • Config files: 0.5 KB
  
  Total impact: 46.5 MB would be freed

To remove: mcp-manager remove server my-server
```

## Implementation Details

### Code Organization

```
utils/mcp_manager/src/mcp_manager/
├── cli/
│   └── commands/
│       ├── removal.py          # NEW: Removal command implementations
│       └── restore.py          # NEW: Restore/undo functionality
├── core/
│   ├── removal.py              # NEW: Core removal logic
│   ├── backup.py               # NEW: Backup management
│   └── cleanup.py              # NEW: File cleanup utilities
└── tests/
    └── test_removal.py         # NEW: Removal command tests
```

### Core Classes

```python
class RemovalManager:
    """Manages server removal operations."""
    
    def remove_server(
        self, 
        name: str,
        from_registry: bool = True,
        from_platforms: List[str] = ["cline", "claude"],
        cleanup_files: bool = True,
        force: bool = False
    ) -> RemovalResult
    
    def remove_from_platform(
        self,
        name: str,
        platform: PlatformType
    ) -> RemovalResult
    
    def find_orphaned_servers(
        self,
        platform: Optional[PlatformType] = None
    ) -> List[str]
    
    def calculate_removal_impact(
        self,
        name: str
    ) -> RemovalImpact


class BackupManager:
    """Manages configuration backups."""
    
    def create_backup(
        self,
        config_file: Path,
        prefix: str = "backup"
    ) -> Path
    
    def list_backups(
        self,
        config_type: str
    ) -> List[BackupInfo]
    
    def restore_backup(
        self,
        backup_file: Path
    ) -> bool
    
    def cleanup_old_backups(
        self,
        keep_count: int = 10
    ) -> int


class CleanupManager:
    """Manages file cleanup operations."""
    
    def cleanup_server_files(
        self,
        server: Server,
        dry_run: bool = False
    ) -> CleanupResult
    
    def calculate_cleanup_size(
        self,
        server: Server
    ) -> int
    
    def find_unused_files(
        self
    ) -> List[Path]
```

### Data Models

```python
class RemovalResult(BaseModel):
    """Result of a removal operation."""
    success: bool
    server_name: str
    removed_from: List[str]
    cleaned_files: List[Path]
    space_freed_mb: float
    errors: List[str]
    backups_created: List[Path]


class RemovalImpact(BaseModel):
    """Impact analysis for server removal."""
    server_name: str
    registry_exists: bool
    platform_configs: Dict[str, bool]
    files_to_remove: List[FileInfo]
    total_size_mb: float
    is_running: bool


class FileInfo(BaseModel):
    """Information about a file to be removed."""
    path: Path
    size_mb: float
    type: str  # venv, log, config, etc.


class BackupInfo(BaseModel):
    """Information about a backup file."""
    path: Path
    timestamp: datetime
    size_mb: float
    config_type: str
```

## User Workflows

### Workflow 1: Complete Server Removal

```bash
# 1. Check what will be removed
mcp-manager info show my-server --removal-impact

# 2. Preview removal
mcp-manager remove server my-server --dry-run

# 3. Remove server with confirmation
mcp-manager remove server my-server

# Output shows success, space recovered, and backup locations
```

### Workflow 2: Platform-Specific Removal

```bash
# 1. Remove from Cline only
mcp-manager remove from-cline my-server

# 2. Server still available in registry for re-sync if needed
mcp-manager config cline  # Would re-add the server
```

### Workflow 3: Bulk Cleanup

```bash
# 1. Find servers to remove
mcp-manager info list --status stopped

# 2. Remove all stopped servers
mcp-manager remove servers --status stopped --dry-run

# 3. Confirm and execute
mcp-manager remove servers --status stopped
```

### Workflow 4: Fix Orphaned Configurations

```bash
# 1. Find orphaned entries
mcp-manager remove orphaned --dry-run

# 2. Clean up orphans
mcp-manager remove orphaned --platform cline
```

### Workflow 5: Undo Accidental Removal

```bash
# 1. List available backups
mcp-manager restore --list

# 2. Restore specific server
mcp-manager restore my-server

# 3. Re-sync to platforms
mcp-manager config sync
```

## Edge Cases and Error Handling

### Edge Case 1: Server Running
**Issue:** User tries to remove a running server  
**Handling:** Warn and require `--force` or explicit stop first

### Edge Case 2: Partial Platform Configuration
**Issue:** Server in registry but only some platforms  
**Handling:** Show accurate status, only attempt removal where configured

### Edge Case 3: Corrupted Configuration Files
**Issue:** Platform config file is invalid JSON  
**Handling:** Create backup, attempt fix, or fail safely with clear error

### Edge Case 4: Permission Issues
**Issue:** Cannot write to platform config files  
**Handling:** Clear error message with suggested fix (run with sudo, check permissions)

### Edge Case 5: Missing Files
**Issue:** Server in registry but files already deleted  
**Handling:** Proceed with config removal, note missing files in output

### Edge Case 6: Concurrent Modifications
**Issue:** Another process modifies config during removal  
**Handling:** Use file locking, retry with exponential backoff

### Edge Case 7: Platform Not Installed
**Issue:** Attempting platform removal but platform not installed  
**Handling:** Skip gracefully with informational message

## Testing Strategy

### Unit Tests

```python
def test_remove_server_from_registry()
def test_remove_server_from_platform()
def test_remove_orphaned_servers()
def test_cleanup_files()
def test_create_backup()
def test_restore_backup()
def test_calculate_removal_impact()
def test_handle_running_server()
def test_handle_missing_files()
```

### Integration Tests

```python
def test_complete_removal_workflow()
def test_platform_specific_removal()
def test_bulk_removal()
def test_undo_removal()
def test_concurrent_operations()
```

### Manual Testing Checklist

- [ ] Remove server with confirmation
- [ ] Remove server with --yes
- [ ] Remove server with --dry-run
- [ ] Remove from-cline with backup verification
- [ ] Remove from-claude with backup verification
- [ ] Remove from-registry leaving platforms
- [ ] Remove servers with pattern matching
- [ ] Remove orphaned entries
- [ ] Attempt remove running server (should fail)
- [ ] Force remove running server
- [ ] Remove with --keep-files
- [ ] Restore from backup
- [ ] Verify space calculations accurate
- [ ] Test with missing platform configs
- [ ] Test with corrupted config files
- [ ] Test permission denied scenarios

## Migration Path

### Phase 1: Core Removal (Week 1)
- Implement RemovalManager
- Add `remove server` command
- Add backup functionality
- Basic testing

### Phase 2: Platform-Specific (Week 2)
- Add `remove from-cline`
- Add `remove from-claude`
- Add `remove from-registry`
- Platform-specific testing

### Phase 3: Advanced Features (Week 3)
- Add `remove servers` (bulk)
- Add `remove orphaned`
- Add `restore` command
- Integration testing

### Phase 4: Polish (Week 4)
- Enhanced output formatting
- Comprehensive error handling
- Documentation
- User acceptance testing

## Future Enhancements

### Version 1.1
- Interactive removal mode with checkboxes
- Removal scheduling (remove at specified time)
- Batch removal from file

### Version 1.2
- Server archiving (remove but keep compressed backup)
- Automatic orphan detection on startup
- Removal statistics and reporting

### Version 2.0
- Undo/redo stack for multiple operations
- Visual removal wizard (TUI)
- Integration with version control for configs

## Success Metrics

- ✅ All removal operations complete successfully
- ✅ No accidental data loss incidents
- ✅ User can easily remove servers at any level
- ✅ Platform configurations stay consistent
- ✅ Backup/restore works reliably
- ✅ Clear, informative output for all operations
- ✅ 100% test coverage for removal operations

## Open Questions

1. **Default behavior for registry removal**: Should it warn about orphaned platform configs?
2. **File cleanup policy**: Should venv removal be optional by default?
3. **Backup retention**: Is 10 backups appropriate, or should it be configurable?
4. **Force removal**: Should `--force` also skip backups for faster operation?
5. **Restore limitations**: Should restore recreate virtual environments automatically?

## Conclusion

This design provides a comprehensive, safe, and user-friendly approach to removing MCP servers at all configuration levels. The hierarchical command structure, combined with robust safety mechanisms, ensures users have fine-grained control while minimizing the risk of accidental data loss.

The implementation can be completed in 4 weeks with incremental releases, allowing for user feedback and iterative improvements.

---

**Approval Status:** ✅ Approved for Implementation  
**Next Steps:** Create implementation checklist and begin Phase 1
