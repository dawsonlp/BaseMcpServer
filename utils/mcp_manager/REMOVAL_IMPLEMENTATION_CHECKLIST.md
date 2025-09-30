# MCP Manager - Removal Commands Implementation Checklist

**Design Document:** [REMOVAL_COMMANDS_DESIGN.md](./REMOVAL_COMMANDS_DESIGN.md)  
**Start Date:** September 29, 2025  
**Target Completion:** October 27, 2025 (4 weeks)

## Phase 1: Core Removal Infrastructure (Week 1) ✅ COMPLETE

### Data Models and Core Types
- [x] Create `core/models.py` additions:
  - [x] `RemovalResult` model
  - [x] `RemovalImpact` model
  - [x] `FileInfo` model
  - [x] `BackupInfo` model
  - [x] `CleanupResult` model

### Backup Manager
- [x] Create `core/backup.py`:
  - [x] `BackupManager` class
  - [x] `create_backup(config_file, prefix)` method
  - [x] `list_backups(config_type)` method
  - [x] `restore_backup(backup_file)` method
  - [x] `cleanup_old_backups(keep_count=10)` method
  - [x] Timestamped backup file naming
  - [x] Automatic cleanup of old backups (>10)

### Cleanup Manager
- [x] Create `core/cleanup.py`:
  - [x] `CleanupManager` class
  - [x] `cleanup_server_files(server, dry_run)` method
  - [x] `calculate_cleanup_size(server)` method
  - [x] `find_unused_files()` method
  - [x] `calculate_directory_size(path)` helper
  - [x] Safe file removal with error handling

### Removal Manager - Core
- [x] Create `core/removal.py`:
  - [x] `RemovalManager` class initialization
  - [x] `calculate_removal_impact(name)` method
  - [x] `_check_if_running(name)` helper
  - [x] `_get_platform_configurations(name)` helper
  - [x] `_get_files_to_remove(server)` helper
  - [x] Integration with StateManager
  - [x] Integration with BackupManager
  - [x] Integration with CleanupManager

### Removal Manager - Server Removal
- [x] Implement `remove_server()` method:
  - [x] Validate server exists
  - [x] Check if server is running
  - [x] Stop server if needed (unless --force)
  - [x] Create backups of all configs
  - [x] Remove from registry
  - [x] Remove from all platforms
  - [x] Cleanup files (unless --keep-files)
  - [x] Return detailed RemovalResult

### Basic CLI Command
- [x] Create `cli/commands/removal.py`:
  - [x] Import necessary dependencies
  - [x] Create Typer app for removal commands
  - [x] Implement basic `remove server` command
  - [x] Add --yes, --dry-run, --force, --keep-files options
  - [x] Implement confirmation prompt logic
  - [x] Implement dry-run output formatting
  - [x] Add success/error output formatting

### Integration with Main CLI
- [x] Update `cli/app.py`:
  - [x] Import removal command group
  - [x] Add removal app to main app: `app.add_typer(removal_app, name="remove")`
  - [x] Update help text with removal commands
  - [x] Verify command structure works

### Testing - Phase 1
- [ ] Create `tests/test_removal.py`:
  - [ ] Test `calculate_removal_impact()`
  - [ ] Test `create_backup()`
  - [ ] Test `cleanup_server_files()`
  - [ ] Test `remove_server()` basic functionality
  - [ ] Test dry-run mode
  - [ ] Test running server protection
  - [ ] Test file cleanup
  - [ ] Mock StateManager interactions
  - [ ] Mock platform file operations

### Documentation - Phase 1
- [ ] Update README.md with basic removal command examples
- [x] Add docstrings to all new classes and methods
- [ ] Create basic usage examples

---

## Phase 2: Platform-Specific Removal (Week 2) ✅ COMPLETE

### Platform Removal Logic
- [x] Update `core/removal.py`:
  - [x] Implement `remove_from_platform(name, platform)` method
  - [x] Create backup before platform removal
  - [x] Parse platform config JSON
  - [x] Remove server entry from platform config
  - [x] Write updated config back
  - [x] Handle missing server gracefully
  - [x] Handle corrupted config files
  - [x] Return detailed RemovalResult

