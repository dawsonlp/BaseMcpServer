# Pipx Installation and Configuration Checklist

This document outlines the development plan for adding `pipx` installation support to `mcp-manager`. The goal is to provide an alternative, more robust installation method for local MCP servers, treating them as first-class Python CLI applications.

## Phase 1: Core `pipx` Integration

-   [ ] **Extend `LocalServer` Model:**
    -   Add a new field `installation_type` to the `LocalServer` model in `server.py`. This will be an `Enum` with values like `VENV` (current method) and `PIPX`.
    -   Add an optional `package_name` field to store the PyPI package name if it differs from the server name.
    -   Add an optional `executable_name` field to store the name of the pipx-installed executable.

-   [ ] **Create `install` Command Extension:**
    -   Modify the `install` command in `mcp_manager/commands/install.py`.
    -   Add a `--pipx` flag to trigger installation via `pipx`.
    -   When `--pipx` is used, the command should:
        -   Run `pipx install .` from the server's source directory.
        -   Verify the installation was successful by checking the output and `pipx list`.
        -   Store the installation type as `PIPX` in the server registry.
        -   Identify and store the executable path provided by `pipx`.

-   [ ] **Update `configure` Command:**
    -   Modify `configure_vscode_cline` in `mcp_manager/commands/configure.py`.
    -   Add a condition to check the `installation_type` of the `LocalServer`.
    -   If the type is `PIPX`:
        -   The `command` in `cline_mcp_settings.json` should be the path to the pipx-installed executable (e.g., `~/.local/bin/jira-helper`).
        -   The `args` should be `["stdio"]`.
        -   The `options` (like `cwd` and `PYTHONPATH`) will no longer be necessary, as `pipx` handles the environment.
    -   If the type is `VENV`, the behavior should remain as it is now (pointing to the venv's Python).

## Phase 2: Server Packaging and Distribution

-   [ ] **Standardize `pyproject.toml` for Servers:**
    -   Ensure each local server (like `jira-helper`) has a `pyproject.toml` file that correctly defines its entry points.
    -   The `[project.scripts]` section should define the executable name. For example: `jira-helper = "jira_helper.main:app"`.

-   [ ] **Refactor Server Entry Points:**
    -   Ensure each server's `main.py` is structured to work as a CLI application, preferably using a library like `typer` or `click`, which is already a dependency of `mcp-manager`. This will standardize argument parsing (`stdio`, `sse`, etc.).

-   [ ] **Build and Test Distribution:**
    -   Add a script or command to build a distributable wheel (`.whl`) for each server.
    -   Test installing the built wheel using `pipx install <path_to_wheel>`.

## Phase 3: Uninstallation and Management

-   [ ] **Extend `uninstall` Command:**
    -   Modify the `uninstall` command in `mcp_manager/commands/uninstall.py`.
    -   If the server's `installation_type` is `PIPX`, the command should run `pipx uninstall <package_name>`.
    -   It should also remove the server entry from the registry.

-   [ ] **Documentation:**
    -   Update `README.md` to explain the new `--pipx` installation option.
    -   Document the required `pyproject.toml` structure for any new servers to be compatible with `pipx` installation.
