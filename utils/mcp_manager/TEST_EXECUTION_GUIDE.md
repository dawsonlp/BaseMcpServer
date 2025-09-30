# MCP Manager Removal - Test Execution Guide

## Overview

This guide walks you through running the functional test for MCP Manager's removal commands. The test validates complete removal workflow using a temporary test server.

## What This Test Does

The test script (`test_removal_functionality.py`) performs an automated, end-to-end test of the removal functionality:

1. **Phase 1: Setup** - Installs test server and configures for both platforms
2. **Phase 2: Remove from Claude** - Tests platform-specific removal (Claude Desktop)
3. **Phase 3: Remove from Cline** - Tests platform-specific removal (Cline)
4. **Phase 4: Remove from Registry** - Tests registry removal with file cleanup
5. **Phase 5: Complete Removal** - Tests single-command complete removal

At each phase, the script:
- ✅ Runs removal commands automatically
- ✅ Verifies config files are updated correctly
- ✅ Checks that files are cleaned up properly
- ✅ Prompts you to verify functionality in applications

## Prerequisites

### Required:
- ✅ mcp-manager installed and working
- ✅ Python 3.10+ available
- ✅ Terminal access

### Recommended:
- ✅ Claude Desktop installed (for complete testing)
- ✅ VS Code with Cline extension installed (for complete testing)

**Note:** The test can still run without Claude Desktop or Cline installed - it will skip the manual verification steps for those platforms.

## Before You Start

### 1. Backup Safety
The test will automatically create backups, but it's good practice to ensure:
- You have no unsaved work in Claude Desktop
- You have no unsaved work in VS Code/Cline
- You're comfortable with the test modifying your MCP configurations

### 2. Time Estimate
- **Full test:** 15-20 minutes
- **Automated checks only:** 5 minutes (if you skip manual platform verification)

### 3. What Gets Modified
The test will temporarily:
- Add/remove "test-echo-server" from mcp-manager registry
- Add/remove "test-echo-server" from Claude Desktop config
- Add/remove "test-echo-server" from Cline config
- Create/remove files in `~/.config/mcp-manager/servers/test-echo-server/`

**All changes are reverted by end of test!**

## Running the Test

### Step 1: Navigate to the test directory
```bash
cd /path/to/BaseMcpServer/utils/mcp_manager
```

### Step 2: Run the test script
```bash
python3 test_removal_functionality.py
```

or

```bash
./test_removal_functionality.py
```

### Step 3: Follow the prompts

The test is interactive and will:
1. Show colored output indicating progress
2. Pause at verification points
3. Ask you to manually check functionality in applications
4. Continue automatically after you confirm

## What You'll Need to Do

### During Phase 1 (Setup):
After installation, you'll be asked to:
1. Open Claude Desktop
2. Look for `test_echo` tool in the tools list
3. Test the tool - it should return: "🧪 TEST-ECHO-SERVER IS WORKING! 🎉"
4. Open VS Code with Cline
5. Look for `test_echo` tool
6. Test it in Cline

Type `yes` when both work correctly.

### During Phase 2 (Remove from Claude):
After removal, you'll be asked to:
1. Restart Claude Desktop
2. Verify `test_echo` tool is NO LONGER available
3. Check Cline still has the tool

Type `yes` to confirm.

### During Phase 3 (Remove from Cline):
After removal, you'll be asked to:
1. Restart VS Code / Reload Cline
2. Verify `test_echo` tool is NO LONGER available in Cline
3. Confirm Claude Desktop also doesn't have it

Type `yes` to confirm.

### During Phases 4 & 5:
These are fully automated - just watch the progress!

## Interpreting Results

### Success Output
```
================================================================================
                              TEST COMPLETE ✓                                  
================================================================================

All tests passed!

Summary:
  ✓ Server can be removed from individual platforms
  ✓ Server can be removed from registry with file cleanup
  ✓ Server can be completely removed in one command
  ✓ Configs are updated correctly
  ✓ Files are cleaned up properly
  ✓ Backups are created automatically

The removal functionality is working correctly!
```

### If Test Fails
The script will show:
- ✗ Clear error messages indicating what failed
- Which phase failed
- What to check manually

Common issues:
- **"Server not found in registry"** - mcp-manager may not be properly installed
- **"Tool not working"** - May need to restart applications
- **"Config file not found"** - Platform may not be installed or configured

## What Gets Left Behind

### After Successful Test:
- ✅ All test server entries removed
- ✅ All test server files cleaned up
- ✅ Your original configs restored (via automatic backups)
- ✅ Backup files in `~/.config/mcp-manager/backups/` (these are safe to delete)

### To Clean Up Backups (optional):
```bash
rm -rf ~/.config/mcp-manager/backups/
```

## Troubleshooting

### Test Won't Start
**Problem:** Script won't run  
**Solution:** Ensure it's executable: `chmod +x test_removal_functionality.py`

### mcp-manager Commands Fail
**Problem:** "mcp-manager: command not found"  
**Solution:** Ensure mcp-manager is installed and in your PATH

### Server Won't Install
**Problem:** Installation fails  
**Solution:** Check that the test-echo-server directory exists and has all files

### Tools Don't Appear in Applications
**Problem:** test_echo tool not visible  
**Solution:** 
1. Restart the application completely
2. Check application logs for MCP connection errors
3. Verify config files manually

### Test Hangs
**Problem:** Test appears stuck  
**Solution:** Press Ctrl+C to cancel, check application logs

## Manual Verification (Alternative)

If you prefer to test manually without the script:

### 1. Install Test Server
```bash
cd utils/mcp_manager
mcp-manager install local test-echo-server --source test-echo-server
```

### 2. Configure Platforms
```bash
mcp-manager config claude
mcp-manager config cline
```

### 3. Test Removal Commands
```bash
# Remove from one platform
mcp-manager remove from-claude test-echo-server --yes

# Remove from other platform
mcp-manager remove from-cline test-echo-server --yes

# Complete removal
mcp-manager remove server test-echo-server --yes
```

### 4. Verify Each Step
Check config files manually at:
- Claude: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Cline: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Registry: `~/.config/mcp-manager/servers/servers.json`

## Questions?

If you encounter issues or have questions about the test:
1. Check the `FUNCTIONAL_TEST_PLAN.md` for detailed test phases
2. Review the test script itself for implementation details
3. Check mcp-manager logs: `~/.config/mcp-manager/logs/`

## Summary

This test validates that:
- ✅ Servers can be removed from individual platforms
- ✅ Servers can be removed from registry only
- ✅ Complete removal works in one command
- ✅ Configs are updated correctly
- ✅ Files are cleaned up properly
- ✅ Backups are created automatically
- ✅ No damage to other configured servers

**Ready to run the test? Navigate to the directory and execute `./test_removal_functionality.py`!**