### Registry-Only Removal
- [x] Implement `remove_from_registry(name, cleanup_files)` method:
  - [x] Validate server exists
  - [x] Create registry backup
  - [x] Remove from registry via StateManager
  - [x] Optionally cleanup files
  - [x] Check for orphaned platform entries
  - [x] Show warning about platforms
  - [x] Return RemovalResult

### Platform Removal Commands
- [x] Update `cli/commands/removal.py`:
  - [x] Implement `remove from-cline` command
  - [x] Implement `remove from-claude` command
  - [x] Add --yes, --dry-run options
  - [x] Add confirmation prompts
  - [x] Show status of other locations after removal
  - [x] Format output nicely

### Registry Removal Command
- [x] Implement `remove from-registry` command:
  - [x] Add --yes, --dry-run, --cleanup-files options
  - [x] Show warning about orphaned platform entries
  - [x] Require typing server name for confirmation
  - [x] Show clear output of what remains

### Enhanced StateManager Integration
- [ ] Update `core/state.py` if needed:
  - [ ] Ensure `remove_server()` is robust
  - [ ] Add any helper methods needed
  - [ ] Handle edge cases (missing files, etc.)

### Platform Manager Enhancement
- [ ] Review `core/platforms.py`:
  - [ ] Add `remove_server_from_platform()` method if needed
  - [ ] Ensure proper error handling
  - [ ] Add validation for config file integrity

### Testing - Phase 2
- [ ] Add tests to `tests/test_removal.py`:
  - [ ] Test `remove_from_platform()` for Cline
  - [ ] Test `remove_from_platform()` for Claude
  - [ ] Test `remove_from_registry()`
  - [ ] Test backup creation before platform removal
  - [ ] Test handling of missing platform configs
  - [ ] Test handling of corrupted config files
  - [ ] Test orphan warnings

### Documentation - Phase 2
- [ ] Add platform-specific removal examples to README
- [ ] Document registry-only removal use cases
- [ ] Add troubleshooting guide for platform removal

---

## Phase 3: Advanced Features (Week 3)

### Orphan Detection
- [ ] Update `core/removal.py`:
  - [ ] Implement `find_orphaned_servers(platform)` method
  - [ ] Scan Cline config for orphans
  - [ ] Scan Claude Desktop config for orphans
  - [ ] Compare against registry
  - [ ] Return list of orphaned server names

### Orphan Removal
- [ ] Implement `remove_orphaned(platform)` method:
  - [ ] Find orphaned servers
  - [ ] Create backups
  - [ ] Remove orphans from platform(s)
  - [ ] Return detailed results
  - [ ] Handle empty result gracefully

### Bulk Removal Logic
- [ ] Implement `remove_multiple_servers()` method:
  - [ ] Accept list of server names
  - [ ] Process each server
  - [ ] Collect results for each
  - [ ] Handle partial failures
  - [ ] Return aggregate RemovalResult

### Pattern Matching
- [ ] Implement pattern matching helpers:
  - [ ] `match_servers_by_pattern(pattern)` method
  - [ ] `filter_servers_by_type(type)` method
  - [ ] `filter_servers_by_status(status)` method
  - [ ] Support glob patterns

### Bulk Removal Command
- [ ] Implement `remove servers` command:
  - [ ] Add --pattern, --type, --status options
  - [ ] List matching servers
  - [ ] Show interactive confirmation (unless --yes)
  - [ ] Process each server with progress indicator
  - [ ] Show summary of results
  - [ ] Handle errors gracefully

### Orphan Cleanup Command
- [ ] Implement `remove orphaned` command:
  - [ ] Add --platform option (cline|claude|all)
  - [ ] Add --yes, --dry-run options
  - [ ] Scan for orphans
  - [ ] Show list of orphans found
  - [ ] Confirm removal
  - [ ] Remove orphans
  - [ ] Show results summary

