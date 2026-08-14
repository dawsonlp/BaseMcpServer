"""Opt-in end-to-end verification of a freshly generated server package."""

import os
import subprocess

import pytest

from server import create_server_files, validate_code_snippet


@pytest.mark.skipif(
    os.environ.get("RUN_GENERATOR_E2E") != "1",
    reason="set RUN_GENERATOR_E2E=1 for lock, sync, test, and build verification",
)
def test_generated_project_locks_tests_and_builds(tmp_path):
    snippet = '''
def add_numbers(a: int, b: int) -> dict[str, int]:
    """Add two numbers."""
    return {"result": a + b}
'''
    project = tmp_path / "generated-contract-server"
    tool_names = validate_code_snippet(snippet)
    create_server_files(
        server_dir=project,
        server_name="generated-contract-server",
        code_snippet=snippet,
        description="Generated contract test",
        author="Test",
        tool_names=tool_names,
    )

    environment = {**os.environ, "UV_CACHE_DIR": str(tmp_path / "uv-cache")}
    for command in (
        ["uv", "lock"],
        ["uv", "sync", "--locked", "--extra", "dev"],
        ["uv", "run", "--locked", "pytest", "-q", "-W", "error"],
        ["uv", "build"],
    ):
        completed = subprocess.run(
            command,
            cwd=project,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, (
            f"{' '.join(command)} failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )

    assert (project / "uv.lock").exists()
    assert list((project / "dist").glob("*.whl"))
    assert list((project / "dist").glob("*.tar.gz"))
