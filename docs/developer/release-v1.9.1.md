# v1.9.1

Jira Helper 2.3.1 uses the SDK worker dispatch for ordinary synchronous adapters,
while workflow generation retains an async boundary for resource notifications.
Client ownership, safe errors, shutdown draining, and public catalogs are preserved.

All five servers and the canonical scaffold now require `mcp>=2.2.0,<3.0.0`.
All six locks were refreshed; MCP resolves to 2.2.0. Pydantic 2.13.5 requires
pydantic-core 2.46.5 exactly, preventing its independent upgrade to 2.49.0.
The Git-sourced YouTube dependency remains at latest tag v0.1.4.

Verification: 97 locked tests passed, generated-project E2E passed separately,
all six wheel/sdist builds passed, and fresh stdio discovery passed. Packaged
Jira modern and legacy sessions preserved the complete tool/resource catalog.
Local deployment is verified separately; a pushed tag is not a GitHub Release.

## v1.9.1 local deployment — October 1

The user authorized commit, tag, push, and local reinstall. Jira was bumped to
2.3.1 and its locked suite (53 tests) and wheel/sdist build passed again.
MCP Manager 1.8.0 was reinstalled through uv tool; installed Python source and
runtime dependency versions matched this checkout and its lock.
All five servers, including Template, were installed through MCP Manager.
Existing configuration files were preserved byte for byte. Fresh managed stdio
sessions discovered Jira 32 tools/two resources (modern and legacy), World Context
7 tools, Creator 3, YouTube 5, and Template 1. Jira reported 2.3.1, retained its
complete tool catalog, and passed non-mutating valid/error calls. Every managed
server's installed dependency versions matched its project lock.
Sync succeeded for Cline, Claude Desktop, VS Code, Codex, and Antigravity; all five
Manager validations passed. Existing client processes were not forcibly restarted.
Local logs are in `/private/tmp/jira-sync-verification/deploy`.
The release is tagged from the follow-up branch; main is not merged and no GitHub
Release publication is included.
