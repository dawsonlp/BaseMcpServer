# MCP Python SDK v2 Conventions

Reviewed: 2026-09-30. This is the current repository convention for maintained
and generated servers; [the build guide](BUILD_A_NEW_MCP.md) describes the workflow.

## Intent and evidence boundary

Build MCP servers from ordinary, independently testable functions, with explicit
composition, registration, and runtime ownership. Use the SDK's supported
capabilities without coupling business logic to server construction.

Keep the dependency policy `mcp>=2.0.0,<3.0.0`. All five server locks currently
resolve `mcp` and `mcp-types` 2.2.0; MCP Manager remains SDK-independent.
An allowed version range, a lockfile resolution, an upstream `main` document,
and a managed installation are different evidence. This documentation update
changes neither dependencies nor installed servers.

The upstream [migration guide][migration] and [v2 capability tour][whats-new]
were reviewed against `main` revision
`d639cf7f97f77388fa7da60c0f9b04f8837b77fd`. The capability sections below describe
that documented v2 surface, not a promise that every future `main` change exists
in our locks. Factory registration and error handling were also checked against
the local 2.2.0 implementation. Verify a newly adopted feature against the locked
SDK and the actual client before treating it as supported in a deployment.

## Factory construction and explicit registration

Use [servers/template](../../servers/template/) as the canonical scaffold:

1. Implement ordinary typed functions, with domain dependencies explicit.
2. Keep tool names, descriptions, annotations, and callable references in a
   registration map, as in the template's `tool_config.py`.
3. Have `create_server()` construct a fresh `MCPServer` and register the selected
   callables through public `add_tool()` and resources through `add_resource()`.
4. Construct and run the server at the application entry point. Use `create_app()`
   for ASGI hosting; pass transport settings when building the app or running it.

Do not use `@server.tool()`, `@server.resource()`, or registration/validation
wrappers on business functions. Do not introduce import-time server instances,
private manager access, or a generic base-server abstraction to perform registration.
Standard lifecycle helpers such as `@asynccontextmanager` are appropriate;
other decorators need a concrete cross-cutting purpose independent of registration.

This is an architectural choice, not an SDK limitation. The SDK's `tool()`
decorator calls `add_tool()` and returns the original function; it does not
replace that function with a tool object. Our preference is to make registration
and its timing visible in the factory. Explicit registration retains the same
high-level schema generation, argument validation, context injection, and result
conversion. Avoiding decorators does **not** require the low-level `Server`.

A minimal example (the template adds configuration and the registration map):

```python
from typing import TypedDict

from mcp.server import MCPServer
from mcp.types import ToolAnnotations


class EchoResult(TypedDict):
    message: str


def echo(message: str) -> EchoResult:
    return {"message": message}


def create_server() -> MCPServer:
    server = MCPServer(name="example", version="1.0.0")
    server.add_tool(
        echo,
        name="echo",
        title="Echo",
        description="Return the supplied message.",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
        structured_output=True,
    )
    return server


if __name__ == "__main__":
    create_server().run("stdio")
```

In a real package, report its own version through `importlib.metadata.version`,
as the template does. Use keyword arguments for identity and instructions;
v2 inserted positional parameters that can silently change the meaning of v1 calls.
Do not reshape the application to satisfy SDK CLI discovery. MCP Manager owns
managed installation and client synchronization; SDK CLI support is a separate
compatibility question. See the [2.2.0 assessment](mcp-sdk-2.2.0-assessment.md).

## Contracts and errors

- Type every public parameter concretely. Include `None` for optional values,
  collection element types, and actual numeric or literal domain limits.
- Do not expose `**kwargs`. Use `dict[str, Any]` only for genuinely open-ended data.
- Use `TypedDict` or Pydantic models for repository-owned stable results and
  `structured_output=True` at registration. Upstream payloads that may grow can
  use an open dictionary schema. Test the advertised schema and returned data.
- Keep domain validation and domain exceptions in ordinary functions. Returned
  status fields represent valid domain states, not disguised invocation failures.
- When a domain failure needs an actionable client-visible explanation, translate
  it at the MCP boundary into a sanitized `ToolError` from
  `mcp.server.mcpserver.exceptions`, or an explicit `CallToolResult(is_error=True)`.
  Use a small ordinary adapter function if needed, registered by the factory;
  do not add a decorator or framework-wide wrapper.

For high-level `MCPServer` calls, the error distinctions are:

