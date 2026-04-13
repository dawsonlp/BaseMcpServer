# MCP Client Support Research

## Overview
This document provides research findings and configuration details for MCP server support across different AI client applications, specifically for extending mcp-manager to support additional clients beyond Cline and Claude Desktop.

**Date**: October 23, 2025  
**Purpose**: Enable mcp-manager to configure MCP servers for Claude Code and ChatGPT

---

## Currently Supported Clients

### 1. Cline (VS Code Extension)
- **Config File**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Status**: ✅ Fully Supported
- **Format**:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "/path/to/executable",
      "args": ["stdio"],
      "env": {}
    }
  }
}
```

### 2. Claude Desktop
- **Config File**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Status**: ✅ Fully Supported  
- **Format**:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "/path/to/executable",
      "args": ["stdio"],
      "env": {}
    }
  }
}
```

---

## Proposed New Clients

### 3. Claude Code

#### Research Summary
- **Official Documentation**: https://docs.claude.com/en/docs/claude-code/mcp
- **Status**: ✅ MCP Support Confirmed
- **Config File**: `~/.claude.json`
- **Config Complexity**: Medium-High (large JSON with project-specific settings)

#### Key Features
- Global MCP server configuration
- Project-specific MCP server overrides
- Three-tier precedence hierarchy:
  1. Project-scoped servers (highest priority)
  2. Local-scoped servers
  3. Global-scoped servers (lowest priority)

#### Configuration Structure

The `~/.claude.json` file is a complex configuration file that includes:
- User settings
- Project histories
- Per-project MCP configurations

**Global MCP Servers Section**:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {
        "API_KEY": "your_key_here"
      }
    }
  }
}
```

**Project-Specific MCP Servers** (within projects object):
```json
{
  "projects": {
    "/path/to/project": {
      "mcpServers": {
        "project-specific-server": {
          "command": "/path/to/command",
          "args": ["stdio"]
        }
      },
      "enabledMcpjsonServers": [],
      "disabledMcpjsonServers": []
    }
  }
}
```

#### Configuration Methods
1. **CLI Wizard**: `claude mcp add` (interactive)
2. **Direct Edit**: Edit `~/.claude.json` manually
3. **Project-Local**: Create `.mcp.json` in project root (highest precedence)

#### Implementation Considerations
- File is large (~42KB typically) with many settings
- Need to preserve existing structure when updating
- Project-specific configurations add complexity
- Need to handle three different scopes (global, project, local)

#### Recommended Approach
- **Global Configuration**: Add servers to top-level `mcpServers` object
- **Backup Strategy**: Always backup before modification
- **Validation**: Validate JSON structure after changes
- **Scope**: Start with global-level support, add project-specific support later

---

### 4. ChatGPT (OpenAI)

#### Research Summary
- **Official Documentation**: 
  - https://platform.openai.com/docs/guides/developer-mode
  - https://platform.openai.com/docs/mcp
  - https://openai.github.io/openai-agents-python/mcp/
- **Status**: ⚠️ MCP Support Available (Limited Implementation)
- **Configuration**: Via OpenAI Developer Mode or Agents SDK (not simple JSON config)

#### Key Features
- MCP support in **ChatGPT Developer Mode** (beta feature)
- MCP support in **OpenAI Agents SDK** (for custom apps)
- **Deep Research** connectors for workspace admins (beta)
- **Hosted MCP Tools** through Responses API

#### Implementation Methods

##### Option 1: Developer Mode (ChatGPT Web/Desktop)
- **Access**: ChatGPT Plus/Pro users with Developer Mode enabled
- **Configuration**: Through ChatGPT UI, not a config file
- **Setup Process**:
  1. Enable Developer Mode in ChatGPT settings
  2. Add MCP servers through the UI
  3. Servers run locally and connect to ChatGPT

**Limitation**: No direct config file access for automation

##### Option 2: OpenAI Agents SDK (Programmatic)
- **Target**: Custom applications using OpenAI Agents SDK
- **Configuration**: Python code-based, not JSON config file
- **Example**:
```python
from openai import OpenAI
from openai.agents import HostedMCPTool

