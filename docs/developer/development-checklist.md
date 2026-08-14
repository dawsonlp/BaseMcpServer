# MCP Python SDK v2 Upgrade Development Checklist

## Purpose

Track the approved MCP Python SDK v2 upgrade from the current repository state
through dependency refresh, v2 adoption, verification, and local deployment.
This document is the durable source of truth for what is complete, what remains,
and what evidence supports each completion claim.

## Scope

This checklist covers:

- all five MCP server projects under `servers/`;
- `utils/mcp_manager`;
- dependency manifests and lockfiles;
- tool schemas, structured results, errors, and metadata;
- lifecycle, resources, and Streamable HTTP security;
- the server template, server generator, developer guidance, and relevant ADRs;
- automated tests, package builds, and managed local installation/discovery.

It does not authorize a commit, push, release, PyPI publication, or deployment
outside the existing local managed environment.

## Status Model

- `[x]` Complete: acceptance condition met and evidence recorded.
- `[-]` In progress: implementation has started, but the acceptance condition is
  not yet met.
- `[ ]` Not started: no accepted implementation evidence yet.
- `[!]` Blocked: cannot proceed without a decision or external change; record the
  blocker next to the item.

Maintenance rules:

1. Keep task IDs stable so progress can be compared over time.
2. Mark an item complete only after its stated verification passes.
3. Add dated evidence to the evidence log whenever a status changes.
4. Do not treat an isolated audit, generated schema inspection, or registry entry
   as proof that the checked-in code or managed process works.
5. Re-run a phase gate after later changes that could invalidate it.

## Current Status

Last updated: 2026-08-14

| Phase | Status | Current reality |
| --- | --- | --- |
| 0. Baseline and control | Complete | Scope, approval, repository inventory, and pre-existing worktree changes are recorded. |
| 1. Dependency refresh | Complete | All six locks were fully upgraded, synchronized, audited for outdated/prerelease packages, and passed 55 tests. |
| 2. MCP contracts | Complete | All 48 schemas are captured; Jira `kwargs` is absent, 44 stable outputs are typed, and four deliberately dynamic outputs remain open. |
| 3. Registration and metadata | Complete | All 48 tools remain imperative and expose version, title, description, and classified behavior hints. |
| 4. Lifecycle, resources, and HTTP | Complete | Lifespan ownership, two Jira resources, notifications, and fail-closed HTTP policy pass tests. |
| 5. Scaffolding and documentation | Complete | Template, generator, ADR, conventions, and active guidance reflect the accepted v2 pattern. |
| 6. Repository verification | Complete | Six locked suites, five builds, metadata inspection, schema capture, and hygiene checks passed. |
| 7. Managed local deployment | Complete | Four operational servers were transactionally installed, synchronized, validated, and exercised over real stdio. |
| 8. Closeout | Complete | Final evidence and the separate publication authorization boundary are recorded. |

## Inputs Consulted

### Governing Inputs

- The dependency-upgrade and MCP v2 adoption plan approved by the user on
  2026-08-14.
- The user's standing decision to retain imperative `MCPServer.add_tool()`
  registration and use decorators only for genuine aspect-oriented,
  cross-cutting behavior.

No separate `technical-design.md` exists for this effort. The explicitly
approved plan is therefore the governing design input for this checklist.

### Supporting Context

- Current `pyproject.toml` and `uv.lock` files for all five servers and MCP
  Manager.
- Current server factories, tool configuration, generator, tests, and developer
  documentation.
- The earlier isolated upgrade audit. Its results are planning evidence, not a
  substitute for verification against the final working tree.

## Phase 0: Baseline and Change Control

- [x] **V2-000 — Record approval and implementation boundary.**
  - Acceptance: the approved scope and prohibited release actions are explicit
    in this document.
- [x] **V2-001 — Inventory the independently locked Python projects.**
  - Acceptance: Jira Helper, Loadbearing YouTube, MCP Server Creator, Template,
    World Context, and MCP Manager are included.