| Failure | Client contract |
| --- | --- |
| SDK argument validation or deliberate `ToolError` | Failed tool result with an explanation the caller can use |
| Ordinary handler exception, including `ValueError` or `RuntimeError` | Failed tool result with sanitized text; diagnostic exception logged server-side |
| Deliberate `MCPError(code, message, data)` | JSON-RPC error; SDK client raises instead of returning an error-flagged tool result |

Do not assume a domain exception's message reaches the model. Never put secrets
or raw upstream response bodies in deliberate public error messages. Tool behavior
annotations are descriptive hints, not authorization controls or retry guarantees.

## Types and SDK integration

Use `from mcp.server import MCPServer`, `from mcp.client import Client`, and
`mcp.types` for protocol models. `mcp.types` remains a supported alias of the
separate `mcp-types` package; do not independently pin that transitive package.
A schema-only project can deliberately depend on `mcp-types` instead.

Use Python snake_case fields (`input_schema`, `structured_content`, `is_error`,
`next_cursor`); wire keys remain camelCase. For manual serialization use
`model_dump(by_alias=True, mode="json")`. Unknown protocol fields are discarded;
put supported custom metadata in `_meta`. Resource URIs are strings, and message
unions no longer have a `.root` wrapper; use the public type adapters for parsing.

Inject request context through an annotated `Context` parameter from
`mcp.server.mcpserver`, never an ambient `get_context()` lookup. Tools needing
lifespan state can use `Context[State]` and
`ctx.request_context.lifespan_context`. Keep context handling at the MCP boundary
and pass only the needed data/services to domain functions. The reviewed guide
notes limitations for parameterized context in prompts/resource templates: use
bare `Context` there and verify the locked release's behavior before adoption.

## Runtime, resources, and transport

Executors, clients, pools, and background work belong to a server lifespan with
deterministic shutdown. Streamable HTTP enters that lifespan once at manager
startup and shares its state across requests/sessions. It is not per-user state.
Synchronous handlers/resolvers run in worker threads; check thread safety and
thread affinity. Async handlers must avoid blocking the event loop.

Expose generated files through public resource registration, replace them
atomically, and return their URIs only after successful production. Publish change
notifications after success. Resource templates now implement RFC 6570 and reject
unsafe extracted paths by default; keep those checks and enforce application
access boundaries as well. Static resources do not acquire request-context
injection simply because a callable accepts `Context`.

Use stdio for local clients and Streamable HTTP for network serving. Legacy SSE
remains a compatibility transport; WebSocket support was removed. Keep logs on
stderr and stdout reserved for protocol traffic even though v2 protects stdio
with private descriptors. The server owns cleanup of children it launches.

Pass host, paths, HTTP options, and `TransportSecuritySettings` to `run()` or
app builders, not the `MCPServer` constructor. App builders do not bind ports;
the outer ASGI server does. A mounted application's host lifespan must explicitly
run the MCP session manager. Streamable HTTP defaults to loopback here; any
non-loopback binding requires explicit, non-empty allowed-host and allowed-origin
lists. Retain the SDK's request-size and session bounds unless a measured need
justifies a change. Do not duplicate SDK transport protections in middleware.

The SDK HTTP boundary now uses `httpx2`: supplied clients, auth objects, mocks,
and caught transport exceptions must use matching types. Application-owned
`httpx` usage can remain with a direct dependency. `httpx2` uses system trust;
configure a CA bundle or SSL context where necessary. The SDK transport restricts
redirects to the endpoint origin. Do not infer network security from stdio tests.

## SDK capabilities and their adoption boundary

These capabilities remain compatible with factory construction; availability
alone does not justify adding them to a server.

| Capability | What it enables and how we use it |
| --- | --- |
| High-level `Client` | Owns connection setup for URL, stdio subprocess, transport context manager, or in-process server. Prefer it for client code and contract tests. |
| `Resolve(fn)` dependencies | Injects values omitted from model-facing inputs. A resolver returning `Elicit(...)` can request user input across both protocol eras. Keep resolvers explicit ordinary functions at the MCP boundary. |
| Typed/multimodal results | Structured results, explicit content blocks, images, audio, and resource links remain available without tool decorators. Choose the actual domain contract. |
| Prompts and resources | Reusable prompts, static resources, templates, and completions remain SDK capabilities. Register selected capabilities explicitly through public APIs; discuss gaps before reaching into private SDK state. |
| Low-level `Server` | Constructor `on_*` handlers accept context/typed params and return full protocol results; public request-handler registration supports custom methods. It no longer validates tool arguments against advertised JSON Schema or supplies high-level wrapping. Use only for a concrete protocol-level requirement. |
| Middleware and tracing | OpenTelemetry propagates trace metadata and records spans when tracing is configured. Custom middleware is provisional; avoid depending on it for core architecture or duplicating SDK behavior. |
| OAuth | Stronger issuer/resource validation, issuer-bound credentials, authorization-code callback objects, and enterprise identity assertions. Adoption requires an actual network/authentication design; transport allowlists are not authentication. |