client = OpenAI()

agent = client.agents.create(
    model="gpt-4",
    tools=[
        HostedMCPTool(
            server_label="your-mcp-server",
            connector_metadata={
                "command": "/path/to/server",
                "args": ["stdio"]
            }
        )
    ]
)
```

##### Option 3: Apps SDK (Custom GPTs)
- **Target**: Custom GPT applications
- **Documentation**: https://developers.openai.com/apps-sdk/concepts/mcp-server/
- **Configuration**: Through Apps SDK, not config file

#### Implementation Challenges
1. **No Standard Config File**: Unlike Cline/Claude, no `~/.chatgpt_config.json` exists
2. **UI-Based Setup**: Requires manual configuration through ChatGPT interface
3. **SDK-Based**: Programmatic configuration requires OpenAI Agents SDK
4. **Authentication**: Requires OpenAI API keys for SDK approach
5. **Platform Variability**: Different for web, desktop, and API usage

#### Recommended Approach
**Cannot directly support through mcp-manager** due to lack of config file. Options:
1. **Documentation Only**: Provide instructions for manual ChatGPT setup
2. **SDK Helper**: Create separate tool for OpenAI Agents SDK integration
3. **Wait for Desktop App**: OpenAI announced MCP support coming to ChatGPT desktop app
4. **Hybrid Approach**: Support documentation + optional SDK integration

---

## Implementation Priority

### Phase 1: Claude Code Support ✅ HIGH PRIORITY
**Rationale**: 
- Has standard JSON config file (~/.claude.json)
- Similar structure to existing supported clients
- Can be automated through mcp-manager
- Active user base with MCP interest

**Implementation Complexity**: Medium
- More complex than Cline/Claude Desktop (larger file, project scopes)
- Requires careful JSON manipulation to preserve existing settings
- Need to handle global vs project-specific configurations

**Recommended Implementation**:
1. Add `claude-code` as a new configuration target
2. Implement global-level MCP server configuration first
3. Backup entire file before modifications
4. Parse JSON, add to `mcpServers` section, write back
5. Add project-specific support in Phase 2

### Phase 2: ChatGPT Support 🔶 MEDIUM PRIORITY
**Rationale**:
- Growing MCP support but no config file access
- Different implementation approach needed
- May become easier with desktop app release

**Implementation Complexity**: High
- No direct config file to manipulate
- Requires either:
  - Documentation-only approach (Easy)
  - OpenAI Agents SDK integration (Hard)
  - Wait for desktop app with config file (TBD)

**Recommended Implementation**:
1. **Short-term**: Create comprehensive documentation for manual setup
2. **Mid-term**: Monitor OpenAI desktop app development
3. **Long-term**: Consider SDK integration if demand warrants

---

## Configuration File Locations Summary

| Client | Platform | Config File Location | Format |
|--------|----------|---------------------|---------|
| **Cline** | VS Code | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` | JSON |
| **Claude Desktop** | Standalone | `~/Library/Application Support/Claude/claude_desktop_config.json` | JSON |
| **Claude Code** | CLI/Editor | `~/.claude.json` | JSON (Complex) |
| **ChatGPT** | Web/Desktop | N/A (UI-based or SDK) | N/A |

---

## mcp-manager Extension Design

### New Command Structure

```bash
# Current supported
mcp-manager config cline
mcp-manager config claude

# Proposed additions
mcp-manager config claude-code      # Phase 1
mcp-manager config chatgpt          # Phase 2 (documentation mode)
```

### Implementation Plan

#### Phase 1: Claude Code Support

