# Agent handover — 2026-10-01

## Intent and authorization

The user wants coherent MCP v2 documentation and server implementations that use
ordinary functions, factory construction, and explicit public SDK registration.
The intended improvement is dependable operation: explicit runtime ownership,
useful safe errors, precise contracts, and verification at the installed boundary.

The user authorized the Jira Helper implementation, branching, pushing, and a
minor release tag. Those actions are complete. They subsequently asked for an
assessment of MCP Manager and the other servers; the recommendations below are
proposals, not authorized implementation. The latest request is this handover.
Do not infer authorization to deploy, merge main, publish a GitHub Release, or
implement the proposed follow-up work from the earlier Jira authorization.

## Checkout and release state

Repository: `/Users/dawsonlp/repos/ai_env/BaseMcpServer`.

- Current branch: `improve/jira-helper-mcp-integration`.
- HEAD: `1383f6880a89127477e1ba76017e1c82690f2049`.
- `2803a96`: Jira integration implementation and MCP v2 documentation.
- `75ef72d`: merged the then-current `origin/main` into this feature branch,
  including the Manager status-icon fix and Jira/World Context lock updates.
- `1383f68`: prepared repository release `v1.9.0`, Jira package `2.3.0`.
- The feature branch and annotated `v1.9.0` tag were pushed and verified remotely
  on September 30. The peeled tag and branch both pointed to HEAD above.
- Main was not merged with the feature branch. No GitHub Release record was
  created, and no managed server installation was performed in this work.

**Important current dirty file:** on October 1, `git status --short` showed an
existing modification to `servers/jira-helper/pyproject.toml`:

```diff
-version = "2.3.0"
+version = "2.2.0"
-    "mcp>=2.0.0,<3.0.0",
+    "mcp>=2.2.0,<3.0.0",
```

Its source and intent are unknown. Preserve it. The committed release, lock,
README, and schema inventory describe Jira 2.3.0; repository instructions retain
the stable policy `mcp>=2.0.0,<3.0.0`. Resolve this discrepancy with the user before
changing version/dependency policy or claiming a fresh locked build is verified.
This handover and its index link are additional uncommitted documentation edits.

## Completed documentation and Jira work

Read upstream [migration](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md)
and [capability](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md)
guides, updated [MCP v2 conventions](mcp-v2-conventions.md), reconciled the SDK
assessment, and updated developer navigation. Documentation distinguishes SDK
capabilities, protocol behavior, and choices actually adopted by this repository.

The [Jira development plan](jira-helper-mcp-improvement-plan.md) records the
implementation and its constraints. The implementation includes:

- `servers/jira-helper/src/mcp_adapters.py`: 32 typed async adapters, explicit
  context/dependency access, worker-thread execution, and safe `ToolError` mapping.
- `runtime.py` and `jira_client.py`: clients owned by one lifespan, lazy creation,
  per-service/instance serialized access, active-work tracking, shutdown drain,
  session cleanup on initialization failure, bounded HTTP timeout, and no automatic
  write retries. Global client caches were removed.
- Plain synchronous domain functions receive a client provider through a
  keyword-only argument. Validation happens before acquiring a client, and
  compound operations retain the selected instance.
- Workflow rendering runs off the event loop, serializes access to Matplotlib,
  closes figures on failure, and preserves atomic artifact writes.
- Expected upstream failures receive safe public messages. Partial issue creation
  preserves successful work and exposes safe link failures rather than prompting
  a misleading retry of the whole operation.
- Stable nested outputs have tighter schemas. Raw full-issue payloads remain open.
- Absent workflow files return `ResourceNotFoundError` with URI data.
- New tests cover lifecycle, isolation, concurrency, cancellation, shutdown,
  schemas, errors, resource subscriptions, modern/legacy protocol behavior, and
  HTTP protection. Jira feature/resource documentation was updated.

All 32 tool names, input schemas/defaults, descriptions, titles, annotations, and
both resource definitions were preserved against the implementation baseline.
Output schema precision changed intentionally. The release schema inventory was
regenerated from the installed 2.3.0 wheel. Comparisons with the older tracked
inventory found 16 output-schema differences; the implementation review counted
14 strengthened nested schemas. These comparisons have different baselines.

## Verification already performed

These results apply to the September 30 release checkout/artifacts, before the
uncommitted pyproject change noted above.

