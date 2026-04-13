# Claude Code Support Implementation Checklist

## Overview
Implementation plan for adding Claude Code support to mcp-manager, enabling automated MCP server configuration for the `~/.claude.json` config file.

**Priority**: HIGH  
**Complexity**: MEDIUM  
**Target Version**: mcp-manager 0.4.0  
**Status**: Ready for Implementation

---

## Prerequisites

- [x] Research completed (see `docs/miscellaneous/MCP_CLIENT_SUPPORT_RESEARCH.md`)
- [x] Claude Code config file location confirmed: `~/.claude.json`
- [x] Config file structure analyzed
- [x] Backup strategy defined

---

## Phase 1: Core Implementation

### 1.1 Update Configuration Constants
**File**: `utils/mcp_manager/src/mcp_manager/cli/commands/config.py`

- [ ] Add "claude-code" to `SUPPORTED_EDITORS` list
- [ ] Add `~/.claude.json` path to `EDITOR_CONFIG_PATHS` dict
- [ ] Add Claude Code-specific configuration constants

**Implementation**:
```python
SUPPORTED_EDITORS = ["cline", "claude", "claude-code"]

EDITOR_CONFIG_PATHS = {
    "cline": Path.home() / "Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    "claude": Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    "claude-code": Path.home() / ".claude.json"  # NEW
}
```

### 1.2 Create Claude Code Configuration Handler
**File**: `utils/mcp_manager/src/mcp_manager/core/claude_code_config.py` (NEW)

- [ ] Create `ClaudeCodeConfigHandler` class
- [ ] Implement `backup()` method
- [ ] Implement `load()` method with validation
- [ ] Implement `add_servers()` method
- [ ] Implement `save()` method with structure preservation
- [ ] Add error handling for corrupted config files
- [ ] Add JSON validation

**Key Methods**:
```python
class ClaudeCodeConfigHandler:
    """Handle Claude Code ~/.claude.json configuration"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        
    def backup(self) -> Path:
        """Create timestamped backup of config file"""
        # Returns backup path
        
    def load(self) -> dict:
        """Load and validate JSON structure"""
        # Returns parsed config dict
        
    def add_servers(self, servers: List[ServerConfig]) -> None:
        """Add MCP servers to global mcpServers section"""
        # Modifies config in place
        
    def save(self, config: dict) -> None:
        """Save config preserving all existing structure"""
        # Writes to file with proper formatting
        
    def validate_structure(self, config: dict) -> bool:
        """Validate required keys exist in config"""
        # Returns True if valid
```

### 1.3 Update Config Command
**File**: `utils/mcp_manager/src/mcp_manager/cli/commands/config.py`

- [ ] Update `config()` function to handle "claude-code" editor
- [ ] Add Claude Code-specific logic using new handler
- [ ] Update help text and examples
- [ ] Add project-specific config support (optional for Phase 1)

**Implementation**:
```python
@app.command()
def config(
    editor: str = typer.Argument(
        ...,
        help="Editor to configure: cline, claude, or claude-code"
    ),
    project_path: Optional[str] = typer.Option(
        None,
        "--project",
        help="[Claude Code] Project path for project-specific config"
    )
):
    """Configure MCP servers for specified editor"""
    
    # Validate editor
    if editor not in SUPPORTED_EDITORS:
        console.print(f"[red]Unsupported editor: {editor}[/red]")
        console.print(f"Supported editors: {', '.join(SUPPORTED_EDITORS)}")
        raise typer.Exit(1)
    
    # Get config path
    config_path = EDITOR_CONFIG_PATHS.get(editor)
    
    # Load servers
    servers = load_installed_servers()
    
    if editor == "claude-code":
        # Use Claude Code-specific handler
        handler = ClaudeCodeConfigHandler(config_path)
        handler.backup()
        handler.add_servers(servers)
        console.print(f"[green]✓[/green] Configured {len(servers)} servers for Claude Code")
    elif editor in ["cline", "claude"]:
        # Existing implementation
        # ...
```

### 1.4 Add Tests
**File**: `utils/mcp_manager/tests/test_claude_code_config.py` (NEW)

- [ ] Test config file backup creation
- [ ] Test loading valid config file
- [ ] Test loading corrupted config file
- [ ] Test adding servers to empty mcpServers
- [ ] Test adding servers to existing mcpServers
- [ ] Test structure preservation after save
- [ ] Test with missing config file
- [ ] Mock file I/O for unit tests

---

## Phase 2: User Experience Enhancements

### 2.1 Update CLI Help and Documentation
**Files**: Multiple

- [ ] Update `mcp-manager --help` output
- [ ] Update `mcp-manager config --help` with Claude Code example
- [ ] Update README.md with Claude Code section
- [ ] Add Claude Code example to quickstart
- [ ] Update `mcp-manager info` to show Claude Code support

### 2.2 Add User Feedback
**File**: `utils/mcp_manager/src/mcp_manager/cli/commands/config.py`

- [ ] Show backup location in output
- [ ] Show number of servers configured
- [ ] Show config file location
- [ ] Warn if Claude Code not installed
- [ ] Show next steps (restart Claude Code)

**Example Output**:
```
ℹ Backed up existing config to: ~/.claude.backup.20251023210440
✓ Configured server 'jira-helper' for Claude Code
✓ Configured server 'worldcontext' for Claude Code  
✓ Configured server 'mcpservercreator' for Claude Code
✓ Updated Claude Code settings at: ~/.claude.json
ℹ Configured 3 servers
ℹ You may need to restart Claude Code for changes to take effect
```

### 2.3 Add Validation and Error Handling
**File**: `utils/mcp_manager/src/mcp_manager/core/claude_code_config.py`

