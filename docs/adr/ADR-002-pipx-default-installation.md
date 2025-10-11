# ADR-002: Default to Pipx Installation Method

## Status
**Proposed**

## Context
Currently, mcp-manager defaults to virtual environment (venv) installation for local servers, requiring users to explicitly specify `--pipx` flag for standalone application installation. This creates friction for users wanting isolated server deployments and doesn't align with modern Python packaging best practices.

### Current State
- Default installation: `mcp-manager install local server-name --source path/` → Uses venv
- Pipx installation: `mcp-manager install local server-name --source path/ --pipx` → Uses pipx
- Users must remember to add `--pipx` flag for better isolation

### Problem Statement
1. **Suboptimal Defaults**: Virtual environments within mcp-manager's control are less isolated than pipx installations
2. **User Experience**: Users forget to specify `--pipx` and get less optimal installations
3. **Modern Standards**: Pipx is becoming the standard for installing Python applications as standalone tools
4. **Dependency Conflicts**: Venv installations can have conflicts with system Python packages

## Decision
**Change mcp-manager to default to pipx installation method with a new `--no-pipx` flag to opt into venv installation.**

### New Behavior
- Default installation: `mcp-manager install local server-name --source path/` → Uses pipx (NEW)
- Venv installation: `mcp-manager install local server-name --source path/ --no-pipx` → Uses venv
- Explicit pipx: `mcp-manager install local server-name --source path/ --pipx` → Uses pipx (still works)

## Consequences

### Positive
1. **Better Isolation**: Pipx installations are completely isolated from system Python and other applications
2. **Easier Management**: Servers installed with pipx are easier to manage and upgrade
3. **Modern Standards**: Aligns with current Python ecosystem best practices
4. **Reduced Conflicts**: Eliminates dependency conflicts between servers and system packages
5. **Consistent Experience**: Users get the best installation method by default

### Negative
1. **Breaking Change**: Existing automation scripts may break if they depend on venv being default
2. **pyproject.toml Requirement**: All servers must have pyproject.toml files for pipx installation
3. **Learning Curve**: Users familiar with venv installations need to learn new behavior
4. **Error Messages**: Users without pyproject.toml will get errors by default instead of falling back

### Migration Impact
- **Version**: This requires a minor version bump (0.2.0 → 0.3.0) due to breaking change
- **Existing Servers**: All current installations continue to work regardless of installation method
- **New Installations**: Will default to pipx, requiring pyproject.toml files
- **Documentation**: All examples and documentation need updating

## Implementation Details

### Code Changes
1. **Primary Change**: In `install.py`, change `pipx: bool = typer.Option(False, ...)` to `pipx: bool = typer.Option(True, ...)`
2. **New Flag**: Add `no_pipx: bool = typer.Option(False, "--no-pipx", help="Use virtual environment instead of pipx")`
3. **Logic**: `use_pipx = pipx and not no_pipx`
4. **Validation**: Ensure `--pipx` and `--no-pipx` are mutually exclusive

### Error Handling Improvements
- Better error message when pyproject.toml is missing for pipx installation
- Suggest using `--no-pipx` flag in error messages
- Clear guidance on when to use each installation method

### Documentation Updates
- Update all installation examples to reflect new defaults
- Add migration guide for existing users
- Update troubleshooting documentation
- Create clear guidance on pyproject.toml requirements

## Alternatives Considered

### Alternative 1: Keep Current Behavior
**Rejected**: Would maintain suboptimal defaults and user experience issues

### Alternative 2: Auto-detect Installation Method
**Rejected**: Too complex, unpredictable behavior, harder to debug

### Alternative 3: Add Configuration Option
**Rejected**: Adds complexity without significant benefit, defaults should be sensible

### Alternative 4: Gradual Migration with Warnings
**Considered**: Could add deprecation warnings for venv installations, but adds complexity

## Implementation Plan
1. **Phase 1**: Core logic changes and parameter updates
2. **Phase 2**: CLI interface and validation updates  
3. **Phase 3**: Error handling and user experience improvements
4. **Phase 4**: Documentation and help text updates
5. **Phase 5**: Testing and validation
6. **Phase 6**: Release preparation and migration guides

## Success Metrics
- [ ] Default installations use pipx without user intervention
- [ ] `--no-pipx` flag successfully forces venv installation
- [ ] Error messages clearly guide users to solutions
- [ ] All existing functionality continues to work
- [ ] User feedback indicates improved experience

## Timeline
- **Target Implementation**: Next minor release (v0.3.0)
- **Breaking Change Notice**: Documented in changelog and release notes
- **Migration Support**: Documentation and examples updated

## Related Documents
- Implementation checklist: `docs/miscellaneous/PIPX_DEFAULT_IMPLEMENTATION_CHECKLIST.md`
- Original design decisions: `docs/adr/design_decisions.md`

---
**Date**: 2025-01-27  
**Author**: Development Team  
**Reviewers**: TBD  
**Decision Date**: TBD
