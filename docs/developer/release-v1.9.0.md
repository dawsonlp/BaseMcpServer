# v1.9.0

Repository minor release; Jira Helper advances from 2.2.0 to 2.3.0.

Jira Helper keeps its 32 tool inputs and two resource definitions while adding
typed asynchronous MCP adapters, lifespan-owned clients, serialized client access,
and safe public errors. Blocking API and workflow rendering operations run off the
event loop. Nested output schemas are more precise, and missing workflow resources
return the protocol's resource-not-found error. Partial issue-creation results
retain successful work and report safe link errors.

Factory construction and explicit public registration remain the architecture.
Updated [MCP v2 conventions](mcp-v2-conventions.md) explain SDK and protocol
capabilities separately from project adoption choices. The
[implementation plan](jira-helper-mcp-improvement-plan.md) records the design,
compatibility constraints, and verification. The Jira schema inventory was
regenerated from the packaged 2.3.0 server.

This release also includes the latest main-branch MCP Manager status-icon fix and
Jira Helper/World Context dependency locks. The MCP dependency policy remains
`mcp>=2.0.0,<3.0.0`.

## Verification

- All six locked package suites: 96 passed, one opt-in test skipped.
- Generated-project E2E: passed separately, including lock, sync, tests, and build.
- All six projects: wheels and source distributions built.
- Packaged Jira Helper: fresh modern (`2026-07-28`) and legacy (`2025-11-25`)
  stdio sessions discovered 32 tools and two resources; success/error calls passed.
  The installed wheel reports server version 2.3.0.
- Live read-only Jira call: six projects returned from the configured default instance.
- Fresh checkout stdio discovery: Template, World Context, MCP Server Creator,
  and Loadbearing YouTube passed.

These checks verify the checkout and disposable package installation. They do not
represent deployment into MCP Manager's managed environments. Live Jira mutations
were not exercised.
