# Repository instructions

## Dependency maintenance

Keep the stable MCP v2 policy `mcp>=2.0.0,<3.0.0`. Refresh all six project locks
with `uv lock --upgrade`, check complete graphs with `uv tree --locked --outdated`,
and explain any upstream-constrained exceptions. Include development dependencies
and check the release tag of the Git-sourced Loadbearing YouTube dependency.

Preserve factory construction and explicit public `add_tool`/`add_resource`
registration. Use `servers/template` as the canonical scaffold. Validate package
tests, generated-project E2E, builds, and real stdio discovery. Distinguish checkout
verification from installation into MCP Manager's managed environments.
