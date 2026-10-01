# Jira Helper MCP Integration Development Plan

Date: 2026-09-30

Status: implemented and verified on branch `improve/jira-helper-mcp-integration`.
The user authorized branching and implementation after reviewing this plan.
The subsequent release request authorizes pushing this branch and tagging the
repository as `v1.9.0`, with Jira Helper package version `2.3.0`. Managed
installation remains outside this release.

## Vision and scope

Make Jira Helper's MCP interface informative on failure, responsive during slow
work, explicit about runtime ownership, and precise about its data contracts.
Preserve ordinary domain functions and factory-based composition through public
`MCPServer.add_tool()` and `add_resource()` APIs.

This work covers Jira Helper's MCP adapters, client ownership, workflow execution,
stable result schemas, protocol tests, and directly affected documentation.
Follow [MCP v2 conventions](mcp-v2-conventions.md) and use the
[template](../../servers/template/) as the factory reference. Do not introduce
registration decorators, import-time servers, private SDK access, a generic
adapter framework, or a replacement server architecture.

Preserve public tool names, arguments/defaults, resource URIs, existing result
fields, and behavior annotations unless a specific compatibility change is agreed.
Keep `mcp>=2.0.0,<3.0.0`; this plan does not require a dependency refresh. It does
not add MCP Tasks, elicitation, OAuth, caching, new business operations, or automatic
retries of writes. Publication and managed installation are separate actions.

## Evidence and starting point

The preceding read-only review established the following on the local checkout:

| Observation | Implication |
| --- | --- |
| Jira Helper's lock resolves MCP 2.2.0; the factory explicitly registers tools/resources and enables structured output. | Retain the current composition approach. |
| Calling `get_issue_details` with `issue_key="bad"` through an in-process MCP client returns only `Error executing tool get_issue_details`. | Expected domain errors lose the explanation needed to correct the call. |
| A 200 ms synchronous workflow stub delayed a concurrent 20 ms timer to approximately 257 ms. | The async handler blocks the event loop. This is a local reproduction, not a production latency measurement. |
| `jira_client.py` has module-global Jira/Confluence caches; the server has no custom lifespan. | Server instances share clients without explicit cleanup or concurrency ownership. |
| Project items advertise arbitrary dictionaries; workflow output advertises an unrestricted object. | Stable, repository-owned shapes are under-specified. |
| Notification tests use a recording context; the missing-resource test expects a broad exception group. | Tests do not establish actual subscription delivery or the exact public resource error. |
| All 38 Jira Helper tests passed. | Existing checks pass despite the reproduced gaps. |

Evidence is from the review immediately preceding this plan, not a new test run
while writing it. Refresh the baseline before implementation. Source entry points:
[factory](../../servers/jira-helper/src/main.py),
[registration](../../servers/jira-helper/src/tool_config.py),
[clients](../../servers/jira-helper/src/jira_client.py),
[workflow](../../servers/jira-helper/src/tools/workflow.py), and
[tests](../../servers/jira-helper/tests/).

## Adopted implementation decisions

The user's instruction to implement the reviewed plan adopts the recommended
starting points below. The implementation uses explicit lazy client suppliers
below the MCP adapter so domain validation occurs before network acquisition.

| Decision | Recommended starting point | Evidence/constraint to resolve |
| --- | --- | --- |
| Client ownership | One small typed state object per server lifespan, containing a lazily populated client registry. | Creating a server should not contact every configured service; closing it must release the clients it owns. |
| Client concurrency | Serialize access per service/instance initially, unless the installed Atlassian client proves safe for shared concurrent use. | Inspect its session and close APIs. A lock around creation alone does not protect concurrent requests; different instances should remain independent. |
| Dependency delivery | Explicit typed MCP adapter functions obtain lifespan state and pass required client/services into ordinary domain functions. | Preserve advertised signatures and avoid a service locator or a proliferation of new layers. Decide the small internal API before changing all tools. |
| Workflow rendering | Run blocking work off-loop and serialize plotting where shared library state requires it. | The scope must cover all concurrent renderers in a process, including separate server instances. A worker thread alone is not a thread-safety solution. |

The current `latest` workflow resources are mutable shared artifacts. Preserve
that contract for this effort: atomic replacement prevents partial files, but does
not guarantee a caller later reads its own generated version. Per-request artifact
identity or multi-user isolation would be a separate requirement and design decision.

## Implementation sequence

Use the IDs below to track completion. Mark a phase complete only after its
acceptance checks pass and evidence is recorded. Keep changes reviewable by phase.

### JH-0 — Baseline and contract inventory

- [x] Record the worktree state, lock/environment versions, and existing modified
  documentation. Preserve unrelated changes.
