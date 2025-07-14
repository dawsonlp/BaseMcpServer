"""Configuration provider implementation."""

from pathlib import Path
from domain.models import PDFEngine
from domain.ports import ConfigurationProvider
from config import settings


class SettingsConfigurationProvider(ConfigurationProvider):
    """Configuration provider using the settings module."""
    
    def get_output_directory(self) -> Path:
        """Get the output directory path."""
        return Path(settings.output_directory)
    
    def get_input_directory(self) -> Path:
        """Get the input directory path."""
        return Path(settings.input_directory)
    
    def get_template_directory(self) -> Path:
        """Get the template directory path."""
        return Path(settings.html_template_dir)
    
    def get_default_pdf_engine(self) -> PDFEngine:
        """Get the default PDF engine."""
        return PDFEngine(settings.pdf_engine)
    
    def get_max_file_size_mb(self) -> int:
        """Get the maximum file size in MB."""
        return settings.max_file_size_mb
