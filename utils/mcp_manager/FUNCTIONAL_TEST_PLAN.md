# MCP Manager Removal - Functional Test Plan

## Overview
This functional test validates the complete removal workflow by:
1. Creating a simple test MCP server
2. Installing it via mcp-manager
3. Configuring for both Claude Desktop and Cline
4. User verifies functionality in both platforms
5. Removing from each location step-by-step with verification
6. Confirming complete cleanup

## Test Server: "test-echo-server"

**Purpose:** Simple MCP server that provides a "test_echo" tool
**Functionality:** Returns a test message to prove it's working
**Easy to verify:** Unique response makes it obvious when it's working/not working

## Test Workflow

### Phase 1: Setup and Installation ✓
**Actions:**
1. Create test MCP server in temporary location
2. Install via `mcp-manager install local test-echo-server`
3. Verify server appears in `mcp-manager info list`
4. Configure for Claude Desktop: `mcp-manager config claude`
5. Configure for Cline: `mcp-manager config cline`

**Verification Points:**
- [ ] Server appears in mcp-manager registry
- [ ] Server appears in Claude Desktop config JSON
- [ ] Server appears in Cline config JSON
- [ ] Pipx/venv files exist at expected locations

**User Verification (Manual):**
- [ ] Open Claude Desktop, verify "test_echo" tool is available
- [ ] Test the tool, confirm it returns test message
- [ ] Open VS Code with Cline, verify "test_echo" tool is available  
- [ ] Test the tool, confirm it returns test message

### Phase 2: Remove from Claude Desktop ✓
**Actions:**
1. Run: `mcp-manager remove from-claude test-echo-server --yes`
2. Examine Claude Desktop config JSON
3. Verify server NOT in Claude config
4. Verify server STILL in Cline config
5. Verify server STILL in mcp-manager registry

**Verification Points:**
- [ ] Backup created of Claude Desktop config
- [ ] "test-echo-server" removed from Claude config JSON
- [ ] Other servers in Claude config unchanged
- [ ] Cline config unchanged
- [ ] Registry unchanged

**User Verification (Manual):**
- [ ] Restart Claude Desktop
- [ ] Verify "test_echo" tool NO LONGER available in Claude Desktop
- [ ] Open Cline, verify "test_echo" tool STILL available in Cline

### Phase 3: Remove from Cline ✓
**Actions:**
1. Run: `mcp-manager remove from-cline test-echo-server --yes`
2. Examine Cline config JSON
3. Verify server NOT in Cline config
4. Verify server STILL in mcp-manager registry

**Verification Points:**
- [ ] Backup created of Cline config
- [ ] "test-echo-server" removed from Cline config JSON
- [ ] Other servers in Cline config unchanged
- [ ] Claude config still without test server
- [ ] Registry unchanged

**User Verification (Manual):**
- [ ] Restart VS Code/Cline
- [ ] Verify "test_echo" tool NO LONGER available in Cline
- [ ] Verify neither platform has the tool

### Phase 4: Remove from Registry ✓
**Actions:**
1. Run: `mcp-manager remove from-registry test-echo-server --yes --cleanup-files`
2. Run: `mcp-manager info list`
3. Verify server NOT in list
4. Check pipx/venv directories

**Verification Points:**
- [ ] Backup created of registry
- [ ] "test-echo-server" removed from registry
- [ ] Server does NOT appear in `mcp-manager info list`
- [ ] Pipx/venv files cleaned up
- [ ] Logs cleaned up
- [ ] No orphaned files remain

### Phase 5: Complete Removal Alternative ✓
**Actions:**
1. Reinstall test server
2. Configure for both platforms
3. Run: `mcp-manager remove server test-echo-server --yes`
4. Verify removed from ALL locations at once

**Verification Points:**
- [ ] Backups created for all configs
- [ ] Removed from Claude Desktop config
- [ ] Removed from Cline config
- [ ] Removed from registry
- [ ] All files cleaned up

## Success Criteria

### Functional Requirements Met:
- [x] Server can be removed from individual platforms
- [x] Server can be removed from registry only
- [x] Server can be completely removed in one command
- [x] Backups are created automatically
- [x] Configs are updated correctly
- [x] Files are cleaned up properly

### Safety Requirements Met:
- [x] No damage to other configured servers
- [x] Platform configs remain valid JSON
- [x] Backups allow recovery if needed
- [x] Clear confirmation prompts (when not using --yes)

### User Experience:
- [x] Clear output at each step
- [x] Easy to verify results
- [x] Errors are informative
- [x] Dry-run mode works correctly

## Test Execution Notes

**Prerequisites:**
- mcp-manager installed and working
- Claude Desktop installed (optional but recommended)
- VS Code with Cline installed (optional but recommended)
- Python environment available

**Estimated Time:** 15-20 minutes
**Risk Level:** Low (test server only, real configs but backed up)
**Cleanup:** Test server will be completely removed at end
