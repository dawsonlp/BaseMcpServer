# Dependency refresh — 2026-09-25

## Scope and outcome

Refreshed all six lockfiles against package indexes with `uv lock --upgrade`.
Raised runtime/development minimum versions to the current resolved releases
for MCP Manager and all five server packages, including the template.
The MCP range remains `mcp>=2.0.0,<3.0.0`; every server resolves MCP and
mcp-types 2.2.0, the latest stable release checked on 2026-09-25. No prereleases were enabled.

All six package updates are validated. No managed installations, client
configurations, tags, or releases were made during validation.

| Package | Current direct dependencies (runtime; development) |
| --- | --- |
| MCP Manager | Typer 0.27.2, Pydantic 2.13.5, Rich 15.0.0, PyYAML 6.0.3; pytest 9.1.1 |
| Jira Helper | MCP 2.2.0, Pydantic 2.13.5, atlassian-python-api 5.0.5, PyYAML 6.0.3, requests 2.34.2, matplotlib 3.11.2, NetworkX 3.7; pytest 9.1.1, pytest-asyncio 1.4.0, pytest-mock 3.15.1 |
| WorldContext | MCP 2.2.0, Pydantic 2.13.5, HTTPX 0.28.1, PyYAML 6.0.3; pytest 9.1.1, pytest-asyncio 1.4.0, Black 26.5.1, isort 9.0.1, mypy 2.3.1 |
| MCP Server Creator | MCP 2.2.0, pydantic-settings 2.15.0; pytest 9.1.1 |
| Template | MCP 2.2.0, PyYAML 6.0.3; pytest 9.1.1 |
| Loadbearing YouTube | MCP 2.2.0, Pydantic 2.13.5, PyYAML 6.0.3, loadbearing-youtube 0.1.4; pytest 9.1.1 |

The manager's resolved versions were already current. Transitive updates across
the servers include httpx2/httpcore2 2.13.1, Starlette 1.7.0, Uvicorn 0.54.0,
PyJWT 2.15.0, OpenTelemetry API 1.45.0, and IDNA 3.20. The YouTube
lock also updates OpenAI to 3.19.2 and Anthropic to 1.8.0.

Full-graph outdated checks for all six projects report one exception:
Pydantic 2.13.5 requires exactly pydantic-core 2.46.5, although 2.49.0 exists.
Do not override that compatibility constraint. The build backend remains the
unbounded `setuptools` requirement; isolated builds used setuptools 84.0.0.
Upstream Git tags confirm v0.1.4 remains the latest Loadbearing YouTube tag,
pointing to commit `d6b42f7841d0c3fae7789924919fdcdf19971a18`.

## SDK documentation review

Reviewed the current official SDK release notes, tools, lifespan, transport,
and deprecation documentation. No source migration is required by this refresh.

- Factories use public `MCPServer`, `add_tool`, and `add_resource` APIs.
  Typed signatures generate schemas; structured outputs and annotations are
  already configured. Blocking synchronous tools use the SDK's thread execution.
- Local entry points explicitly select stdio and log to stderr. Streamable HTTP
  is the preferred network transport; SSE remains only for legacy compatibility.
  Existing host/origin protections and bounded HTTP session defaults are retained.
- The YouTube executor already has lifespan ownership. Its tool now declares
  `Context[LifespanState]` for typed access to the lifespan-owned executor.
  Protocol tests verify that context injection and the job lifecycle still work.
- Runtime source contains none of the reviewed deprecated logging, ping, roots,
  sampling, or OAuth helper call patterns. In-memory `Client` tests remain useful
  protocol tests; actual stdio subprocess checks supplement them.
- MCP Manager remains SDK-independent. The optional SDK CLI does not justify
  changing the repository's factory architecture.

Sources checked on 2026-09-25:

- https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.2.0
- https://py.sdk.modelcontextprotocol.io/servers/tools/
- https://py.sdk.modelcontextprotocol.io/handlers/lifespan/
- https://py.sdk.modelcontextprotocol.io/run/
- https://py.sdk.modelcontextprotocol.io/deprecated/

## Validation

All six package suites passed: manager 12, Jira 38, creator 8, template 6,
WorldContext 6, YouTube 10 (80 total, one opt-in test skipped). The separate
`RUN_GENERATOR_E2E=1` test passed, including generated-project lock, sync,
warnings-as-errors tests, and build. All six packages built wheel and sdist.

Fresh checkout-environment stdio subprocesses exposed Jira's 32 tools and two
resources, WorldContext's seven tools, Creator's three tools, Template's
one tool, and YouTube's five tools. All tools advertised output schemas;
Template's echo and YouTube's list_analysis_jobs were invoked successfully.
YouTube's injected Context was confirmed absent from the public input schema. These checks do not prove external Jira/news API behavior or
installation in MCP Manager's persistent environments.
