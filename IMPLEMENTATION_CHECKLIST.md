# MCP Server Configuration Standardization - Implementation Checklist

## Overview

This checklist guides the migration from `python-dotenv` to `python-decouple` across all MCP servers.

**Reference**: See `CONFIG_STANDARDIZATION.md` for detailed rationale and standards.

## Pre-Implementation Checklist

- [ ] Review `CONFIG_STANDARDIZATION.md`
- [ ] Backup current server configurations
- [ ] Ensure all servers are currently functional
- [ ] Document current .env file locations and formats

## Phase 1: Requirements File Updates

### Update requirements.txt files

- [ ] **jira-helper**: Replace `python-dotenv>=1.1.1` with `python-decouple>=3.8`
- [ ] **document-processor**: Replace `python-dotenv>=1.1.1` with `python-decouple>=3.8`
- [ ] **mcpservercreator**: Replace `python-dotenv>=1.1.1` with `python-decouple>=3.8`
- [ ] **template**: Replace `python-dotenv>=1.1.1` with `python-decouple>=3.8`

### Verify requirements consistency

- [ ] All servers use `python-decouple>=3.8`
- [ ] All servers use consistent MCP core dependencies
- [ ] No servers still reference `python-dotenv`

## Phase 2: Configuration Code Updates

### jira-helper config.py

- [ ] Replace `from python_dotenv import load_dotenv` with `from decouple import config`
- [ ] Remove `load_dotenv()` calls
- [ ] Update JIRA_INSTANCES parsing to use decouple
- [ ] Test multi-line JSON parsing specifically
- [ ] Verify all environment variables load correctly

### document-processor config.py

- [ ] Replace `from python_dotenv import load_dotenv` with `from decouple import config`
- [ ] Remove `load_dotenv()` calls
- [ ] Update any complex configuration parsing
- [ ] Verify all environment variables load correctly

### mcpservercreator config.py

- [ ] Replace `from python_dotenv import load_dotenv` with `from decouple import config`
- [ ] Remove `load_dotenv()` calls
- [ ] Update any complex configuration parsing
- [ ] Verify all environment variables load correctly

### template config.py

- [ ] Replace `from python_dotenv import load_dotenv` with `from decouple import config`
- [ ] Remove `load_dotenv()` calls
- [ ] Ensure template serves as good example for new servers
- [ ] Add comments explaining decouple usage patterns

## Phase 3: Server Redeployment

### Redeploy each server with updated dependencies

- [ ] **jira-helper**: `mcp-manager install local jira-helper --source servers/jira-helper --force`
- [ ] **document-processor**: `mcp-manager install local document-processor --source servers/document-processor --force`
- [ ] **mcpservercreator**: `mcp-manager install local mcpservercreator --source servers/mcpservercreator --force`

### Verify installations

- [ ] All servers install without dependency errors
- [ ] All virtual environments contain python-decouple
- [ ] No servers contain python-dotenv in their venv

## Phase 4: Functional Testing

### jira-helper testing (Primary focus)

- [ ] Server starts without configuration parsing errors
- [ ] Multi-line JIRA_INSTANCES JSON parses correctly
- [ ] Can list Jira projects successfully
- [ ] All Jira tools function as expected
- [ ] No python-dotenv parsing warnings in logs

### document-processor testing

- [ ] Server starts without configuration parsing errors
- [ ] All document processing tools function
- [ ] Configuration loads correctly

### mcpservercreator testing

- [ ] Server starts without configuration parsing errors
- [ ] Can create new MCP servers successfully
- [ ] All server creation tools function

### Integration testing

- [ ] All servers can be used simultaneously
- [ ] No configuration conflicts between servers
- [ ] MCP client connections work properly

## Phase 5: Validation and Cleanup

### Code review

- [ ] No remaining references to python-dotenv in any server code
- [ ] All config.py files follow the standardized pattern
- [ ] All requirements.txt files are consistent
- [ ] Template server is properly updated for future use

### Documentation updates

- [ ] Update any server-specific README files
- [ ] Update deployment documentation
- [ ] Mark CONFIG_STANDARDIZATION.md as "Implemented"

### Environment verification

- [ ] Existing .env files work without modification
- [ ] Complex configuration values (JSON) parse correctly
- [ ] All environment variables are accessible

## Rollback Procedures (If Needed)

### Quick rollback steps

1. [ ] Revert all requirements.txt files to use python-dotenv
2. [ ] Revert all config.py files to original state
3. [ ] Redeploy all servers with original dependencies
4. [ ] Verify functionality restored
5. [ ] Document issues encountered for future resolution

### Rollback verification

- [ ] All servers functional with original configuration
- [ ] No residual python-decouple dependencies
- [ ] Original .env parsing behavior restored

## Success Criteria

- [ ] All servers start without configuration errors
- [ ] jira-helper successfully parses multi-line JSON configuration
- [ ] All MCP tools and resources function correctly
- [ ] No python-dotenv dependencies remain in any server
- [ ] Configuration approach is consistent across all servers
- [ ] Template server provides good example for future development

## Post-Implementation

### Monitoring

- [ ] Monitor server logs for configuration-related errors
- [ ] Verify stable operation over 24-48 hours
- [ ] Check for any performance impacts

### Documentation

- [ ] Update project documentation to reflect new standard
- [ ] Create developer guidelines for future server configuration
- [ ] Archive this checklist as completed

---

**Implementation Date**: January 13, 2025  
**Implementer**: [To be filled]  
**Status**: In Progress  
**Completion Date**: [To be filled]

## Notes

Use this space to document any issues, deviations, or additional steps taken during implementation:

- 
- 
-