- [x] **V2-002 — Record and preserve the pre-existing dirty worktree.**
  - Acceptance: the 13 pre-existing modified files are treated as user-owned
    work and are not reverted or silently replaced.
- [x] **V2-003 — Establish the initial dependency state.**
  - Acceptance: all five server manifests use `mcp>=2.0.0,<3.0.0`, their locks
    resolve `mcp` and `mcp-types` 2.0.0, and the five obsolete explicit
    prerelease overrides are absent.
- [x] **V2-004 — Record known unresolved resolution defects.**
  - Acceptance: the initial baseline recorded inherited Pydantic alpha, Wrapt
    RC, HTTPX dev, and isort beta resolutions. They were remediated before
    checklist execution and released in v1.5.4.

### Phase 0 Gate

- [x] Scope is approved, the starting state is evidenced, and implementation can
  proceed without losing or overstating pre-existing work.

## Phase 1: Refresh All Packages to Current Stable Releases

- [x] **V2-100 — Revalidate upstream release state at execution time.**
  - Check every direct dependency against its authoritative package index or
    upstream repository.
  - Confirm MCP 2.x is still the intended stable major line.
  - Confirm whether `loadbearing-youtube` v0.1.4 remains the current intended
    upstream tag before changing its Git reference.
  - Evidence: dated version inventory with source links or resolver output.
- [x] **V2-101 — Capture a before/after dependency inventory.**
  - Include every direct dependency and each resolved version in all six locks.
  - Distinguish direct requirements from transitive resolutions.
- [x] **V2-102 — Replace the MCP v2 release-candidate pin.**
  - Acceptance: all five server manifests use `mcp>=2.0.0,<3.0.0` and no server
    forces prerelease resolution.
- [x] **V2-103 — Review lower bounds as compatibility claims.**
  - Retain a lower bound when tests demonstrate compatibility with it.
  - Raise a lower bound only when the implementation actually requires a newer
    API; record the reason.
- [x] **V2-104 — Upgrade all six lockfiles.**
  - Run a full upgrade for each server and MCP Manager from its own project
    directory.
  - Do not hand-edit resolved versions.
  - Keep each lockfile deterministic and synchronized with its manifest.
- [x] **V2-105 — Eliminate unintended prerelease resolutions.**
  - Acceptance: no alpha, beta, RC, or dev dependency remains unless an explicit,
    documented requirement makes it unavoidable and the user approves it.
- [x] **V2-106 — Review Git and non-index sources.**
  - Confirm immutable tags or revisions and expected package metadata.
  - Do not advance `loadbearing-youtube` merely because a branch has newer
    commits.
- [x] **V2-107 — Synchronize each environment from its lock.**
  - Acceptance: all six projects install successfully in locked mode without
    mutating the lock.
- [x] **V2-108 — Review the dependency diff for scope and regressions.**
  - Explain major-version changes, removals, new packages, and any justified
    non-current pin.

### Phase 1 Gate

- [x] All six locks are current, stable, reproducible, and supported by a dated
  before/after inventory; any exception is explicit and approved.

## Phase 2: Make MCP v2 Contracts Truthful

- [x] **V2-200 — Inventory the complete exposed tool schemas.**
  - Capture the schema for every registered tool, not only tool names and counts.
  - Use this inventory to identify false required fields, untyped collections,
    missing nullability, and unconstrained values.
- [x] **V2-201 — Remove the unintended Jira `kwargs` schema field.**
  - Acceptance: none of the 32 Jira tools advertises a required
    `kwargs: string` parameter.
  - Preserve genuinely arbitrary Jira fields through an explicit typed field
    map rather than an implicit `**kwargs` escape hatch.
- [x] **V2-202 — Correct input annotations and constraints.**
  - Express optional values as optional.
  - Use concrete item types for lists and mappings.
  - Add numeric bounds, literals, or enums where the domain already constrains
    accepted values.
  - Do not invent constraints that the upstream service does not enforce.