| Check | Result |
| --- | --- |
| Locked suites | Jira 52, Template 6, World Context 6, YouTube 10, Creator 8, Manager 14: 96 passed; one opt-in Creator E2E skipped in its ordinary suite. |
| Generated-project E2E | Passed separately; generated lock, sync, tests, and build succeeded. |
| Builds | Wheels and source distributions built for all six projects. |
| Packaged Jira stdio | Disposable environment with locked runtime dependencies; modern `2026-07-28` and legacy `2025-11-25` discovered 32 tools and two resources; success/error calls passed. Installed server reported 2.3.0. |
| Live Jira | Read-only packaged-server call returned six projects from the configured default instance. No live mutations exercised. |
| Other stdio discovery | Fresh checkout processes: Template 1, World Context 7, Creator 3, YouTube 5 tools. |
| Git | Release push/tag verified remotely; tree was clean when release completed. |

See [release notes](release-v1.9.0.md). Supporting local logs, scripts, wheel
installs, builds, and catalogs were placed in `/tmp/jira-mcp-evidence`; inspect
whether they still exist before relying on them. They are not repository inputs.
Checkout/disposable installation verification is distinct from MCP Manager's
managed environments, which were not updated by this release.

## Recommended next work: MCP Manager

These findings came from a read-only code review, not failure-injection tests.
Keep Manager's install/configuration role SDK-independent; a protocol probe can
be a separate helper. Prioritize:

1. **Safe registry mutations.** `core/state.py` returns an empty mapping on registry
   read/parse failure, directly writes JSON, and has a 30-second cache. A later
   mutation can overwrite unreadable state; independent CLI processes can lose
   updates. Fail mutations on invalid state, atomically replace writes, and lock
   and freshly read the complete read–modify–write operation. Preserve invalid
   entries rather than silently dropping them during another entry's update.
2. **Reproducible installation and provenance.** `cli/commands/install.py` installs
   source with `uv pip install`, independently resolving dependencies rather than
   consuming the tested lock. Design a locked path and record installed package
   version, lock identity, and console entry point. `core/platforms.py` currently
   rereads the mutable source pyproject to choose an installed command, which can
   diverge from installed metadata. Discuss fallback behavior for external projects
   without a lock rather than silently choosing a policy.
3. **Runtime verification.** `core/validation.py` checks configuration/paths and
   treats missing environment Python as a warning. Add an explicit opt-in probe
   of the exact managed command, cwd, and environment: bounded process startup,
   discovery, versions/catalog reporting, clean termination, actionable diagnostics.
   Distinguish configuration validity, protocol operation, and service health.
   Discovery should not automatically call mutating business tools.
4. **Complete reinstall recovery.** Registry publication and filesystem rollback
   are not one complete transaction. Backup deletion occurs inside a block whose
   later failures trigger rollback. Define the commit point, restore registry and
   environment consistently on pre-commit failures, and report post-commit cleanup
   failures separately. Preserve credentials/settings and test interrupted stages.

## Recommended next work: servers

The installed MCP 2.2.0 SDK already runs synchronous handlers through
`anyio.to_thread.run_sync`. Verified in installed `func_metadata.py` and upstream
migration documentation. Do not justify a blanket async conversion by claiming
ordinary synchronous tool functions block the event loop. Adopt adapters where
they make injection, error translation, or runtime control clearer.

| Component | Concrete next changes |
| --- | --- |
| MCP Server Creator | First fix `server.py:list_installed_servers`: it parses obsolete “Local MCP Servers”/“Remote MCP Servers” headings, but Manager uses “MCP Servers” and supports `list --format json`. Consume JSON with a subprocess timeout and a defined result shape. Protect concurrent creation of the same name; avoid deleting existing generated source before replacement succeeds. Preserve partial creation/install/sync outcomes. |
| Loadbearing YouTube | `tool_config.py` owns the executor in lifespan but keeps jobs/events/locks globally. Move them into lifespan-owned state, bound queued work, handle submission failure, and define cancellation/shutdown outcomes. `executor.shutdown(wait=True)` currently runs synchronously inside async lifespan cleanup; offload that wait. Tighten job/provider schemas and map expected failures safely. Explicit adapters can keep MCP context out of domain code. |
| World Context | `tool_config.py` creates HTTP clients per request and has a process-global cache. Own reusable clients/cache per lifespan, prevent duplicate refreshes, expose stale provenance, tighten nested results, and sanitize upstream errors. Preserve useful partial aggregate results. Choose synchronous pooled clients or async I/O based on the actual concurrency need. |
| Template | Keep echo minimal. Add concise optional lifecycle/error/injection examples and generated-project checks. Do not impose Jira's client registry or a generic adapter framework on every generated server. |

