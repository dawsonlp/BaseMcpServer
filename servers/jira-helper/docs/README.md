# Jira Helper MCP Server Documentation

The Jira Helper MCP server provides Jira + Confluence integration over the Model
Context Protocol: issue management, JQL/filter search, transitions, time
tracking, and more. It follows the flat `mcp-commons` pattern used across this
monorepo (tools declared in `src/tools/`, registered via `tool_config.py`).

## Documentation

### For users
- [Getting Started](user/getting-started.md) — setup and basic usage
- [Available Tools](user/available-tools.md) — tool reference

### For developers
- [Adding Features](developer/adding-features.md) — how to add a tool
- [Cline-safe output](architecture/cline-safe-output.md) — output sanitization for Cline
- [Search system](architecture/search-system.md) — search/JQL design
- [MCP resource system](architecture/mcp-resource-system.md) — proposed design for serving
  workflow-graph images as MCP resources (status: design-only, not yet implemented)

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