- [x] **V2-203 — Add full-schema regression tests.**
  - Assert required fields, nullability, item types, additional-properties
    behavior, enums, and numeric limits for representative and risk-bearing
    tools.
  - Add a global assertion that no accidental `kwargs` field is exposed.
- [x] **V2-204 — Introduce stable structured output contracts.**
  - Use `TypedDict` or Pydantic models where this repository owns a stable result
    shape.
  - Keep genuinely open-ended upstream payloads honest rather than pretending
    they are closed schemas.
- [x] **V2-205 — Normalize tool error behavior.**
  - Raise ordinary, model-actionable exceptions for tool execution failures.
  - Reserve protocol-level errors for MCP protocol failures.
  - Preserve `status` or `error` fields when they are valid domain state rather
    than failed tool execution.
- [x] **V2-206 — Exercise contracts through an in-memory MCP client.**
  - Use `raise_exceptions=True`.
  - Verify success results, input validation, `is_error`, and
    `structured_content` behavior.

### Phase 2 Gate

- [x] Every exposed input and stable output contract is truthful, accidental
  schema artifacts are absent, and client-level success/error behavior is tested.

## Phase 3: Complete Imperative Registration and v2 Metadata

- [x] **V2-300 — Preserve decorator-free MCP registration.**
  - Keep `MCPServer.add_tool()` as the registration mechanism.
  - Do not introduce `@mcp.tool`, `@mcp.resource`, or `@mcp.prompt`.
  - A decorator may be proposed separately only when it implements genuine
    cross-cutting behavior such as tracing, authorization, or retry policy.
- [x] **V2-301 — Create a tool-behavior classification matrix.**
  - Cover all 48 current tools: Jira 32, World Context 7, MCP Server Creator 3,
    Loadbearing YouTube 5, and Template 1.
  - Classify read-only, additive, destructive, idempotent, and open-world
    behavior from actual effects, not names.
- [x] **V2-302 — Add complete tool specifications.**
  - Supply the registered function, stable name, title, concise description,
    and accurate MCP `ToolAnnotations` for every tool.
  - Treat annotations as behavioral hints, not enforcement.
- [x] **V2-303 — Set package versions on server instances.**
  - Acceptance: each `MCPServer(...)` reports the corresponding package version
    without duplicating a manually drifting value.
- [x] **V2-304 — Remove the deprecated Pydantic v1 validator in MCP Manager.**
  - Replace `@validator('name')` with functional or type-based Pydantic v2
    validation.
  - Do not add a replacement decorator solely to modernize syntax.
- [x] **V2-305 — Test registration metadata and validation.**
  - Assert package version, titles, descriptions, annotations, and manager model
    validation through public behavior.

### Phase 3 Gate

- [x] All 48 tools are imperatively registered with accurate v2 metadata, server
  versions are truthful, and no non-aspect decorator was introduced.

## Phase 4: Lifecycle, Resources, and Streamable HTTP

### Managed Lifecycle

- [x] **V2-400 — Move the Loadbearing thread pool into managed lifespan.**
  - Remove import-time or process-global executor ownership.
  - Create and expose the executor through server lifespan state.
  - Guarantee deterministic shutdown on normal exit and startup failure.
- [x] **V2-401 — Test lifecycle ownership.**
  - Verify one executor per server lifespan, reuse during that lifespan, and
    shutdown without leaked worker threads.

### Jira Workflow Resource

- [x] **V2-410 — Expose the Jira workflow image as an imperative resource.**
  - Register an MCP `FileResource` through `add_resource()`.
  - Replace the oversized inline base64 tool result with a resource URI or other
    bounded reference.
  - Preserve tool compatibility where practical and document any changed result
    contract.
- [x] **V2-411 — Notify resource subscribers after regeneration.**
  - Emit the appropriate resource update only after a successful artifact
    replacement.
