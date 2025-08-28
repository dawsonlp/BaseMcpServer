# MCP Manager Naming Standardization Checklist

**Goal**: Standardize on `mcp-manager` as the primary CLI command name while maintaining backward compatibility

## Current Status
- ✅ **PyPI Package Name**: `mcp-manager` (already correct)
- ✅ **Python Package Name**: `mcp_manager` (already correct, required by Python syntax)
- ✅ **CLI Script Entry**: Updated to `mcp-manager` with `mcpmanager` alias for backward compatibility

## Files to Review and Update

### Documentation Files
- [ ] `utils/mcp_manager/README.md` - Update installation and usage examples
- [ ] `utils/mcp_manager/MCP_MANAGER_2.0_ARCHITECTURE.md` - Update CLI command references
- [ ] `docs/BUILD_A_NEW_MCP.md` - Check for mcpmanager references
- [ ] `docs/cline-compatibility.md` - Check for command references
- [ ] `docs/design_decisions.md` - Update with naming decision
- [ ] `QUICKSTART.md` - Update command examples if any
- [ ] `readme.md` (project root) - Update command references if any

### Configuration and Setup Files
- [x] `utils/mcp_manager/pyproject.toml` - **COMPLETED**: Updated scripts section
- [ ] Check for any Docker files that might reference the command
- [ ] Check for any shell scripts that might call mcpmanager

### Code Files That May Reference Command Name
- [ ] Search for hardcoded "mcpmanager" strings in source code
- [ ] Check help text and documentation strings within the CLI
- [ ] Check error messages that might reference the command name
- [ ] Check any subprocess calls that might invoke the command

### Other Services/Projects in Repository
- [ ] `servers/jira-helper/` - Check for mcpmanager references
- [ ] `servers/document-processor/` - Check for mcpmanager references  
- [ ] `servers/mcpservercreator/` - Check for mcpmanager references
- [ ] `servers/worldcontext/` - Check for mcpmanager references
- [ ] `servers/template/` - Check for mcpmanager references
- [ ] Any other server directories for command references

### Testing and Examples
- [ ] Look for test files that might call the CLI command
- [ ] Check example scripts or usage demos
- [ ] Check any CI/CD configuration files

### User-Facing Communication
- [ ] Update any help text within the application
- [ ] Check CLI command descriptions and examples
- [ ] Verify --help output shows correct command name
- [ ] Update any error messages that reference the command

## Search Tasks
- [ ] Search project-wide for "mcpmanager" (case-insensitive)
- [ ] Search project-wide for "mcp_manager" in documentation contexts
- [ ] Search for installation instructions
- [ ] Search for usage examples

## Validation Steps
- [ ] Test `mcp-manager` command works after pipx install
- [ ] Test `mcpmanager` alias still works (backward compatibility)
- [ ] Test `python -m mcp_manager` still works
- [ ] Verify help text shows correct primary command name
- [ ] Check all documentation uses consistent naming

## Communication Plan
- [ ] Decide on transition timeline for users
- [ ] Consider whether to announce the naming change
- [ ] Update any external references (if applicable)

## Notes
- Primary command: `mcp-manager`
- Backward compatibility: `mcpmanager` (alias)
- Module execution: `python -m mcp_manager` (unchanged)
- Package structure: `mcp_manager/` (unchanged)
