"""Configuration management for the WorldContext MCP server."""

import os
from pathlib import Path
from typing import Any

import yaml


def _convert_env_value(value: str) -> str | int | float | bool:
    lowered = value.lower()
    if lowered in {"true", "yes", "1", "on"}:
        return True
    if lowered in {"false", "no", "0", "off"}:
        return False
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class ServerConfig:
    """Small YAML configuration reader with environment-variable overrides."""

    def __init__(self, server_name: str, env_prefix: str):
        self.env_prefix = env_prefix
        candidates = (
            Path.home() / ".config" / "mcp-manager" / "servers" / server_name / "config.yaml",
            Path.home() / ".config" / server_name / "config.yaml",
            Path.cwd() / "config.yaml",
        )
        config_path = next((path for path in candidates if path.exists()), None)
        self.config_data: dict[str, Any] = {}
        if config_path is not None:
            self.config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    def get(self, section: str, key: str, default: Any = None) -> Any:
        env_name = f"{self.env_prefix}_{section.upper()}_{key.upper()}"
        if env_name in os.environ:
            return _convert_env_value(os.environ[env_name])
        section_data = self.config_data.get(section, {})
        return section_data.get(key, default) if isinstance(section_data, dict) else default


_load_dotenv(Path.cwd() / ".env")
config = ServerConfig(server_name="worldcontext", env_prefix="WORLDCONTEXT")