YouTube currently uses application job IDs and polling. Keep that mechanism until
there is an agreed replacement: upstream documentation says the experimental
Tasks API was removed and the replacement official extension is not implemented
by the SDK yet. Verify upstream status again before adopting it.

Suggested sequence: Manager registry/install reliability, Creator JSON
integration, YouTube lifecycle, World Context, then template guidance. Agree on
the scope and any significant installation/runtime policy choices with the user
before implementation; the preceding assessment was not an implementation request.

## Working rules and next-agent starting point

Read repository `AGENTS.md` and [MCP v2 conventions](mcp-v2-conventions.md).
Preserve factory construction and public `add_tool`/`add_resource` registration;
avoid registration decorators, import-time server objects, and private SDK APIs.
Use `servers/template` as the canonical scaffold. Apply serialization only where
the underlying dependency requires it. Preserve public compatibility unless an
explicit change is agreed.

Start with `git status`, inspect the pyproject discrepancy, and establish the next
authorized scope. Create a new follow-up branch when implementation is authorized;
do not move or reuse `v1.9.0` for later changes.

Typical checks after substantive implementation:

```sh
uv run --directory <project> --locked --extra dev pytest -q
RUN_GENERATOR_E2E=1 uv run --directory servers/mcpservercreator --locked --extra dev pytest tests/test_generator_e2e.py -q
uv build --project <project>
git diff --check
```

Add behavior-focused tests for corrupt registry preservation, concurrent writes,
rollback stages, bounded subprocesses, lifespan isolation, queue limits, and
modern/legacy protocol behavior as relevant. Verify real stdio discovery and
installed artifacts. If performing dependency maintenance, repository instructions
require all six `uv lock --upgrade` runs, complete `uv tree --locked --outdated`
graphs including development dependencies, and checking the Git-sourced YouTube
dependency's release tag; explain upstream-constrained exceptions.

Managed installation, client synchronization, main-branch merging, tag pushing,
and GitHub Release publication are distinct outcomes. Obtain the relevant scope,
perform and verify each requested action, and report only observed completion.

## October 1 authorized follow-up

The user approved raising the MCP minimum to 2.2.0 and simplifying Jira adapters
to use SDK synchronous dispatch. Jira package version is restored to 2.3.0.
The earlier discrepancy above is historical; it no longer requires clarification.
Most adapters are synchronous; workflow generation remains async to await its
resource notification. Manager and other server runtime proposals remain outside
this follow-up scope. Verification results will be recorded after completion.

### Follow-up verification — October 1

Implemented on `improve/jira-sdk-sync-dispatch`: 31 synchronous Jira adapters
use SDK worker dispatch; workflow generation retains an async notification
boundary. Client ownership and public contracts are preserved. All five server
manifests and current scaffold guidance use `mcp>=2.2.0,<3.0.0`.

- Locked suites: Jira 53, Template 6, World Context 6, YouTube 10, Creator 8,
  Manager 14: 97 passed; the opt-in Creator E2E passed separately.
- Wheels and source distributions built for all six projects.
- Fresh disposable Jira wheel install reported 2.3.0; modern `2026-07-28` and
  legacy `2025-11-25` stdio discovery exposed 32 tools and two resources.
  Full tool/resource inventories exactly matched the tracked release inventory;
  valid JQL and safe invalid-issue calls passed in both modes.
- Fresh stdio discovery passed for Template, World Context, Creator, and YouTube.
- All six `uv lock --upgrade` and `uv tree --locked --outdated` checks completed,
  including development dependencies. Manager's lock was already current.
  MCP remains 2.2.0. The only outdated graph entry was pydantic-core 2.46.5
  versus 2.49.0: installed Pydantic 2.13.5 requires exactly 2.46.5.
- Remote YouTube tag inventory confirmed v0.1.4 is the latest available tag;
  its peeled commit matches the locked dependency d6b42f7841d0c3fae7789924919fdcdf19971a18.
- `git diff --check` passed. Evidence logs and disposable artifacts are in
  `/private/tmp/jira-sync-verification`; these are local, temporary evidence.

These are checkout/disposable-artifact checks. No managed installations, client
synchronization, live Jira mutations, commit/push, merge, tag, or release publication
were performed for this follow-up.

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
