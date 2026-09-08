# MCP Python SDK 2.2.0 Assessment

Date: 2026-09-07

## Evidence boundary

This assessment covers the repository's five server packages and MCP Manager.
It distinguishes source-level development, packaged local deployment, and
network-server behavior. The release and dependency claims below were checked
against the MCP 2.2.0 release notes and the six refreshed `uv.lock` files.

## Dependency result

All server locks now resolve `mcp` and `mcp-types` 2.2.0 while retaining the
bounded runtime policy `mcp>=2.0.0,<3.0.0`. Neither the servers nor the manager
request the optional SDK CLI. The manager deliberately has no MCP SDK
dependency.

Other direct dependency updates selected by the resolver include Pydantic
2.13.5, Typer 0.27.2, `atlassian-python-api` 5.0.4, and isort 9.0.1. The
Loadbearing YouTube graph also advances Anthropic 1.0.0 to 1.4.0 and OpenAI
3.3.1 to 3.8.0 through its pinned `loadbearing-youtube` v0.1.4 dependency.

## MCP 2.2.0 behavior and relevance

The release changes four relevant boundaries:

- HTTP clients follow redirects only within the endpoint origin.
- Legacy stateful Streamable HTTP sessions expire after 30 idle minutes and
  are capped at 10,000 sessions by default.
- OAuth issuer and resource validation is stricter, with new deprecation
  warnings for omitted settings.
- Tool output-schema references are resolved within the output schema.

The current servers do not implement MCP OAuth or MCP HTTP clients. Their
managed deployment is stdio. Their optional Streamable HTTP entry points gain
the bounded-session defaults without repository code changes. Existing output
schemas are generated from typed return values and pass the upgraded protocol
tests. No server needs custom session limits, redirect behavior, OAuth changes,
or output-schema work for this release.

## Per-project assessment

### Jira Helper

The 32 tools and two file resources use explicit `add_tool()` and
`add_resource()` registration. MCP 2.2.0 requires no behavioral migration.
The Atlassian dependency floor remains the pre-existing 5.0.3 repository change
and the lock advances to 5.0.4. The existing factory and entry point remain
unchanged.

### World Context

The seven read-oriented tools are unaffected by the SDK's HTTP client redirect
rule because application HTTP calls use the project's own `httpx` client, not
the MCP transport client. The optional MCP Streamable HTTP server receives the
new bounded legacy-session defaults. Its server construction remains unchanged.

### MCP Server Creator

The three tools and generated template remain factory-based and imperatively
registered. Because the canonical template now contains the development CLI
extra and module-level `mcp` object, newly generated servers inherit the same
factory-based structure. MCP Manager remains the generated server's install and
synchronization path.

### Loadbearing YouTube

The five tools and lifespan-owned executor require no SDK migration. The
Anthropic and OpenAI changes are transitive through the pinned upstream package
and are covered by the locked tests and managed stdio verification. The
server construction remains unchanged.

### Template

The template remains the canonical factory-based design. The SDK CLI was tested
against it and could not discover a server because the CLI requires a
module-level object. That is a CLI compatibility constraint, not evidence that
the template should instantiate servers at import time. No template change was
made for the CLI.

### MCP Manager

MCP Manager remains SDK-independent. Adding `mcp[cli]` to it would couple a
multi-client lifecycle tool to a server SDK and install a second CLI without a
shared implementation boundary.

## MCP CLI versus MCP Manager

| Capability | MCP SDK CLI | MCP Manager |
| --- | --- | --- |
| Run a source server | Yes | No |
| Launch MCP Inspector | Yes, through `mcp dev` and Node.js/npx | No |
| Install a server persistently | Claude Desktop configuration only | Isolated package environment plus registry |
| Preserve per-server configuration | No repository-specific lifecycle | Yes |
| Synchronize multiple clients | No | Yes |
| Validate, list, show, and remove managed servers | No | Yes |
| Transactional forced reinstall | No | Yes |

The overlap is narrow: both can cause a server entry to appear in Claude
Desktop. The SDK CLI may be useful for projects already shaped around a
module-level SDK object, but it does not run this repository's factory-based
servers without restructuring them. MCP Manager owns persistent installation,
configuration, validation, and fan-out. No server or manager code should be
changed merely to satisfy `mcp install`, `mcp run`, or `mcp dev`, and no manager
code should delegate to or wrap `mcp install`.

## Decisions

- Keep `mcp>=2.0.0,<3.0.0` as the deployed runtime requirement.
- Do not add `mcp[cli]` to server or manager dependencies without a development
  need independent of the CLI's preferred module shape.
- Retain `create_server()`, explicit `add_tool()` registration, and construction
  at the actual application boundary rather than import time.
- Keep in-memory protocol tests for fast contract checks, backed by real
  managed-subprocess stdio verification at the deployment boundary.
- Do not add the SDK to MCP Manager and do not duplicate `mcp dev` or `mcp run`.
- Accept MCP 2.2.0's default legacy HTTP session bounds; add configuration only
  if an observed network deployment needs different limits.

## Verification

- All six locked test suites passed: 80 tests total, with the generator E2E
  skipped in the normal matrix and passed separately when enabled.
- Wheels and source distributions built for all four operational servers, the
  template, and MCP Manager 1.8.0. Artifact metadata retains plain
  `mcp>=2.0.0,<3.0.0` and the existing console entry points.
- MCP Manager transactionally reinstalled all four operational servers,
  preserving the three existing `config.yaml` files, and synchronized five
  registered servers to Cline, Claude Desktop, VS Code, Codex, and Antigravity.
- Manager validation passed for each reinstalled server.
- Real managed-subprocess stdio discovery under MCP 2.2.0 returned Jira Helper
  32 tools and two resources, World Context seven tools, MCP Server Creator
  three tools, and Loadbearing YouTube five tools.
- The template test suite emits one upstream Starlette warning about a
  deprecated AnyIO alias. No repository code or MCP 2.2 deprecation warning was
  observed.

## Upstream references

- <https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.2.0>
- <https://py.sdk.modelcontextprotocol.io/get-started/installation/>
- <https://github.com/modelcontextprotocol/python-sdk/blob/v2.2.0/src/mcp/cli/cli.py>