- [x] Capture all advertised tool names, input/output schemas, annotations, and
  resource definitions. Record legitimate schema differences expected from JH-4.
- [x] Run the Jira tests and reproduce the error and scheduling failures with
  deterministic local fixtures, without using live mutations.

Acceptance: a comparison baseline and failing regression cases exist for the
observable behaviors this plan changes. No claim of installed-server verification
is inferred from these checkout tests.

### JH-1 — Actionable MCP errors

- [x] Inventory expected validation, missing-object, authentication/permission,
  connection, and API failures across Jira and Confluence tools.
- [x] Keep the existing domain exception hierarchy MCP-independent. Add explicit
  boundary adapters that translate expected failures to `ToolError` with safe,
  actionable text. Register these ordinary callables in the factory's tool map.
- [x] Define public messages deliberately. Existing exception text can contain
  raw upstream details, so do not blindly expose `str(error)` for every `JiraError`.
  Preserve diagnostic causes in server logs; keep unexpected defects sanitized.
- [x] Preserve valid partial-success results, such as an issue created with some
  links failing. Do not turn them into a blanket failure that encourages duplicate
  creation. No automatic retries for externally mutating operations.

Acceptance: malformed issue keys, unknown instances, permission failures, and
controlled upstream failures yield `is_error=True` with useful safe messages;
unexpected exceptions do not reveal internals. SDK input validation still works,
success schemas remain intact, and domain functions remain directly testable.
Test representative branches for each error category and ensure all registered
tools receive the intended boundary treatment without `**kwargs` schema erosion.

### JH-2 — Responsive workflow execution

- [x] Extract synchronous Jira lookup, graph preparation/rendering, and atomic
  file replacement into ordinary functions with explicit dependencies.
- [x] Keep a thin async MCP handler that awaits bounded off-loop execution, then
  publishes `notify_resource_updated()` after successful replacement. Retain JSON
  output and the current resource URI contract.
- [x] Apply the agreed rendering concurrency policy. Close figures and remove
  temporary files on failure. Ensure exceptions cross the worker boundary into
  the error contract from JH-1.
- [x] Define cancellation/shutdown behavior explicitly: cancellation cannot kill
  a running synchronous thread or undo an external write. Use supported client
  timeouts, retain ownership of in-flight work, and do not close clients beneath it.

Acceptance: a blocked workflow fixture does not prevent an unrelated MCP call
from completing. Use synchronization events and bounded waits, not a fragile
exact-duration assertion. Existing success/failed-replacement behavior remains;
notifications never precede publication or claim failed publication succeeded.
Concurrent rendering and shutdown tests establish the agreed policy.

### JH-3 — Lifespan-owned clients

Uses the adopted ownership/concurrency decisions above.

- [x] Add a small typed runtime state and lifespan function; supply it from
  `create_server()`. Keep configuration resolution and runtime ownership distinct.
- [x] Move Jira/Confluence caches out of module globals into the owned registry;
  implement lazy creation, synchronization, and cleanup using the actual installed
  client's supported APIs. Clean up failed initialization too.
- [x] Wire `Context[State]` at the MCP boundary and explicit dependencies below it.
  Reuse the adapters from JH-1 and the workflow functions from JH-2.
- [x] Update every tool path, including compound operations, so no legacy global
  cache silently bypasses ownership or creates lock-order/deadlock problems.

Acceptance: two server instances have isolated registries; concurrent first use
does not leak duplicate clients; client access follows the agreed policy; unused
instances are not contacted; shutdown closes owned clients once after owned work
finishes. Fakes can replace dependencies without patching global client caches.

### JH-4 — Precise stable result schemas

Can proceed independently after JH-0; integrate with JH-1/JH-3 before final checks.

- [x] Define nested `TypedDict` records for repository-projected projects,
  configured instances, issue summaries, and other fixed records discovered by
  the inventory. Keep raw Jira/Confluence payloads explicitly open-ended.
- [x] Define workflow result contracts for JSON data, generated artifacts, and
  no-data outcomes, including optional fields. Check how the locked SDK represents
  the selected types before adopting a union or adding a new discriminator.
- [x] Preserve existing payload fields and valid partial-success semantics.
  Treat any proposed output-shape change as a separate compatibility decision.

Acceptance: discovery describes nested stable fields; representative results
validate against their published schemas; raw upstream extras survive where
intended. No new required inputs or accidental exposure of injected dependencies.

### JH-5 — Protocol verification and documentation

- [x] Add real modern `Client.listen(...)` coverage: establish the accepted
  subscription before publication, generate an artifact, receive its update, and
  read the completed resource. Bound waits and assert the relevant honored filter.
- [x] Test representative success and error calls in modern and legacy modes.
  Separate normal public error conversion from diagnostic exception propagation.