- [x] **V2-412 — Test resource discovery, reading, and update behavior.**
  - Include missing-file, regeneration-failure, content type, and subscriber
    notification cases.

### Streamable HTTP Security

- [x] **V2-420 — Keep network defaults on loopback.**
  - A default configuration must not expose the server on a non-loopback
    interface.
- [x] **V2-421 — Require explicit host and origin policy for non-loopback use.**
  - Configure MCP v2 transport security settings with explicit allowed hosts and
    origins.
  - Reject ambiguous or empty production exposure settings.
- [x] **V2-422 — Add fail-closed transport tests.**
  - Cover accepted loopback requests, rejected host headers, rejected origins,
    and explicitly permitted non-loopback configurations.
- [x] **V2-423 — Keep transport behavior inside supported SDK facilities.**
  - Do not add custom middleware for behavior already supplied by MCP v2.
  - Treat additional middleware as a separate decision; built-in OpenTelemetry
    support is sufficient for this effort unless evidence establishes a gap.

### Explicit Retentions

- [x] **V2-430 — Confirm existing job and polling behavior still passes.**
  - Retain the current mechanism because the MCP tasks extension is not part of
    the approved v2 scope.
- [x] **V2-431 — Confirm no speculative protocol features were added.**
  - Do not add prompts, elicitation, or sampling without a concrete use case and
    separate approval.

### Phase 4 Gate

- [x] Lifespan-owned resources shut down deterministically, Jira resource
  behavior works through MCP, and HTTP exposure fails closed.

## Phase 5: Update Scaffolding, Documentation, and Architecture Record

- [x] **V2-500 — Update generated dependency constraints.**
  - Current local generator output uses `mcp>=2.0.0,<3.0.0` and omits the
    prerelease override; its regression test reflects that contract.
- [x] **V2-501 — Update the basic dependency guide.**
  - Current local developer guidance describes the stable v2 range and no longer
    instructs users to force prereleases.
- [x] **V2-502 — Bring the template up to the accepted v2 conventions.**
  - Include server version, typed schemas/results, metadata, imperative
    registration, lifecycle guidance, and safe HTTP defaults where applicable.
- [x] **V2-503 — Bring MCP Server Creator output up to the same conventions.**
  - Generated projects must not reproduce a schema, lifecycle, metadata,
    decorator, or security defect fixed elsewhere in this effort.
- [x] **V2-504 — Add generator end-to-end verification.**
  - Generate a fresh project in a temporary directory.
  - Lock, test, build, and inspect it without editing the generated output.
- [x] **V2-505 — Supersede the historical decorator/FastMCP guidance.**
  - Preserve historical ADR content but mark obsolete decisions as superseded.
  - Add or update the governing ADR for imperative registration and the narrow
    aspect-oriented exception.
- [x] **V2-506 — Remove stale MCP Commons and decorator examples from active docs.**
  - Search the repository after edits and classify any retained occurrence as
    historical, test-fixture, or intentional negative example.
- [x] **V2-507 — Document the v2 contract and operational conventions.**
  - Cover dependency bounds, schema truthfulness, structured results, error
    behavior, annotations, resources, lifespan, HTTP security, and verification.

### Phase 5 Gate

- [x] A newly generated server follows the same accepted v2 practices as the
  hand-maintained servers, and active documentation no longer teaches superseded
  patterns.

## Phase 6: Verify the Repository and Built Artifacts

- [x] **V2-600 — Run all six locked test suites.**
  - Run from each project environment with warnings treated as errors.
  - Record command, commit/worktree identity, pass/fail result, test count, and
    duration.
  - The earlier isolated 55-test pass is historical evidence only.
- [x] **V2-601 — Run targeted schema and in-memory protocol tests.**
  - Confirm these tests actually exercise list/discovery and tool calls through
    MCP rather than only calling Python functions directly.
- [x] **V2-602 — Build all five server distributions.**
  - Build wheel and source distribution for Jira Helper, World Context, MCP
    Server Creator, Loadbearing YouTube, and Template.
