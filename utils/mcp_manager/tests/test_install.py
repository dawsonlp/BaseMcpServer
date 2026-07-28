"""Regression tests for transactional local server installation."""

import subprocess
from pathlib import Path

import pytest

import mcp_manager.core.state as state_module
from mcp_manager.cli.commands import install as install_module


class FakeState:
    def __init__(self):
        self.added = None

    def get_server(self, name):
        return None

    def add_server(self, server):
        self.added = server

    def update_server(self, server):
        raise AssertionError("No current registry entry should be updated")


def _arrange_install(monkeypatch, tmp_path: Path):
    managed_dir = tmp_path / "managed" / "example"
    managed_dir.mkdir(parents=True)
    (managed_dir / "config.yaml").write_text("token: preserved\n")
    (managed_dir / "old-environment").write_text("present\n")

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "pyproject.toml").write_text("[project]\nname='example'\nversion='1'\n")

    fake_state = FakeState()
    monkeypatch.setattr(install_module, "state", fake_state)
    monkeypatch.setattr(install_module, "_require_uv", lambda: "/usr/bin/uv")
    monkeypatch.setattr(state_module, "get_server_dir", lambda name: managed_dir)
    return managed_dir, source_dir, fake_state


def test_failed_force_install_preserves_live_environment(monkeypatch, tmp_path):
    managed_dir, source_dir, fake_state = _arrange_install(monkeypatch, tmp_path)

    def fake_run(args, **kwargs):
        if args[1] == "venv":
            return subprocess.CompletedProcess(args, 0, "", "")
        return subprocess.CompletedProcess(args, 1, "", "dependency resolution failed")

    monkeypatch.setattr(install_module.subprocess, "run", fake_run)

    with pytest.raises(SystemExit):
        install_module.install_local("example", source_dir, force=True, auto_approve=[])

    assert (managed_dir / "config.yaml").read_text() == "token: preserved\n"
    assert (managed_dir / "old-environment").exists()
    assert fake_state.added is None


def test_successful_force_install_allows_prereleases_and_swaps_atomically(
    monkeypatch, tmp_path
):
    managed_dir, source_dir, fake_state = _arrange_install(monkeypatch, tmp_path)
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if args[1] == "venv":
            python = Path(args[2]) / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.touch()
            script = python.parent / "example"
            script.write_text(f"#!{python}\n")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(install_module.subprocess, "run", fake_run)

    install_module.install_local("example", source_dir, force=True, auto_approve=[])

    pip_call = next(args for args in calls if args[1:3] == ["pip", "install"])
    assert "--prerelease=allow" in pip_call
    assert (managed_dir / "config.yaml").read_text() == "token: preserved\n"
    assert not (managed_dir / "old-environment").exists()
    assert fake_state.added is not None
    assert fake_state.added.venv_dir == managed_dir / ".venv"
    shebang = (managed_dir / ".venv" / "bin" / "example").read_text().strip()
    assert shebang == f"#!{managed_dir / '.venv' / 'bin' / 'python'}"
