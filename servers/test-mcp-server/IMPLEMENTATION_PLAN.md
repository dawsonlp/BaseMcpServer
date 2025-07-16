# Minimal Streamable HTTP MCP Server Implementation Plan

## Objective
Create the simplest possible MCP server using streamable HTTP transport that runs reliably without port conflicts or configuration errors.

## Pre-Implementation Analysis
- **Current Issue**: Port 8000 conflicts, incorrect FastMCP.run() parameters
- **Root Cause**: Lack of proper port management and incorrect API usage
- **Success Criteria**: Server runs on available port, responds to MCP protocol requests

## Implementation Checklist

### Phase 1: Environment Preparation
- [ ] Check current port usage (lsof -i :8000, :8001, :8002)
- [ ] Kill any existing test server processes
- [ ] Verify MCP dependencies are installed
- [ ] Choose available port (default: 8001)

### Phase 2: Server Configuration
- [ ] Update server.py with correct FastMCP.run() syntax (no host/port params)
- [ ] Add environment variable support for port (PORT env var)
- [ ] Add basic logging to show server startup info
- [ ] Add error handling for startup failures
- [ ] Test server.py syntax without running

### Phase 3: Startup Script Creation
- [ ] Create run.sh script with:
  - [ ] Port availability check
  - [ ] Process cleanup (kill existing on same port)
  - [ ] Environment variable setup
  - [ ] nohup execution for persistence
  - [ ] Log file redirection
- [ ] Make run.sh executable (chmod +x)
- [ ] Test run.sh script execution

### Phase 4: Basic Functionality Testing
- [ ] Start server using run.sh
- [ ] Verify server is listening on correct port (lsof check)
- [ ] Check server logs for startup success
- [ ] Test MCP protocol endpoint with curl:
  - [ ] POST to /mcp with tools/list request
  - [ ] Verify JSON-RPC response format
  - [ ] Test hello tool with sample input

### Phase 5: Documentation
- [ ] Create README.md with:
  - [ ] Usage instructions
  - [ ] Port and endpoint information
  - [ ] Example curl commands
  - [ ] Troubleshooting section

### Phase 6: Cleanup and Validation
- [ ] Test server restart persistence
- [ ] Verify no port conflicts after restart
- [ ] Confirm server responds after system restart
- [ ] Document final working configuration

## Error Handling Strategy
- **Port Conflicts**: Check and kill processes before starting
- **Startup Failures**: Log errors to file, provide clear error messages
- **Process Management**: Use proper nohup and process cleanup
- **Configuration Issues**: Validate environment before starting

## Files to Create/Modify
1. `servers/test-mcp-server/server.py` - Fixed MCP server
2. `servers/test-mcp-server/run.sh` - Startup script
3. `servers/test-mcp-server/README.md` - Usage documentation

## Success Validation
- [ ] Server starts without errors
- [ ] Server responds to MCP protocol requests
- [ ] Server persists across terminal restarts
- [ ] No port conflicts or binding errors
- [ ] Clear documentation for usage

## Implementation Notes
- Use port 8001 as default to avoid conflicts with existing services on 8000
- FastMCP.run() method only accepts transport parameter, not host/port
- Use environment variables for configuration flexibility
- Implement proper process management for production-like behavior