**1. Add Configuration Target**
```python
# In cli/commands/config.py
SUPPORTED_EDITORS = ["cline", "claude", "claude-code"]

EDITOR_CONFIG_PATHS = {
    "cline": "~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    "claude": "~/Library/Application Support/Claude/claude_desktop_config.json",
    "claude-code": "~/.claude.json"
}
```

**2. Implement Claude Code Handler**
```python
class ClaudeCodeConfigHandler:
    """Handle Claude Code configuration with complex JSON structure"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        
    def backup(self) -> Path:
        """Create backup of entire config file"""
        
    def load(self) -> dict:
        """Load and parse complex JSON structure"""
        
    def add_servers(self, servers: list[ServerConfig]) -> None:
        """Add MCP servers to global mcpServers section"""
        
    def save(self, config: dict) -> None:
        """Save config while preserving structure"""
```

**3. Update CLI Command**
```python
@app.command()
def config(
    editor: str = typer.Argument(..., help="Editor: cline, claude, or claude-code"),
    project_path: Optional[str] = typer.Option(None, help="Project path for Claude Code project-specific config")
):
    """Configure MCP servers for specified editor"""
    if editor == "claude-code":
        handler = ClaudeCodeConfigHandler(config_path)
        # Handle global or project-specific based on project_path
    # ... existing code
```

#### Phase 2: ChatGPT Documentation

**1. Create Documentation Generator**
```python
def generate_chatgpt_instructions(servers: list[ServerConfig]) -> str:
    """Generate setup instructions for ChatGPT Developer Mode"""
    # Return formatted markdown with step-by-step instructions
```

**2. Add Documentation Command**
```bash
mcp-manager config chatgpt --docs
# Outputs detailed setup instructions for ChatGPT
```

---

## Testing Strategy

### Claude Code Testing
1. **Backup Verification**: Ensure backup is created before modification
2. **JSON Integrity**: Validate JSON structure after changes
3. **Server Registration**: Verify servers appear in Claude Code
4. **Project Isolation**: Test global vs project-specific configs
5. **Error Handling**: Test with corrupted/missing config files

### ChatGPT Testing
1. **Documentation Quality**: Verify instructions are clear and complete
2. **SDK Integration** (if implemented): Test with OpenAI Agents SDK
3. **User Feedback**: Gather feedback on manual setup process

---

## References

### Claude Code
- Official Docs: https://docs.claude.com/en/docs/claude-code/mcp
- Setup Guide: https://mcpcat.io/guides/adding-an-mcp-server-to-claude-code/
- Configuration Tutorial: https://scottspence.com/posts/configuring-mcp-tools-in-claude-code
- Reddit Discussion: https://www.reddit.com/r/ClaudeAI/comments/1jf4hnt/setting_up_mcp_servers_in_claude_code_a_tech/

### ChatGPT / OpenAI
- Developer Mode: https://platform.openai.com/docs/guides/developer-mode
- MCP Docs: https://platform.openai.com/docs/mcp
- Agents SDK: https://openai.github.io/openai-agents-python/mcp/
- Medium Article: https://medium.com/data-science-in-your-pocket/mcp-servers-using-chatgpt-cd8455e6cbe1
- Community Discussion: https://community.openai.com/t/mcp-server-tools-now-in-chatgpt-developer-mode/1357233

---

## Conclusion

### Immediate Action Items
1. ✅ **Document findings** (This document)
2. 🔜 **Implement Claude Code support** - High priority, straightforward implementation
3. 🔜 **Create ChatGPT setup documentation** - Provide value while waiting for better integration options
4. 📅 **Monitor OpenAI desktop app** - May enable better ChatGPT integration in future

### Success Metrics
- Claude Code users can configure MCP servers via `mcp-manager config claude-code`
- ChatGPT users have clear documentation for manual MCP setup
- All existing functionality (Cline, Claude Desktop) continues to work
- Configuration files are safely backed up before modifications

---

**Last Updated**: October 23, 2025  
**Status**: Research Complete, Ready for Implementation  
**Next Steps**: Create implementation checklist for Claude Code support
