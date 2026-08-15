import json
from pathlib import Path

import pytest

import mcp_manager.core.platforms as platforms
from mcp_manager.core.models import PlatformType, Server, ServerType


def _server(tmp_path: Path) -> Server:
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text(
        '[project]\nname="example-package"\nversion="1"\n'
        '[project.scripts]\nexample-mcp="main:main"\n'
    )
    venv = tmp_path / "venv"
    executable = venv / "bin" / "example-mcp"
    executable.parent.mkdir(parents=True)
    executable.touch()
    return Server(name="example", server_type=ServerType.LOCAL, source_dir=source, venv_dir=venv)


@pytest.mark.parametrize(
    ("platform", "container", "expected"),
    [
        (PlatformType.CLINE, "mcpServers", {"disabled": False, "autoApprove": []}),
        (PlatformType.CLAUDE_DESKTOP, "mcpServers", {}),
        (PlatformType.VSCODE, "servers", {"type": "stdio"}),
        (PlatformType.ANTIGRAVITY, "mcpServers", {}),
    ],
)
def test_file_profiles_share_resolution_without_losing_specific_fields(
    tmp_path, platform, container, expected
):
    entry = platforms.build_mcp_server_entry(_server(tmp_path), platform)
    assert entry is not None
    assert entry["command"].endswith("/bin/example-mcp")
    assert entry["args"] == ["stdio"]
    for key, value in expected.items():
        assert entry[key] == value
    assert platforms.platform_container_key(platform) == container


def test_malformed_settings_are_not_treated_as_empty(monkeypatch, tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{broken")
    monkeypatch.setattr(platforms, "get_platform_settings_path", lambda _platform: path)
    with pytest.raises(RuntimeError, match="Cannot safely read"):
        platforms.read_platform_settings(PlatformType.CLINE)
    assert path.read_text() == "{broken"


def test_settings_write_replaces_atomically_and_preserves_payload(monkeypatch, tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"unrelated": True}))
    monkeypatch.setattr(platforms, "get_platform_settings_path", lambda _platform: path)
    payload = {"unrelated": True, "mcpServers": {"example": {"command": "x"}}}
    platforms.write_platform_settings(PlatformType.CLINE, payload)
    assert json.loads(path.read_text()) == payload
    assert list(tmp_path.iterdir()) == [path]
