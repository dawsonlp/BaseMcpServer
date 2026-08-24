import pytest

import mcp_manager.core.state as state


@pytest.mark.parametrize("platform", ["darwin", "linux"])
def test_supported_platforms_are_accepted(monkeypatch, platform):
    monkeypatch.setattr(state.sys, "platform", platform)
    state.ensure_supported_platform()


def test_windows_is_rejected_explicitly(monkeypatch):
    monkeypatch.setattr(state.sys, "platform", "win32")
    with pytest.raises(RuntimeError, match="supports macOS and Linux"):
        state.ensure_supported_platform()
