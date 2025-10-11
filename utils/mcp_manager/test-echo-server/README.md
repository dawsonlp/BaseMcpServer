# Test Echo Server

A minimal MCP server for testing mcp-manager removal functionality.

## Purpose

This server provides a single `test_echo` tool that returns a unique, easily identifiable message. This makes it perfect for testing whether the server is properly installed and working in Claude Desktop and Cline.

## Tool

**test_echo**
- Description: Returns a test message to verify server is working
- Input: Optional `message` parameter (string)
- Output: Test message confirming the server is functioning

## Expected Response

When you use the tool, you should see:
```
✅ Test Echo Response: 🧪 TEST-ECHO-SERVER IS WORKING! 🎉

This confirms the test-echo-server MCP server is installed and functioning correctly in this environment.
```

## Installation

This server is installed automatically by the functional test script. To install manually:

```bash
mcp-manager install local test-echo-server --source /path/to/test-echo-server
```

## Usage in Tests

This server is used by `test_removal_functionality.py` to validate:
1. Server installation via mcp-manager
2. Platform configuration (Claude Desktop & Cline)
3. Step-by-step removal from each location
4. File cleanup verification
5. Complete removal workflow

## Dependencies

- Python 3.10+
- mcp >= 1.0.0 (installed automatically)

## Files

- `src/main.py` - Main server implementation
- `pyproject.toml` - Package configuration
- `README.md` - This file
