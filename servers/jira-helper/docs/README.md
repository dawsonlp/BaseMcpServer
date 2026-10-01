# Jira Helper MCP Server Documentation

The Jira Helper MCP server provides Jira + Confluence integration over the Model
Context Protocol: issue management, JQL/filter search, transitions, time
tracking, and more. It follows the repository's factory-based MCP SDK v2 pattern:
domain functions live in `src/tools/`, explicit adapters in `mcp_adapters.py`
are mapped in `tool_config.py`, and registered
by `create_server()` through `MCPServer.add_tool()`.

## Documentation

### For users
- [Getting Started](user/getting-started.md) — setup and basic usage
- [Available Tools](user/available-tools.md) — tool reference

### For developers
- [MCP integration development plan](../../../docs/developer/jira-helper-mcp-improvement-plan.md) — implementation scope, decisions, and acceptance evidence
- [Adding Features](developer/adding-features.md) — how to add a tool
- [Cline-safe output](architecture/cline-safe-output.md) — output sanitization for Cline
- [Search system](architecture/search-system.md) — search/JQL design
- [MCP resource system](architecture/mcp-resource-system.md) — serving
  workflow-graph images, atomic publication, and subscription behavior

## Quick start

1. **Install**: `mcp-manager install jira-helper --source servers/jira-helper --force`
2. **Configure**: copy `config.yaml.example` to `config.yaml` and fill in your Atlassian details
   (see [QUICKSTART.md](../../../QUICKSTART.md) for the full walkthrough)
3. **Sync**: `mcp-manager sync`, then restart your editor

## Key features

- JQL and filter-based search with injection prevention
- Issue create/update/transition and workflow operations
- Time tracking (log work, manage estimates)
- Confluence page operations