For low-level handlers, distinguish execution-error results from protocol errors
explicitly. The two reviewed upstream pages disagree on the exact fallback code
and message for unexpected low-level exceptions; do not depend on that fallback.
Verify against the chosen release when implementing a low-level server.

## Protocol revision: 2026-07-28 versus legacy connections

SDK major version and MCP protocol revision are separate. The v2 server supports
modern and legacy peers from the same application. The documented `Client` default
is `mode="auto"`: discover the modern surface, then fall back to legacy
initialization when unsupported. `mode="legacy"` explicitly exercises the old
handshake. Inspect `client.protocol_version` rather than inferring it from transport
or package version; modern negotiation also applies to stdio.

| Protocol change | Practical consequence |
| --- | --- |
| Per-request version/capability metadata and `server/discover` | Modern requests need no initialization handshake or HTTP session ID. Identity is optional metadata, so generic clients must allow `server_info is None`. |
| No server-initiated requests | Modern input gathering returns `InputRequiredResult`; the client answers and retries. `Resolve`/`Elicit` bridges this with legacy elicitation. Direct `ctx.elicit()` fails on the modern path even when a callback exists. |
| Unified `subscriptions/listen` | Clients select notification kinds/URIs through `client.listen(...)`. Publish using context `notify_*` helpers; old session push helpers do not deliver modern change events. |
| Routing headers | `Mcp-Method`, `Mcp-Name`, and schema-declared `Mcp-Param-*` headers enable gateway routing. Header/body inconsistencies are rejected; clients must know the tool schema. |
| Cache hints | List/read results can declare lifetime and scope. The SDK client honors those hints; choose scope with caller-specific data in mind. |
| Extension negotiation | Optional capability sets use reverse-DNS identifiers. MCP Apps is a supported example; extension support must be checked on both peers. |

Modern stateless transport makes distribution across workers easier, but does not
make application state distributed. Multi-round-trip retries need shared
`RequestStateSecurity` keys across replicas; cross-replica notifications need a
shared `SubscriptionBus`. Legacy stateful HTTP clients retain session-routing
requirements. `stateless_http=True` governs the legacy path, not modern behavior.

A multi-round-trip request can re-enter execution. Obtain required input before
mutating state and design retries around the operation's actual consequences.
Resolver requests require declared client capabilities; do not assume every host
supports elicitation merely because the server does.

Roots, sampling, and MCP protocol logging are deprecated. Their legacy availability
is distinct from modern removal of the request back-channel. Prefer standard
Python logging and `ctx.report_progress()` for client-visible progress (absolute
values, not increments). Modern progress is server-to-client only; `ping` and
`logging/setLevel` are absent from the modern protocol. Keep deprecation warnings
visible and test any deliberate legacy compatibility path.

Experimental SDK Tasks runtime APIs were removed. Tasks moved to an official
extension that the reviewed SDK documentation says is not yet implemented.
Loadbearing YouTube's existing application job/polling mechanism remains
intentional; it is not MCP Tasks. Prompts, elicitation, Apps, caching, subscriptions,
and new authentication flows require a concrete use case before adoption.

## Verification and maintenance

- Test ordinary functions directly, then verify factory registrations, schemas,
  annotations, structured results, resources, and error behavior through `Client`.
  Use `raise_exceptions=True` to expose unexpected failures and separate tests with
  normal conversion enabled to assert public `is_error` behavior.
- Exercise modern and legacy modes where compatibility is claimed. In-process
  modern calls use direct dispatch; passing them does not prove JSON wire behavior.
  Verify real stdio discovery and calls, plus HTTP/security behavior when relevant.
- Timeouts are float seconds. Client timeouts raise `MCPError` with
  `REQUEST_TIMEOUT` (`-32001`); cancellation now reaches the handler. Neither
  cancellation nor an idempotency hint proves an external mutation was undone.
- For dependency refreshes, upgrade all six locks, inspect complete outdated
  graphs and upstream constraints (including the Git-sourced YouTube release),
  run package tests and generator E2E, and build artifacts. Verify managed
  installations separately from the checkout. See the
  [development checklist](development-checklist.md).

## Sources