- [ ] Check if Claude Code is installed
- [ ] Validate config file before modification
- [ ] Handle JSON parsing errors gracefully
- [ ] Rollback on save failure
- [ ] Provide clear error messages

---

## Phase 3: Advanced Features (Optional)

### 3.1 Project-Specific Configuration
**File**: `utils/mcp_manager/src/mcp_manager/core/claude_code_config.py`

- [ ] Add project path parameter support
- [ ] Implement project-specific server addition
- [ ] Handle projects section in config
- [ ] Add validation for project paths
- [ ] Update documentation

**Usage**:
```bash
# Global configuration (default)
mcp-manager config claude-code

# Project-specific configuration
mcp-manager config claude-code --project /path/to/project
```

### 3.2 Server Removal for Claude Code
**File**: `utils/mcp_manager/src/mcp_manager/cli/commands/removal.py`

- [ ] Extend removal command to support Claude Code
- [ ] Handle global vs project-specific removal
- [ ] Update tests for Claude Code removal

### 3.3 List Command Enhancement
**File**: `utils/mcp_manager/src/mcp_manager/cli/commands/list.py`

- [ ] Show which editors each server is configured for
- [ ] Add "Configured In" column to table
- [ ] Show Claude Code in configured editors list

---

## Testing Plan

### Unit Tests
- [ ] Test ClaudeCodeConfigHandler.backup()
- [ ] Test ClaudeCodeConfigHandler.load()
- [ ] Test ClaudeCodeConfigHandler.add_servers()
- [ ] Test ClaudeCodeConfigHandler.save()
- [ ] Test with various config file states
- [ ] Test error handling paths

### Integration Tests
- [ ] Test full config workflow (backup -> load -> modify -> save)
- [ ] Test with real ~/.claude.json file (backup first!)
- [ ] Test server addition to empty config
- [ ] Test server addition to populated config
- [ ] Test multiple servers
- [ ] Test config command end-to-end

### Manual Testing
- [ ] Verify Claude Code recognizes configured servers
- [ ] Test in fresh environment
- [ ] Test with existing servers
- [ ] Test backup restoration
- [ ] Verify no data loss in config file
- [ ] Test error scenarios

---

## Documentation Updates

### Code Documentation
- [ ] Add docstrings to all new methods
- [ ] Add inline comments for complex logic
- [ ] Update type hints
- [ ] Add usage examples in docstrings

### User Documentation
- [ ] Update README.md with Claude Code section
- [ ] Add Claude Code to supported clients list
- [ ] Update installation instructions
- [ ] Add troubleshooting section for Claude Code
- [ ] Create Claude Code configuration guide

### Developer Documentation
- [ ] Document Claude Code config file structure
- [ ] Document implementation decisions
- [ ] Add architecture notes
- [ ] Update contribution guide

---

## Implementation Order

1. **Core Functionality** (Week 1)
   - [ ] Create ClaudeCodeConfigHandler class
   - [ ] Update config command
   - [ ] Basic tests
   - [ ] Manual verification

2. **Polish & Testing** (Week 2)
   - [ ] Comprehensive test suite
   - [ ] Error handling
   - [ ] User feedback
   - [ ] Documentation

3. **Advanced Features** (Week 3+)
   - [ ] Project-specific config (optional)
   - [ ] Server removal support
   - [ ] List command enhancement

---

## Success Criteria

- [ ] Users can run `mcp-manager config claude-code` successfully
- [ ] Servers appear in Claude Code after configuration
- [ ] Original config structure is preserved
- [ ] Backups are created automatically
- [ ] Clear error messages for all failure cases
- [ ] All tests pass
- [ ] Documentation is complete
- [ ] No regressions in Cline/Claude Desktop support

---

## Rollout Plan

1. **Alpha Testing** (Internal)
   - Test with development team
   - Verify on multiple machines
   - Fix critical bugs

2. **Beta Release** (0.4.0-beta)
   - Announce in release notes
   - Gather user feedback
   - Monitor for issues

3. **Stable Release** (0.4.0)
   - Address beta feedback
   - Final documentation review
   - Public announcement

---

## Risk Mitigation

### Risk: Config File Corruption
**Mitigation**: 
- Always create backup before modification
- Validate JSON after modification
- Implement rollback on failure
- Thorough testing with various config states

### Risk: Breaking Existing Functionality
**Mitigation**:
- Comprehensive test suite for existing features
- Keep Cline/Claude Desktop logic separate
- No shared code paths unless necessary
- Regression testing before release

### Risk: User Data Loss
**Mitigation**:
- Timestamped backups
- Clear backup location messaging
- Validation before save
- Recovery instructions in docs

---

## Timeline

**Estimated Completion**: 2-3 weeks

- Week 1: Core implementation (ClaudeCodeConfigHandler, basic config command)
- Week 2: Testing, error handling, documentation
- Week 3: Polish, advanced features (optional), release prep

**Quick Implementation** (if needed): 1 week for basic functionality

---

## Related Documents

- Research: `docs/miscellaneous/MCP_CLIENT_SUPPORT_RESEARCH.md`
- Main README: `utils/mcp_manager/README.md`
- Config Command: `utils/mcp_manager/src/mcp_manager/cli/commands/config.py`

---

## Notes

- Focus on global configuration first (simplest, most useful)
- Project-specific can be added later if demand warrants
- Keep implementation simple and maintainable
- Prioritize data safety (backups, validation)
- ChatGPT support will be documentation-only for now

---

**Last Updated**: October 23, 2025  
**Status**: Ready for Implementation  
**Next Action**: Begin Phase 1.1 - Update Configuration Constants
