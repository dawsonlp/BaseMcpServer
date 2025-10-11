# MCP Manager Help System Consolidation & Config Standardization

## Project Overview
Consolidate help/info commands for better user experience and standardize config file locations across all servers with backward compatibility.

## Phase 1: Command Structure Redesign
- [ ] 1.1 Enhance `help` command to be comprehensive information source
- [ ] 1.2 Move system overview from redundant `info` commands into `help`
- [ ] 1.3 Add file location section to `help` command
- [ ] 1.4 Keep focused `info` commands: `list` and `show` for specific server queries
- [ ] 1.5 Remove redundant `info tree` and `info summary` commands

## Phase 2: Enhanced Help Content
- [ ] 2.1 Add "File Locations" section showing config search order
- [ ] 2.2 Add log file location information  
- [ ] 2.3 Add virtual environment paths
- [ ] 2.4 Include example commands for finding config/log files

## Phase 3: Enhanced Info Commands
- [ ] 3.1 Enhance `info show {server}` to display actual file paths being used
- [ ] 3.2 Add indicators showing which config file is active vs. available
- [ ] 3.3 Show log file locations and sizes

## Phase 4: Server Config Standardization
- [x] 4.1 Complete jira-helper config path updates (✅ DONE)
- [x] 4.2 Update worldcontext config path logic (✅ DONE)  
- [x] 4.3 Update template server config path logic (✅ DONE)
- [x] 4.4 Update mcpservercreator config path logic (✅ DONE)
- [x] 4.5 Ensure all servers follow precedence: mcp-manager → legacy → local (✅ DONE)

## Phase 5: Testing & Documentation
- [ ] 5.1 Test backward compatibility with existing deployments
- [ ] 5.2 Create migration guide for users with custom config locations
- [ ] 5.3 Update README files with standardized config patterns
- [ ] 5.4 Test all servers can find configs in expected locations

## Config File Precedence Standard

All servers should follow this standardized config lookup order:

1. **MCP-Manager Managed**: `~/.config/mcp-manager/servers/{server-name}/config.yaml`
2. **Legacy Locations**: Server-specific legacy paths for backward compatibility
3. **Local Development**: `./config.yaml` 
4. **Example Template**: `./config.yaml.example` (fallback)

## Implementation Notes

### File Structure
- **Config files**: `~/.config/mcp-manager/servers/{server-name}/config.yaml`
- **Log files**: `~/.config/mcp-manager/logs/{server-name}.log`
- **Virtual environments**: `~/.config/mcp-manager/servers/{server-name}/.venv`

### Backward Compatibility
- Maintain support for existing config file locations
- Clear logging about which config file is being used
- Migration hints for users with custom locations

### Help System Design
- Single comprehensive `help` command with all information
- Focused `info` commands for specific operational queries
- Clear file location guidance where users expect to find it

## Testing Checklist
- [ ] Existing jira-helper deployments continue to work
- [ ] New mcp-manager deployments use correct paths
- [ ] Help system shows accurate file locations
- [ ] Config file precedence works as documented
- [ ] All servers follow the same config pattern

## Success Criteria
- Users can easily find config and log file locations
- No existing deployments are broken
- Consistent config management across all servers
- Simplified, non-redundant help system