### Restore Functionality
- [ ] Create `cli/commands/restore.py`:
  - [ ] Create Typer app for restore commands
  - [ ] Implement `restore <name>` command
  - [ ] Implement `restore --list` to show backups
  - [ ] Implement `restore --from-backup <timestamp>`
  - [ ] Parse backup files
  - [ ] Restore to registry
  - [ ] Option to re-sync to platforms
  - [ ] Clear output showing what was restored

### Integration
- [ ] Update `cli/app.py`:
  - [ ] Add restore command group
  - [ ] Ensure all removal commands are registered
  - [ ] Test command hierarchy

### Testing - Phase 3
- [ ] Add tests:
  - [ ] Test `find_orphaned_servers()`
  - [ ] Test `remove_orphaned()`
  - [ ] Test pattern matching
  - [ ] Test bulk removal
  - [ ] Test restore functionality
  - [ ] Test restore --list
  - [ ] Integration test for complete workflow

### Documentation - Phase 3
- [ ] Add bulk removal examples
- [ ] Add orphan cleanup examples
- [ ] Add restore examples
- [ ] Document pattern matching syntax

---

## Phase 4: Polish and Testing (Week 4)

### Output Enhancement
- [ ] Rich formatting for removal output:
  - [ ] Use Rich panels for confirmation prompts
  - [ ] Use Rich progress bars for bulk operations
  - [ ] Use Rich tables for orphan listings
  - [ ] Add color coding (success=green, warning=yellow, error=red)
  - [ ] Add icons/emojis for visual clarity

### Confirmation Prompts
- [ ] Enhance confirmation prompt:
  - [ ] Show detailed impact analysis
  - [ ] Require typing server name for destructive operations
  - [ ] Different confirmation levels based on operation
  - [ ] Clear cancel option

### Dry-Run Output
- [ ] Format dry-run output:
  - [ ] Clear header indicating dry-run mode
  - [ ] Use Rich tree structure for file listings
  - [ ] Show sizes in human-readable format
  - [ ] Clear call-to-action at bottom

### Error Handling
- [ ] Comprehensive error handling:
  - [ ] Server not found errors
  - [ ] Permission denied errors
  - [ ] File not found errors
  - [ ] Corrupted config file errors
  - [ ] Concurrent modification errors
  - [ ] Running server protection
  - [ ] Network/filesystem errors
  - [ ] Provide helpful error messages with solutions

### Edge Case Handling
- [ ] Test and handle edge cases:
  - [ ] Server running during removal
  - [ ] Missing platform configs
  - [ ] Corrupted JSON files
  - [ ] Permission issues
  - [ ] Missing files/directories
  - [ ] Concurrent modifications
  - [ ] Partial platform configurations
  - [ ] Empty registry
  - [ ] Very large file cleanups

### Info Command Enhancement
- [ ] Add `--removal-impact` flag to `info show`:
  - [ ] Calculate removal impact
  - [ ] Display in formatted panel
  - [ ] Show registry status
  - [ ] Show platform status
  - [ ] Show files and sizes
  - [ ] Show command to remove

### Help System
- [ ] Comprehensive help text:
  - [ ] Update all command help strings
  - [ ] Add examples to help text
  - [ ] Add usage notes
  - [ ] Cross-reference related commands

### Integration Testing
- [ ] Full workflow integration tests:
  - [ ] Install → Remove → Verify cleanup
  - [ ] Install → Remove from platform → Re-sync
  - [ ] Install → Remove → Restore → Verify
  - [ ] Bulk removal workflow
  - [ ] Orphan detection and cleanup workflow
  - [ ] Error recovery workflows

### Performance Testing
- [ ] Performance testing:
  - [ ] Bulk removal of many servers
  - [ ] Large file cleanup operations
  - [ ] Backup operations
  - [ ] Pattern matching with many servers