- [x] **V2-603 — Inspect distribution metadata.**
  - Verify `Requires-Python`, `Requires-Dist`, package version, console entry
    points, included modules, and absence of unintended files.
- [x] **V2-604 — Verify clean dependency synchronization.**
  - Recreate or cleanly synchronize from each lock and rerun the minimum smoke
    suite needed to catch undeclared dependencies.
- [x] **V2-605 — Run repository hygiene checks.**
  - Run `git diff --check`.
  - Inspect status for generated artifacts, secrets, local configuration, and
    unrelated modifications.
  - Preserve pre-existing user changes and report overlap explicitly.
- [x] **V2-606 — Produce the verification matrix.**
  - One row per project with lock, sync, test, warning, build, and metadata
    results plus evidence paths.

### Phase 6 Gate

- [x] All six projects pass locked verification, all five server packages build
  correctly, and the final diff contains only intentional changes.

## Phase 7: Transactional Managed Local Deployment

- [x] **V2-700 — Capture the managed-environment baseline.**
  - Record installed versions, executable paths, registry state, client
    configuration, and a recoverable copy of configuration needed for rollback.
- [x] **V2-701 — Define and test the rollback procedure.**
  - Identify the exact prior artifacts or installations before replacing them.
  - Do not begin deployment if rollback inputs are incomplete.
- [x] **V2-702 — Install the four operational server artifacts transactionally.**
  - Jira Helper, World Context, MCP Server Creator, and Loadbearing YouTube are
    in scope.
  - The Template package is build-tested but not installed as an operational
    server.
  - Preserve server-specific secrets and configuration.
- [x] **V2-703 — Synchronize supported MCP clients.**
  - Apply the managed configuration through MCP Manager and verify the written
    client configurations rather than relying only on command success.
- [x] **V2-704 — Validate registry and process identity.**
  - Confirm the registry points to the newly installed executables and that
    launched processes use those paths and expected versions.
- [x] **V2-705 — Perform real stdio discovery.**
  - Expected tool counts: Jira 32, World Context 7, MCP Server Creator 3, and
    Loadbearing YouTube 5.
  - Also verify Jira resource discovery if `V2-410` is implemented.
  - A deliberate approved tool-count change must update this checklist before
    the gate is accepted.
- [x] **V2-706 — Run bounded operational smoke tests.**
  - Prefer read-only calls and controlled local inputs.
  - Verify structured content and error behavior through the managed process.
- [x] **V2-707 — Roll back on any failed acceptance condition.**
  - No deployment acceptance condition failed, so rollback was not triggered;
    the verified restore set remains at
    `/private/tmp/BaseMcpServer-rollback-20260814`.
  - Record the failure and restored state before attempting another deployment.

### Phase 7 Gate

- [x] All four managed servers launch from the intended artifacts, expose the
  expected capabilities through real stdio sessions, and retain valid client
  configuration.

## Phase 8: Closeout

- [x] **V2-800 — Update every checklist status from final evidence.**
  - No item remains `[-]`; every unfinished item is `[ ]` or `[!]` with a reason.
- [x] **V2-801 — Write the final implementation report.**
  - Summarize dependency changes, MCP v2 adaptations, behavior changes, test and
    build results, deployment evidence, remaining risks, and deferred work.
- [x] **V2-802 — Reconcile documentation and evidence links.**
  - All paths and commands in the report must resolve against the final tree.
- [x] **V2-803 — Request separate authorization for repository publication.**
  - Do not commit, push, open a pull request, tag, release, or publish to PyPI
    unless the user explicitly authorizes that action after reviewing results.
  - Authorization remains outstanding; this closeout report requests that
    separate decision without performing any publication action.

## Final Implementation Report

### Delivered Changes

- Refreshed all six dependency locks to current stable resolutions. The only
  apparently newer unresolved package is `pydantic-core` 2.48.0; Pydantic
  2.13.4 intentionally requires its matching Core 2.46.4.
