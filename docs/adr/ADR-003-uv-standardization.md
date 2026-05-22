# ADR-003: Standardize Local Server Installs on uv

## Status
**Accepted** (mcp-manager 1.1.0, May 2026)

## Context

[ADR-002](ADR-002-pipx-default-installation.md) had mcp-manager defaulting to "pipx-style isolated install" with a `--no-pipx` legacy-flow opt-out. In practice that decision aged badly:

1. **The `--no-pipx` flag was misnamed.** The default path didn't actually shell out to `pipx`; it used the `virtualenv` library plus `pip install <source>` against an internal venv. The opt-out path was an entirely different "source-copy + venv + `pip install -r`" flow. Two install modes lived behind a flag whose name described neither one.
2. **Drift from the broader Python ecosystem.** Through 2025/2026 `uv` consolidated the install/venv/lock/run/tool surfaces into one fast tool. `pipx`'s usefulness narrowed (mostly: "isolated CLI tools globally"), and the rest of the project's docs began telling users to `uv tool install` mcp-manager itself anyway — creating a contradiction with the internal pipx framing.
3. **The pipx-style code path was already a strict subset of what `uv pip install` provides.** `uv venv` + `uv pip install <source>` produces a standard PEP 405 venv with identical layout, so every existing consumer of `venv_dir/bin/<exe>` works unchanged.

## Decision

**Replace every internal install path in mcp-manager with `uv`. Remove the `--no-pipx` flag and the legacy source-copy flow entirely. There is exactly one install method going forward.**

Specifically:

- `mcp-manager install local` runs `uv venv <server>/.venv` then `uv pip install --python <venv-python> <source>` (no fallbacks, no flags to pick a mode).
- The `InstallationType` enum collapses to a single live value (`uv`); the `pipx` and `venv` values are gone.
- The `virtualenv` library is dropped as a dependency (uv handles venv creation).
- `mcp-manager` itself is published for installation via `uv tool install` (pipx is no longer documented as the install path).
- Editor-settings paths (`~/.config/mcp-manager/servers/<name>/.venv/bin/<name>`) are unchanged, so already-installed servers continue to work via `mcp-manager config sync`.

## Migration

mcp-manager 1.2.0 (the cleanup release that finalized this decision) removed the validators that auto-migrated legacy state values. Old registry entries (`installation_type: "pipx"` or `"venv"`, `server_type: "local_stdio"` / `"local_sse"`, etc.) are skipped on load with a clear, actionable message:

```
mcp-manager install local <name> --source <path> --force
```

Per-server `config.yaml` files (API keys, credentials) under `~/.config/mcp-manager/servers/<name>/` are preserved automatically across reinstall — `install local --force` backs up and restores `config.yaml`. The auto-migration of `~/.mcp_servers` → `~/.config/mcp-manager` was also removed; the new install root has been the only documented location for years.

## Consequences

### Positive

- **One install method to document and reason about.** Reduced ~250 lines of branching code and several confusingly-named flags.
- **No `virtualenv` dependency.** uv supplies a faster, statically-linked venv creator.
- **Aligned with the wider project's install story.** Everything in this repo now installs via `uv tool install` or `mcp-manager install local`; the words "pipx" and "virtualenv" are no longer needed in user-facing docs.
- **Cache wins on reinstall.** uv's content-addressed cache makes `--force` reinstalls noticeably faster.

### Negative

- **uv is now a hard requirement on `PATH`.** `mcp-manager install local` fails fast with a helpful install pointer if `shutil.which("uv")` returns None.
- **Loss of `pipx` as an alternative install channel for mcp-manager itself.** A user who already has pipx but not uv has one more tool to install. We judged this an acceptable trade for narrative simplicity.
- **No automatic migration of pre-1.1.0 registry entries.** Affected users must run `mcp-manager install local <name> --source <path> --force` per server. Config files survive; the registry entry is rewritten.

## Implementation

Implemented across three commits on `main`:

- `6eac7d4` — `refactor(mcp-manager): standardize local server installs on uv (v1.1.0)` — replaced the install internals, dropped the `--no-pipx` flag and the legacy source-copy branch, collapsed the `InstallationType` enum, removed the `virtualenv` dependency.
- `8990c5a` — `refactor(mcp-manager): rewrite platforms.py; drop legacy migrations (v1.2.0)` — finalized cleanup by removing the legacy state-load validators and the `~/.mcp_servers` auto-migrator, and adding the actionable skip message described above.
- `46350bc` — `docs: remove ghost references and refresh mcp-manager command listings` — purged residual ghost commands from help text and the docs surface.

## Alternatives Considered

### Keep the `--no-pipx` source-copy flow as a fallback
Rejected. Two install modes meant two sets of documentation, two test paths, and a flag whose name described neither. The source-copy flow was only useful for servers without a `pyproject.toml`, and we already require a `pyproject.toml` for every server in this repo.

### Detect uv vs. pip at runtime
Rejected. Adds a fragile probe step. uv installs cleanly; mandating it removes a class of ambiguity.

### Keep pipx as a parallel install channel for mcp-manager itself
Rejected for documentation simplicity. Users who prefer pipx can still run `pipx install ./utils/mcp_manager` — it's not blocked, just no longer documented.

## Related

- [ADR-002](ADR-002-pipx-default-installation.md) — the (now superseded) decision this replaces
- [`utils/mcp_manager/README.md`](../../utils/mcp_manager/README.md) — current user-facing install instructions
- [`QUICKSTART.md`](../../QUICKSTART.md) — current end-to-end onboarding