- [Migration guide][migration]: API changes and migration details.
- [What's new in v2][whats-new]: SDK and protocol capabilities.
- [Reviewed migration snapshot](https://github.com/modelcontextprotocol/python-sdk/blob/d639cf7f97f77388fa7da60c0f9b04f8837b77fd/docs/migration.md)
  and [capability snapshot](https://github.com/modelcontextprotocol/python-sdk/blob/d639cf7f97f77388fa7da60c0f9b04f8837b77fd/docs/whats-new.md).
- [SDK server implementation](https://github.com/modelcontextprotocol/python-sdk/blob/v2.2.0/src/mcp/server/mcpserver/server.py): explicit registration and high-level dispatch.
- [SDK tool implementation](https://github.com/modelcontextprotocol/python-sdk/blob/v2.2.0/src/mcp/server/mcpserver/tools/base.py): validation and error handling.

[migration]: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md
[whats-new]: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md

## Tool behavior matrix

`RO` means the tool does not mutate user or external state. `Destructive` means
the mutation can replace or remove existing state. `Idempotent` is a behavioral
hint, not a retry guarantee. `Open` means the tool interacts with state outside
the server process. These values are the source for registered
`ToolAnnotations`.

| Server | Tool | RO | Destructive | Idempotent | Open |
| --- | --- | ---: | ---: | ---: | ---: |
| Jira | `list_jira_projects` | yes | no | yes | yes |
| Jira | `get_issue_details` | yes | no | yes | yes |
| Jira | `get_full_issue_details` | yes | no | yes | yes |
| Jira | `create_jira_ticket` | no | no | no | yes |
| Jira | `add_comment_to_jira_ticket` | no | no | no | yes |
| Jira | `transition_jira_issue` | no | yes | no | yes |
| Jira | `get_issue_transitions` | yes | no | yes | yes |
| Jira | `change_issue_assignee` | no | yes | no | yes |
| Jira | `list_project_tickets` | yes | no | yes | yes |
| Jira | `get_custom_field_mappings` | yes | no | yes | yes |
| Jira | `generate_project_workflow_graph` | no | no | yes | yes |
| Jira | `list_jira_instances` | yes | no | yes | no |
| Jira | `update_jira_issue` | no | yes | no | yes |
| Jira | `search_jira_issues` | yes | no | yes | yes |
| Jira | `validate_jql_query` | yes | no | yes | no |
| Jira | `create_issue_link` | no | no | no | yes |
| Jira | `create_epic_story_link` | no | no | no | yes |
| Jira | `get_issue_links` | yes | no | yes | yes |
| Jira | `create_issue_with_links` | no | no | no | yes |
| Jira | `log_work` | no | no | no | yes |
| Jira | `get_work_logs` | yes | no | yes | yes |
| Jira | `get_time_tracking_info` | yes | no | yes | yes |
| Jira | `update_time_estimates` | no | yes | no | yes |
| Jira | `upload_file_to_jira` | no | no | no | yes |
| Jira | `list_issue_attachments` | yes | no | yes | yes |
| Jira | `delete_issue_attachment` | no | yes | no | yes |
| Jira | `list_confluence_spaces` | yes | no | yes | yes |
| Jira | `list_confluence_pages` | yes | no | yes | yes |
| Jira | `get_confluence_page` | yes | no | yes | yes |
| Jira | `search_confluence_pages` | yes | no | yes | yes |
| Jira | `create_confluence_page` | no | no | no | yes |
| Jira | `update_confluence_page` | no | yes | no | yes |
| World Context | `get_current_datetime` | yes | no | yes | no |
| World Context | `get_stock_market_overview` | yes | no | yes | yes |
| World Context | `get_stock_quote` | yes | no | yes | yes |
| World Context | `get_news_headlines` | yes | no | yes | yes |
| World Context | `get_context_summary` | yes | no | yes | yes |
| World Context | `get_latest_tool_versions` | yes | no | yes | yes |
| World Context | `get_python_package_version` | yes | no | yes | yes |
| MCP Server Creator | `help` | yes | no | yes | no |
| MCP Server Creator | `create_mcp_server` | no | yes | no | yes |
| MCP Server Creator | `list_installed_servers` | yes | no | yes | no |
| Loadbearing YouTube | `analyze_video` | no | no | no | yes |
| Loadbearing YouTube | `get_analysis_result` | yes | no | yes | no |
| Loadbearing YouTube | `list_analysis_jobs` | yes | no | yes | no |
| Loadbearing YouTube | `get_video_transcript` | yes | no | yes | yes |
| Loadbearing YouTube | `list_analysis_providers` | yes | no | yes | no |
| Template | `echo` | yes | no | yes | no |
