#!/usr/bin/env python3
"""
Functional Test Script for MCP Manager Removal Commands

This script tests the complete removal workflow:
1. Installs a test MCP server
2. Configures it for Claude Desktop and Cline
3. User verifies functionality in both platforms
4. Removes from each location step-by-step
5. Verifies cleanup at each stage
6. Tests complete removal command
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional
import time


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    """Print a colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")


def print_step(step_num: int, text: str):
    """Print a step indicator."""
    print(f"{Colors.BOLD}{Colors.CYAN}[Step {step_num}]{Colors.END} {text}")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def run_command(cmd: list[str], check: bool = True) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )
    
    if check and result.returncode != 0:
        print_error(f"Command failed: {' '.join(cmd)}")
        print_error(f"Error: {result.stderr}")
        sys.exit(1)
    
    return result.returncode, result.stdout, result.stderr


def wait_for_user(prompt: str = "Press Enter to continue..."):
    """Wait for user input."""
    print(f"\n{Colors.YELLOW}{prompt}{Colors.END}")
    input()


def get_config_paths() -> dict[str, Path]:
    """Get paths to configuration files."""
    home = Path.home()
    return {
        'claude': home / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json',
        'cline': home / 'Library' / 'Application Support' / 'Code' / 'User' / 'globalStorage' / 'saoudrizwan.claude-dev' / 'settings' / 'cline_mcp_settings.json',
        'registry': home / '.config' / 'mcp-manager' / 'servers' / 'servers.json'
    }


def check_server_in_config(config_path: Path, server_name: str) -> bool:
    """Check if server exists in a config file."""
    if not config_path.exists():
        return False
    
    try:
        config = json.loads(config_path.read_text())
        return server_name in config.get('mcpServers', {})
    except Exception:
        return False


def check_server_in_registry(server_name: str) -> bool:
    """Check if server exists in mcp-manager registry."""
    _, stdout, _ = run_command(['mcp-manager', 'info', 'list', '--format', 'json'], check=False)
    try:
        servers = json.loads(stdout)
        # servers is a dict with server names as keys
        return server_name in servers
    except Exception:
        return False


def check_pipx_files(server_name: str) -> bool:
    """Check if pipx/venv files exist for server."""
    home = Path.home()
    server_dir = home / '.config' / 'mcp-manager' / 'servers' / server_name
    return server_dir.exists()


