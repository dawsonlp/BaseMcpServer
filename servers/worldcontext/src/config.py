from pathlib import Path
import yaml

class Config:
    def __init__(self, long_name: str, short_name: str):
        self.long_name = long_name
        self.short_name = short_name
        with open(self._find_config()) as f:
            self.data = yaml.safe_load(f) or {}
    
    def _find_config(self):
        for path in [
            Path.home() / ".config" / self.short_name / "config.yaml",
            Path.cwd() / "config.yaml" ]:
            if path.exists():
                return path
        raise FileNotFoundError(f"No config.yaml found for {self.long_name}")
    
    def get(self, *keys, default=None):
        current = self.data
        for key in keys:
            current = current.get(key, {}) if isinstance(current, dict) else {}
        return current if current != {} else default

config = Config("WorldContext MCP Server", "worldcontext")
