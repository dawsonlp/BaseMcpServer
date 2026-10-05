# v1.9.2 — dependency refresh

All six project locks were refreshed with `uv lock --upgrade`, including development
and transitive dependencies. The five server locks resolve MCP and mcp-types 2.3.0;
the stable policy remains `mcp>=2.2.0,<3.0.0`. MCP Manager remains SDK-independent.
Other upgrades include rpds-py 2026.9.1, OpenAI 3.24.0, Black 26.10.0,
mypy 2.4.0, ast-serialize 0.12.1, and platformdirs 4.12.3.

Complete `uv tree --locked --outdated` audits found only pydantic-core 2.46.5
behind latest 2.49.0: Pydantic 2.13.5 requires 2.46.5 exactly. The Git-sourced
Loadbearing YouTube dependency remains on its latest upstream release tag v0.1.4.

## Package versions

| Package | Version |
| --- | --- |
| Jira Helper | 2.3.2 |
| World Context | 1.3.1 |
| MCP Server Creator | 1.5.1 |
| Loadbearing YouTube MCP server | 0.1.1 |
| Template MCP server | 0.1.1 |
| MCP Manager | 1.8.1 |

## MCP 2.3.0 compatibility

The [upstream release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0)
rejects invalid `x-mcp-header` annotations at registration and validates an explicit
null structured result against its output schema. None of our server handlers
uses `x-mcp-header`; ordinary optional tool parameters are unaffected by that
restriction. Existing typed success-result and error-result tests pass. No
server reads the affected legacy `ctx.meta`, `ctx.params`, or experimental
capability fields, and no tools/list-rewriting middleware is present.
No server implementation migration was needed. This is test and source-inspection
evidence, not exhaustive coverage of every upstream payload or client.

## Verification and local deployment

On October 4, 2026, all six locked suites passed: 97 tests, with the opt-in
E2E normally skipped. The generated-project E2E passed separately. All six
wheel/source builds passed; wheel metadata confirmed package versions, MCP
ranges, and console entry points. `git diff --check` passed.

Fresh checkout and managed stdio sessions discovered Jira 32 tools/two resources
in modern and legacy modes, World Context seven tools, Creator three tools,
YouTube five tools, and Template one tool. Jira invalid-input handling, World
Context date/time, and Template echo calls passed over real stdio.

MCP Manager and all five managed servers were reinstalled. Installed dependency
versions matched their project locks. Existing managed config files were preserved
byte for byte. Manager validation passed for every server; sync succeeded for
Cline, Claude Desktop, VS Code, Codex, and Antigravity. Existing client processes
were not forcibly restarted. Verification/build/install logs are under
`/private/tmp/BaseMcpServer-v1.9.2` on the release machine.

The release artifacts comprise six wheels and six source distributions. Publication
is to the repository's GitHub Release, with main and a new annotated v1.9.2 tag;
no PyPI publication is part of this release.