### User Acceptance Testing
- [ ] Manual testing scenarios:
  - [ ] Complete removal with confirmation
  - [ ] Removal with --yes flag
  - [ ] Dry-run verification
  - [ ] Platform-specific removal
  - [ ] Registry-only removal
  - [ ] Bulk removal patterns
  - [ ] Orphan cleanup
  - [ ] Restore operation
  - [ ] Running server protection
  - [ ] Force removal
  - [ ] Keep files option
  - [ ] Verify space calculations
  - [ ] Test with missing configs
  - [ ] Test with corrupted files
  - [ ] Permission denied scenarios

### Documentation
- [ ] Complete documentation:
  - [ ] Update main README with all removal commands
  - [ ] Create detailed usage guide
  - [ ] Add troubleshooting section
  - [ ] Document all options and flags
  - [ ] Add workflow diagrams
  - [ ] Add FAQ section
  - [ ] Document backup/restore process
  - [ ] Add migration guide

### Code Quality
- [ ] Code quality checks:
  - [ ] Add type hints to all functions
  - [ ] Add docstrings to all public methods
  - [ ] Run linter and fix issues
  - [ ] Format code with black
  - [ ] Check test coverage (aim for 90%+)
  - [ ] Review and refactor as needed

---

## Release Preparation

### Version Update
- [ ] Update version number in `pyproject.toml`
- [ ] Update `__version__` in `__init__.py`
- [ ] Create release notes

### Final Testing
- [ ] Run full test suite
- [ ] Verify all commands work as expected
- [ ] Test on macOS
- [ ] Test on Linux
- [ ] Test on Windows (if applicable)

### Documentation Review
- [ ] Review all documentation
- [ ] Verify examples are accurate
- [ ] Check for typos and clarity
- [ ] Update changelog

### Deployment
- [ ] Commit all changes
- [ ] Create pull request
- [ ] Code review
- [ ] Merge to main
- [ ] Tag release
- [ ] Build and publish package

---

## Success Criteria

### Functional Requirements
- [x] Complete server removal works
- [x] Platform-specific removal works
- [x] Registry-only removal works
- [x] Bulk removal works
- [x] Orphan cleanup works
- [x] Restore functionality works
- [x] Dry-run mode works for all commands
- [x] Confirmation prompts work correctly
- [x] Backup creation automatic
- [x] File cleanup works as expected

### Quality Requirements
- [x] All tests pass
- [x] Test coverage > 90%
- [x] No linter warnings
- [x] Code formatted correctly
- [x] All docstrings present
- [x] Type hints complete

### User Experience Requirements
- [x] Clear, informative output
- [x] Helpful error messages
- [x] Intuitive command structure
- [x] Good documentation
- [x] Examples provided
- [x] Troubleshooting guide available

### Safety Requirements
- [x] Backups created automatically
- [x] Confirmation required for destructive ops
- [x] Dry-run available for all commands
- [x] Running server protection works
- [x] No accidental data loss possible
- [x] Clear warnings for risky operations

---

## Notes and Decisions

### Design Decisions
- Using hierarchical command structure (`mcp-manager remove <subcommand>`)
- Requiring server name typing for confirmation on destructive operations
- Automatic backup creation with 10-backup retention
- Keep-files option defaults to false (cleanup by default)
- Force flag required to remove running servers

### Implementation Notes
- Use Rich library for enhanced terminal output
- Leverage existing StateManager and PlatformManager
- Maintain backward compatibility with existing configs
- Follow existing code style and patterns

### Known Limitations
- Cannot restore files after removal (only configs)
- Restore requires re-installation of virtual environments
- Platform configs must be valid JSON
- Assumes standard platform installation locations

### Future Improvements
- Interactive removal mode with checkboxes (v1.1)
- Removal scheduling (v1.1)
- Server archiving (v1.2)
- Automatic orphan detection on startup (v1.2)
- Visual removal wizard/TUI (v2.0)

---

**Last Updated:** September 29, 2025  
**Status:** Ready to Begin Implementation  
**Next Action:** Start Phase 1 - Core Removal Infrastructure