- Captured the public schemas for all 48 tools in
  [`schema-inventory/`](schema-inventory/). No Jira schema exposes `kwargs`.
  Forty-four stable outputs have explicit `TypedDict` schemas. The four
  deliberately open outputs are Jira full issue details and workflow graph
  generation plus Loadbearing analysis submission/result, whose shapes vary by
  requested mode or provider-produced job state.
- Added explicit nullability, typed collection items, Jira/Confluence result
  limits, Loadbearing polling limits, World Context headline limits, and the
  Jira workflow output-format enum.
- Added titles, descriptions, behavior annotations, and package-derived server
  versions for every tool/server while retaining imperative registration.
- Replaced MCP Manager's Pydantic v1 `@validator` with `AfterValidator` on an
  annotated type; no replacement registration/validation decorator was added.
- Moved the Loadbearing executor into server lifespan and retained the existing
  job/polling behavior.
- Replaced Jira workflow base64 output with two imperative `FileResource`
  entries, atomic artifact replacement, URI results, and post-success update
  notification.
- Changed HTTP defaults to loopback and made non-loopback startup require
  explicit allowed-host and allowed-origin lists through MCP v2 transport
  security.
- Updated the Template, MCP Server Creator, active developer guidance, and ADR.
  Generated tools reject decorators, `**kwargs`, untyped parameters, missing
  return types, and bare collection returns. Unknown generated behavior hints
  remain explicitly `None` because effects cannot be inferred safely from a
  function name or syntax alone and must be classified by the author.

### Verification Matrix

| Project | Lock/sync | Tests with `-W error` | Build | Metadata |
| --- | --- | ---: | --- | --- |
| Jira Helper | 63 packages; locked sync passed | 38 passed | wheel + sdist | `jira-helper` 2.2.0, Python >=3.13, `jira-helper = main:main` |
| Loadbearing YouTube | 55 packages; locked sync passed | 10 passed | wheel + sdist | `loadbearing-youtube-mcp-server` 0.1.0, Python >=3.11, `loadbearing-youtube-mcp = main:main` |
| World Context | 51 packages; locked sync passed | 6 passed | wheel + sdist | `worldcontext-mcp-server` 1.3.0, Python >=3.11, `worldcontext = main:main` |
| Template | 38 packages; locked sync passed | 6 passed | wheel + sdist | `template-mcp-server` 0.1.0, Python >=3.11, `template = main:main` |
| MCP Server Creator | 39 packages; locked sync passed | 7 passed, 1 opt-in skipped; opt-in E2E passed separately | wheel + sdist | `mcpservercreator` 1.4.0, Python >=3.11, `mcpservercreator = main:main` |
| MCP Manager | 19 packages; locked sync passed | 3 passed | not a server build target | functional Pydantic v2 validation verified |

The opt-in generator E2E created a fresh project and passed `uv lock`, locked
sync, generated protocol tests with warnings as errors, and `uv build` without
editing the generated output. `git diff --check` passed.

### Managed Deployment

- Baseline and exact rollback inputs are stored at
  `/private/tmp/BaseMcpServer-rollback-20260814` (251 MB). Registry/process-file
  hashes match the pre-deployment originals, and each backed-up environment
  imports MCP 2.0.0.
- Rollback procedure: stop managed clients/processes; move any failed live
  server directory aside; restore the four backed-up server directories to
  their exact original paths; restore `servers.json` and `processes.json`; run
  `mcp-manager sync`, `mcp-manager validate`, and real stdio discovery. Exact
  path restoration is required because virtual-environment script shebangs are
  not relocatable.
- Transactional reinstall preserved all three existing server-specific
  `config.yaml` files byte-for-byte. MCP Manager synchronized Cline, Claude
  Desktop, VS Code, Codex, and Antigravity.