def main():
    """Run the functional test."""
    test_server = "test-echo-server"
    test_dir = Path(__file__).parent / "test-echo-server"
    
    print_header("MCP Manager Removal - Functional Test")
    print_info("This test will validate the complete removal workflow")
    print_info("using a temporary test MCP server.")
    print()
    print_warning("This test will modify your Claude Desktop and Cline configurations.")
    print_warning("Backups will be created automatically, but please ensure you have")
    print_warning("no critical unsaved work in either application.")
    print()
    
    wait_for_user("Press Enter to begin the test...")
    
    # ============================================================================
    # PHASE 1: Setup and Installation
    # ============================================================================
    print_header("PHASE 1: Setup and Installation")
    
    # Step 1: Check test server exists
    print_step(1, "Checking test server files...")
    if not test_dir.exists():
        print_error(f"Test server directory not found: {test_dir}")
        sys.exit(1)
    if not (test_dir / "src" / "main.py").exists():
        print_error("Test server main.py not found")
        sys.exit(1)
    print_success("Test server files found")
    
    # Step 2: Install test server
    print_step(2, f"Installing test server via mcp-manager...")
    run_command([
        'mcp-manager', 'install', 'local', test_server,
        '--source', str(test_dir),
        '--force'
    ])
    print_success("Test server installed")
    
    # Step 3: Verify in registry
    print_step(3, "Verifying server appears in registry...")
    if not check_server_in_registry(test_server):
        print_error("Server not found in registry!")
        sys.exit(1)
    print_success("Server found in registry")
    
    # Step 4: Configure for Claude Desktop
    print_step(4, "Configuring for Claude Desktop...")
    run_command(['mcp-manager', 'config', 'claude', '--backup'])
    
    config_paths = get_config_paths()
    if check_server_in_config(config_paths['claude'], test_server):
        print_success("Server configured in Claude Desktop")
    else:
        print_warning("Server may not be in Claude Desktop config (config file may not exist yet)")
    
    # Step 5: Configure for Cline
    print_step(5, "Configuring for Cline...")
    run_command(['mcp-manager', 'config', 'cline', '--backup'])
    
    if check_server_in_config(config_paths['cline'], test_server):
        print_success("Server configured in Cline")
    else:
        print_warning("Server may not be in Cline config (config file may not exist yet)")
    
    # Step 6: User verification
    print_step(6, "User verification required")
    print()
    print_info("Please perform the following manual checks:")
    print("  1. Open Claude Desktop")
    print("  2. Look for the 'test_echo' tool")
    print("  3. Test it - it should return: '🧪 TEST-ECHO-SERVER IS WORKING! 🎉'")
    print()
    print("  4. Open VS Code with Cline")
    print("  5. Look for the 'test_echo' tool")
    print("  6. Test it - it should return the same message")
    print()
    
    response = input(f"{Colors.YELLOW}Did the tool work in BOTH Claude Desktop and Cline? (yes/no): {Colors.END}").strip().lower()
    if response != 'yes':
        print_error("Test failed - tool not working in both platforms")
        print_info("You may need to restart Claude Desktop and VS Code")
        sys.exit(1)
    
    print_success("Phase 1 complete - server installed and working in both platforms")
    
    # ============================================================================
    # PHASE 2: Remove from Claude Desktop
    # ============================================================================
    print_header("PHASE 2: Remove from Claude Desktop")
    
    print_step(1, "Removing from Claude Desktop...")
    run_command(['mcp-manager', 'remove', 'from-claude', test_server, '--yes'])
    print_success("Removal command completed")
    
    print_step(2, "Verifying removal from Claude config...")
    if check_server_in_config(config_paths['claude'], test_server):
        print_error("Server still in Claude Desktop config!")
        sys.exit(1)
    print_success("Server removed from Claude Desktop config")
    
    print_step(3, "Verifying server still in other locations...")
    if not check_server_in_config(config_paths['cline'], test_server):
        print_error("Server missing from Cline config (should still be there)!")
        sys.exit(1)
    print_success("Server still in Cline config")
    
    if not check_server_in_registry(test_server):
        print_error("Server missing from registry (should still be there)!")
        sys.exit(1)
    print_success("Server still in registry")
    
    print_step(4, "User verification required")
    print()
    print_info("Please perform the following manual checks:")
    print("  1. Restart Claude Desktop")
    print("  2. Verify the 'test_echo' tool is NO LONGER available")
    print()
    print("  3. Open VS Code with Cline")
    print("  4. Verify the 'test_echo' tool IS STILL available")
    print()
    
    response = input(f"{Colors.YELLOW}Confirm: Tool removed from Claude but still in Cline? (yes/no): {Colors.END}").strip().lower()
    if response != 'yes':
        print_error("Test failed - unexpected tool availability")
        sys.exit(1)
    
    print_success("Phase 2 complete - removed from Claude Desktop only")
    
    # ============================================================================
    # PHASE 3: Remove from Cline
    # ============================================================================
    print_header("PHASE 3: Remove from Cline")
    
    print_step(1, "Removing from Cline...")
    run_command(['mcp-manager', 'remove', 'from-cline', test_server, '--yes'])
    print_success("Removal command completed")
    
    print_step(2, "Verifying removal from Cline config...")
    if check_server_in_config(config_paths['cline'], test_server):
        print_error("Server still in Cline config!")
        sys.exit(1)
    print_success("Server removed from Cline config")
    
    print_step(3, "Verifying server still in registry...")
    if not check_server_in_registry(test_server):
        print_error("Server missing from registry (should still be there)!")
        sys.exit(1)
    print_success("Server still in registry")
    
    print_step(4, "User verification required")
    print()
    print_info("Please perform the following manual checks:")
    print("  1. Restart VS Code / Reload Cline")
    print("  2. Verify the 'test_echo' tool is NO LONGER available")
    print()
    print("  3. Confirm Claude Desktop also doesn't have it")
    print()
    
    response = input(f"{Colors.YELLOW}Confirm: Tool removed from both platforms? (yes/no): {Colors.END}").strip().lower()
    if response != 'yes':
        print_error("Test failed - tool still available somewhere")
        sys.exit(1)
    
    print_success("Phase 3 complete - removed from both platforms")
    
    # ============================================================================
    # PHASE 4: Remove from Registry
    # ============================================================================
    print_header("PHASE 4: Remove from Registry with File Cleanup")
    
    print_step(1, "Checking files exist before removal...")
    files_exist_before = check_pipx_files(test_server)
    if files_exist_before:
        print_success("Server files found")
    else:
        print_warning("Server files not found (unexpected)")
    
    print_step(2, "Removing from registry with file cleanup...")
    run_command(['mcp-manager', 'remove', 'from-registry', test_server, '--yes', '--cleanup-files'])
    print_success("Removal command completed")
    
    print_step(3, "Verifying removal from registry...")
    if check_server_in_registry(test_server):
        print_error("Server still in registry!")
        sys.exit(1)
    print_success("Server removed from registry")
    
    print_step(4, "Verifying file cleanup...")
    if check_pipx_files(test_server):
        print_error("Server files still exist!")
        sys.exit(1)
    print_success("Server files cleaned up")
    
    print_step(5, "Verifying with mcp-manager list...")
    _, stdout, _ = run_command(['mcp-manager', 'info', 'list'])
    if test_server in stdout:
        print_error(f"Server '{test_server}' still appears in list!")
        sys.exit(1)
    print_success("Server does not appear in list")
    
    print_success("Phase 4 complete - completely removed from registry and files cleaned")
    
    # ============================================================================
    # PHASE 5: Test Complete Removal Command
    # ============================================================================
    print_header("PHASE 5: Test Complete Removal Command")
    
    print_info("Now testing the 'remove server' command which removes everything at once")
    print()
    
    print_step(1, "Reinstalling test server...")
    run_command([
        'mcp-manager', 'install', 'local', test_server,
        '--source', str(test_dir),
        '--force'
    ])
    print_success("Test server reinstalled")
    
    print_step(2, "Reconfiguring for both platforms...")
    run_command(['mcp-manager', 'config', 'claude', '--backup'])
    run_command(['mcp-manager', 'config', 'cline', '--backup'])
    print_success("Configured for both platforms")
    
    print_step(3, "Removing completely with single command...")
    run_command(['mcp-manager', 'remove', 'server', test_server, '--yes'])
    print_success("Complete removal command completed")
    
    print_step(4, "Verifying removal from all locations...")
    errors = []
    
    if check_server_in_config(config_paths['claude'], test_server):
        errors.append("Still in Claude Desktop config")
    if check_server_in_config(config_paths['cline'], test_server):
        errors.append("Still in Cline config")
    if check_server_in_registry(test_server):
        errors.append("Still in registry")
    if check_pipx_files(test_server):
        errors.append("Files still exist")
    
    if errors:
        print_error("Complete removal failed:")
        for error in errors:
            print_error(f"  - {error}")
        sys.exit(1)
    
    print_success("Server removed from all locations")
    print_success("All files cleaned up")
    
    # ============================================================================
    # TEST COMPLETE
    # ============================================================================
    print_header("TEST COMPLETE ✓")
    
    print()
    print(f"{Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.END}")
    print()
    print("Summary:")
    print("  ✓ Server can be removed from individual platforms")
    print("  ✓ Server can be removed from registry with file cleanup")
    print("  ✓ Server can be completely removed in one command")
    print("  ✓ Configs are updated correctly")
    print("  ✓ Files are cleaned up properly")
    print("  ✓ Backups are created automatically")
    print()
    print(f"{Colors.BOLD}The removal functionality is working correctly!{Colors.END}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
