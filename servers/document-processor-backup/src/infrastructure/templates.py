"""Template rendering implementations."""

import jinja2
from pathlib import Path
from typing import List

from domain.ports import TemplateRenderer


class Jinja2TemplateRenderer(TemplateRenderer):
    """Jinja2 template renderer implementation."""
    
    def __init__(self, template_directory: Path):
        self._template_dir = template_directory
        self._template_dir.mkdir(parents=True, exist_ok=True)
        
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_directory)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    async def render(self, template_name: str, content: str) -> str:
        """Render content using a template."""
        try:
            template = self._env.get_template(template_name)
            return template.render(content=content)
        except jinja2.TemplateNotFound:
            raise ValueError(f"Template {template_name} not found")
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    async def list_templates(self) -> List[str]:
        """List available templates."""
        templates = []
        if self._template_dir.exists():
            for template_file in self._template_dir.glob("*.html"):
                templates.append(template_file.name)
        return templates
    
    async def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        template_path = self._template_dir / template_name
        return template_path.exists() and template_path.is_file()