- Final managed stdio verification: Jira 32 tools and two resources, World
  Context 7 tools, MCP Server Creator 3 tools, and Loadbearing YouTube 5 tools.
  Each server reported its package version, complete metadata, structured
  content, and a successful bounded read-only smoke call.

### Remaining Boundary and Risk

- The user separately authorized repository publication as version `v1.6.0`,
  including the commit, push, pull request, tag, and GitHub release. PyPI
  publication remains outside the authorized scope.
- The rollback copy is temporary operating-system storage and should be retained
  only until the user accepts the deployment or replaced with a durable backup
  if a longer rollback window is required.
- Prompts, sampling, elicitation, MCP tasks, and custom middleware remain
  deliberately deferred.

## Completion Criteria

The effort is complete only when:

- every non-deferred checklist item is complete;
- all six dependency graphs are current, stable, locked, and reproducible;
- tool inputs, outputs, errors, annotations, and server versions are truthful;
- no decorator is used merely as a registration or validation convenience;
- managed lifecycle, Jira resource behavior, and HTTP security pass their tests;
- generated projects follow the same conventions as maintained projects;
- all tests, builds, metadata inspections, and real managed stdio checks pass;
- rollback and final-state evidence are recorded; and
- any remaining exception is explicitly approved rather than silently accepted.

## Decisions Made

- Use `mcp>=2.0.0,<3.0.0` rather than an exact release-candidate pin.
- Upgrade all packages, subject to stable-release and compatibility verification.
- Retain imperative `add_tool()` and `add_resource()` registration.
- Use decorators only for genuine aspect-oriented, cross-cutting behavior.
- Adopt v2 capabilities when they improve truthful contracts, lifecycle,
  resource delivery, or transport safety.
- Retain job/polling behavior and avoid speculative prompts, elicitation, and
  sampling.
- Build the Template package but do not install it as an operational server.

## Decisions Explicitly Deferred

- Any new prompts, sampling, elicitation, or MCP tasks adoption.
- Custom middleware beyond demonstrated gaps in supported SDK behavior.
- PyPI publication.
- Unrelated application behavior changes discovered during the upgrade.

## Open Questions

No blocking design question is known at checklist creation. New questions must
be attached to the task that exposed them and must distinguish observed evidence
from the proposed decision.

## Questions For CTO

No implementation-blocking question is currently open. Any newly discovered
scope or architecture choice will be recorded here before work proceeds past the
affected phase gate.

## Decisions Requested

All decisions required for the implementation and the `v1.6.0` tagged GitHub
release have been made. PyPI publication would require separate authorization.

## Evidence Log