- [x] Replace the broad missing-resource assertion with the actual public
  `MCPError` contract. Verify the locked `FileResource` behavior first; distinguish
  an unknown URI from a registered artifact that has not yet been generated. If
  missing files need adaptation, use a small public resource implementation.
- [x] Exercise real subprocess stdio discovery/calls against the built package,
  using local fixtures or configured read-only operations. Verify applicable
  HTTP host/origin checks and lifespan startup/shutdown at the ASGI boundary.
- [x] Update Jira's feature-development guidance and resource documentation to
  match the final code. The existing adding-features page still describes removed
  layers and shows `**kwargs`; the local index labels implemented resources as
  design-only. Preserve relevant output-sanitization guidance during correction.

Acceptance: tests verify delivery and client-visible outcomes rather than only
helper calls. The catalog still exposes the expected 32 tools and two resources
unless an explicit scope change is recorded. Documentation describes final adopted
decisions and limitations, with no claim that optional capabilities were deployed.

## Completion and release boundary

1. Run Jira Helper's locked test suite and relevant concurrency/protocol checks.
   Use `uv run --directory servers/jira-helper --locked --extra dev pytest`.
2. Complete the repository-required package tests, generated-project E2E, builds,
   and real stdio discovery. Keep the generator/template unchanged unless a shared
   defect is established; report any broadened scope before modifying it.
3. Check final schemas against JH-0, review documentation links, and run
   `git diff --check`. Record commands, versions, results, and unresolved issues.
4. Report checkout/package readiness separately from installation. When managed
   installation is requested, use MCP Manager and verify a fresh managed stdio
   process afterward. Do not claim an earlier process loaded the new package.

If dependencies must change, follow the separate repository maintenance policy:
refresh all six locks, inspect complete outdated graphs, explain upstream limits,
and check the Git-sourced YouTube release. Do not silently fold that work into
this integration improvement.

## Completion evidence — 2026-09-30

All phases JH-0 through JH-5 are complete in the checkout. Existing documentation
changes were carried onto the branch without reverting them. No dependency
versions or lockfiles changed; the packaging manifest now includes the new adapter
and runtime modules.

| Verification | Result |
| --- | --- |
| Jira Helper | 52 tests passed; baseline was 38. Tests cover safe errors, partial creation, lazy isolated clients, serialized access, failed initialization cleanup, shutdown/cancellation, responsive workflow calls, rendering cleanup/serialization, modern subscriptions, both protocol modes, raw payloads, nested schemas, and HTTP protection/lifespan. |
| Other locked suites | Template 6, World Context 6, Loadbearing YouTube 10, MCP Server Creator 8, MCP Manager 12 passed. The normal Creator suite skips one opt-in E2E test. |
| Generator E2E | Passed separately with `RUN_GENERATOR_E2E=1`; generated project lock, sync, tests, and build succeeded. |
| Package artifacts | Wheels and source distributions built for all six projects. Jira wheel includes `mcp_adapters.py` and `runtime.py`. |
| Catalog compatibility | Before/after comparison retained all 32 tool names, input schemas, descriptions, titles, annotations, and both resource definitions. Stable nested output schemas were intentionally strengthened. |
| Packaged Jira stdio | Disposable environment installed the wheel with locked runtime dependencies. Fresh modern (`2026-07-28`) and legacy (`2025-11-25`) processes discovered 32 tools/two resources and passed success/error calls. |
| Live read-only boundary | The packaged modern Jira process listed six projects from the configured default instance. No live mutations were exercised. |
| Other real stdio processes | Template 1, World Context 7, Creator 3, and YouTube 5 tools discovered from fresh checkout-environment subprocesses. |
| Hygiene | Relative links and `git diff --check` passed. |

Commands used include the locked pytest command above, `uv build --project <path>`,
and `RUN_GENERATOR_E2E=1 uv run --directory servers/mcpservercreator --locked
--extra dev pytest tests/test_generator_e2e.py -q`. Local logs, catalog snapshots,
artifacts, and subprocess verification scripts are under `/tmp/jira-mcp-evidence`;
that temporary directory is supporting evidence, not a repository dependency.

The isolated build initially could not reach PyPI from the sandbox; rerunning with
package-index/cache access succeeded. Final package testing is separate from MCP
Manager deployment: existing managed servers were not reinstalled or synchronized.
The current latest-artifact sharing and synchronous cancellation limits described
above remain intentional constraints.

## References

- [MCP v2 conventions](mcp-v2-conventions.md)
- [SDK migration guide](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md)
- [SDK v2 capability overview](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md)
- [Jira Helper documentation](../../servers/jira-helper/docs/README.md)
