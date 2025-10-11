# MCP Manager: Pipx Default Installation Implementation Checklist

## 🎯 Feature Overview
**Change mcp-manager to default to pipx installation with new --no-pipx flag to opt out**

**Current Behavior**: `--pipx` flag defaults to `False` (venv installation)  
**New Behavior**: Default to `True` (pipx installation), add `--no-pipx` flag for venv

## 📋 Implementation Checklist

### Phase 1: Core Logic Changes
- [ ] **1.1** Update `utils/mcp_manager/src/mcp_manager/cli/commands/install.py`
  - [ ] Change `pipx` parameter default from `False` to `True`
  - [ ] Add new `no_pipx` parameter with `--no-pipx` flag
  - [ ] Update parameter logic: `use_pipx = pipx and not no_pipx`
  - [ ] Update help text for both flags
  - [ ] Add mutual exclusion validation (can't use both `--pipx` and `--no-pipx`)

- [ ] **1.2** Update Installation Type Logic
  - [ ] Modify line ~37: `installation_type = InstallationType.PIPX if use_pipx else InstallationType.VENV`
  - [ ] Update pyproject.toml requirement check to use `use_pipx` variable
  - [ ] Ensure proper error messaging for missing pyproject.toml when using pipx

### Phase 2: CLI Interface Updates
- [ ] **2.1** Parameter Definition Changes
  ```python
  pipx: bool = typer.Option(True, "--pipx", help="Install as standalone application (default)"),
  no_pipx: bool = typer.Option(False, "--no-pipx", help="Use virtual environment instead of pipx"),
  ```

- [ ] **2.2** Add Validation Logic
  - [ ] Add check to prevent both `--pipx` and `--no-pipx` being used together
  - [ ] Add clear error message for conflicting flags
  - [ ] Add validation that `--no-pipx` overrides default pipx behavior

### Phase 3: Help and Documentation Updates
- [ ] **3.1** Update CLI Help Text
  - [ ] Update `--pipx` help: "Install as standalone application (default)"
  - [ ] Add `--no-pipx` help: "Use virtual environment instead of pipx installation"
  - [ ] Update main command help to reflect new default behavior

- [ ] **3.2** Update Documentation
  - [ ] Update `utils/mcp_manager/README.md` with new default behavior
  - [ ] Update any installation examples to reflect new defaults
  - [ ] Add migration notes for existing users
  - [ ] Update troubleshooting guide for pyproject.toml requirements

### Phase 4: Error Handling and User Experience
- [ ] **4.1** Improve Error Messages
  - [ ] Better error message when pyproject.toml is missing for pipx install
  - [ ] Suggest using `--no-pipx` flag in pyproject.toml error message
  - [ ] Clear guidance on when to use each installation method

- [ ] **4.2** Progress and Output Updates
  - [ ] Update progress messages to indicate installation type being used
  - [ ] Add info message showing chosen installation method
  - [ ] Update success message to indicate installation type used

### Phase 5: Backwards Compatibility
- [ ] **5.1** Consider Migration Path
  - [ ] Document breaking change in changelog
  - [ ] Consider adding deprecation warning for explicit `--pipx` usage
  - [ ] Ensure existing installations continue to work

- [ ] **5.2** Version Compatibility
  - [ ] Update version number in pyproject.toml (0.2.0 → 0.3.0 for breaking change)
  - [ ] Add version compatibility checks if needed

### Phase 6: Testing and Validation
- [ ] **6.1** Unit Tests
  - [ ] Test default pipx installation behavior
  - [ ] Test `--no-pipx` flag functionality
  - [ ] Test mutual exclusion validation
  - [ ] Test error handling for missing pyproject.toml
  - [ ] Test backwards compatibility scenarios

- [ ] **6.2** Integration Tests
  - [ ] Test installation of servers with pyproject.toml (should work by default)
  - [ ] Test installation of servers without pyproject.toml using `--no-pipx`
  - [ ] Test reinstallation scenarios with different flags
  - [ ] Test error scenarios and user feedback

- [ ] **6.3** Manual Testing
  - [ ] Install jira-helper using default behavior (should be pipx)
  - [ ] Install worldcontext using `--no-pipx` flag
  - [ ] Verify both installation types work correctly
  - [ ] Test help text and error messages

### Phase 7: Documentation and Communication
- [ ] **7.1** Update README Files
  - [ ] Update main README with new installation examples
  - [ ] Update developer documentation
  - [ ] Add migration guide for existing users

- [ ] **7.2** Add ADR (Architectural Decision Record)
  - [ ] Document why pipx is now the default
  - [ ] Document benefits and tradeoffs
  - [ ] Document migration considerations

### Phase 8: Release Preparation
- [ ] **8.1** Version Update
  - [ ] Update version to 0.3.0 (breaking change)
  - [ ] Update changelog with breaking changes
  - [ ] Update any version references

- [ ] **8.2** Release Testing
  - [ ] Test fresh installations on clean systems
  - [ ] Test upgrade scenarios from 0.2.0
  - [ ] Verify all existing servers continue to work
  - [ ] Test documentation examples

## 🔧 Code Changes Summary

### Primary Files to Modify:
1. `utils/mcp_manager/src/mcp_manager/cli/commands/install.py` - Core logic changes
2. `utils/mcp_manager/README.md` - Documentation updates  
3. `utils/mcp_manager/pyproject.toml` - Version bump
4. `docs/adr/` - New ADR for the change

### Key Logic Change:
```python
# Before
pipx: bool = typer.Option(False, "--pipx", help="Install as standalone application (requires pyproject.toml)")

# After  
pipx: bool = typer.Option(True, "--pipx", help="Install as standalone application (default)"),
no_pipx: bool = typer.Option(False, "--no-pipx", help="Use virtual environment instead of pipx"),

# Usage logic
if pipx and no_pipx:
    raise MCPManagerError("Cannot use both --pipx and --no-pipx flags")
use_pipx = pipx and not no_pipx
```

## 🎯 Success Criteria
- [ ] Default `mcp-manager install local` command uses pipx installation
- [ ] `--no-pipx` flag successfully forces venv installation  
- [ ] Clear error messages for missing pyproject.toml
- [ ] All existing functionality continues to work
- [ ] Comprehensive documentation updated
- [ ] Tests pass for both installation methods
- [ ] Breaking change properly documented and versioned

## ⚠️ Risks and Considerations
- **Breaking Change**: Existing automation may expect venv installation by default
- **pyproject.toml Requirement**: More servers will need pyproject.toml files
- **Error Experience**: Users without pyproject.toml will get errors by default
- **Migration Path**: Need clear guidance for users upgrading

## 📝 Notes
- This is a breaking change requiring a minor version bump (0.2.0 → 0.3.0)
- Consider adding a migration notice in the first run after upgrade
- May want to add server validation to check for pyproject.toml during development
- Should improve error messages to guide users toward solutions