| Date | Task | Evidence | Result |
| --- | --- | --- | --- |
| 2026-08-14 | V2-000 | User approved the implementation plan and requested this development checklist. | Complete |
| 2026-08-14 | V2-001 | Repository contains five server `pyproject.toml`/`uv.lock` pairs plus `utils/mcp_manager`. | Complete |
| 2026-08-14 | V2-002 | `git status --short` recorded 13 pre-existing modified files before this checklist was added. | Complete |
| 2026-08-14 | V2-003 | Manifest search and lock inspection show the five stable MCP ranges and `mcp`/`mcp-types` 2.0.0. | Complete |
| 2026-08-14 | V2-004 | Lock inspection found Pydantic 2.14.0a1, Wrapt 2.3.0rc2, HTTPX 1.0.dev3, and isort 9.0.0b1 where applicable. | Complete |
| 2026-08-14 | V2-105 | Release v1.5.4 removed inherited prerelease resolutions; all four managed server environments report no prerelease packages. | Complete |
| 2026-08-14 | V2-500 | Current generator source and regression test require the stable MCP v2 range and reject prerelease configuration. | Complete |
| 2026-08-14 | V2-501 | Current local `BUILD_A_NEW_MCP.md` diff describes stable v2 bounds and removes prerelease instructions. | Complete |
| 2026-08-14 | Release baseline | PR #38 merged as `c2d7831`; GitHub release v1.5.4 published; 55 tests, six package builds, managed validation, and real stdio discovery passed. | Complete |
| 2026-08-14 | V2-100–V2-108 | Full `uv lock --upgrade` and `uv sync --locked --all-extras` completed for all six projects. Resolver updates included Pydantic Settings 2.15.0, Typer 0.27.1, OpenAI 3.0.0, and current stable transitives. `loadbearing-youtube` v0.1.4 remains the newest upstream tag. | Complete |
| 2026-08-14 | Phase 1 gate | Full `uv tree --outdated` leaves only Pydantic Core 2.48.0 unselected because current Pydantic 2.13.4 pins its matching Core 2.46.4. All 55 tests pass after locked synchronization. | Complete |
| 2026-08-14 | V2-200–V2-206 | Five captured schema inventories cover 48 tools; no `kwargs` appears; 44 stable outputs are typed and four conditional/dynamic outputs remain explicitly open. In-memory client tests cover structured success and MCP errors. | Complete |
| 2026-08-14 | V2-300–V2-305 | All tool registrations remain imperative and expose titles, descriptions, classified annotations, and package-derived versions. MCP Manager model tests pass with functional Pydantic v2 validation. | Complete |
| 2026-08-14 | V2-400–V2-431 | Tests verify lifespan-owned executor shutdown, Jira file-resource discovery/read/atomic replacement/notification/failure behavior, loopback HTTP acceptance, rejected hosts/origins, and explicit non-loopback policy. | Complete |
| 2026-08-14 | V2-502–V2-507 | Template, generator, opt-in generated-project E2E, governing ADR, conventions guide, and active docs were updated. Repository search leaves only historical or intentional negative decorator/MCP Commons examples. | Complete |
| 2026-08-14 | V2-600–V2-606 | Six locked suites passed with warnings as errors: 38 + 10 + 6 + 6 + 7 + 3 = 70 tests, with one opt-in E2E skipped in the normal matrix and then passed separately. Five wheel/sdist builds and metadata inspection passed; `git diff --check` passed. | Complete |
| 2026-08-14 | V2-700–V2-707 | A 251 MB exact rollback set was verified, four servers were transactionally reinstalled, configs remained byte-identical, five clients synchronized, four validations passed, and real stdio discovery/smokes returned 32/7/3/5 tools plus two Jira resources. | Complete |
| 2026-08-14 | V2-800–V2-803 | Checklist statuses, final report, evidence links, residual risk, and separate publication-authorization boundary were reconciled. | Complete |
| 2026-08-14 | Release authorization | Human reviewer authorized commit, push, pull request, and a tagged GitHub release as `v1.6.0`; PyPI publication remains excluded. | Complete |

## Publication Scope

- Version: `v1.6.0`.
- Included: commit, push, pull request, merge, Git tag, and GitHub release.
- Excluded: PyPI publication.

## Approval Status

- Governing plan: approved by the user on 2026-08-14.
- This tracking artifact: approved by the user on 2026-08-14.
- Implementation: the pre-checklist stable-SDK migration shipped as v1.5.4;
  the broader checklist implementation and managed local deployment are
  complete. Repository publication as v1.6.0 is authorized.

## Sign-Off

### Author

- Signer: Codex
- Signer Type: agent
- Role: Development checklist author
- Review Perspective: implementation planning and verification
- Disposition: completed-release-authorized
- Summary Notes: Implemented and verified the approved v2 checklist, including
  managed deployment; v1.6.0 repository publication is authorized and PyPI
  publication remains excluded.
- Date: 2026-08-14

### Review Entries

- 2026-08-14 — Human reviewer approved proceeding with the updated checklist
  after completion of the v1.5.4 stable-SDK release.

### Human Sign-Off

- Signer: Human reviewer
- Signer Type: human
- Status: approved

### Workflow Status

- Current Status: implementation and managed deployment complete; v1.6.0
  tagged GitHub release authorized
