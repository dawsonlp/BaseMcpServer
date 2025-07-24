import yaml
from pathlib import Path
from typing import Dict, Any
from domain.models import ServerConfig, GreetingStyle
from domain.results import Result, Error, ErrorType

class ConfigAdapter:
    """Adapter for configuration management."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
    
    def load_config(self) -> Result[ServerConfig]:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                # Return default configuration
                return Result.ok(ServerConfig(
                    name="uhes60-mcp",
                    version="1.0.0",
                    greetings_file="greetings.txt",
                    default_style=GreetingStyle.CASUAL
                ))
            
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            return Result.ok(ServerConfig(
                name=config_data.get("name", "uhes60-mcp"),
                version=config_data.get("version", "1.0.0"),
                greetings_file=config_data.get("greetings_file", "greetings.txt"),
                default_style=GreetingStyle(config_data.get("default_style", "casual"))
            ))
            
        except Exception as e:
            return Result.fail(Error(
                type=ErrorType.UNKNOWN_ERROR,
                message=f"Failed to load configuration: {str(e)}"
            ))
