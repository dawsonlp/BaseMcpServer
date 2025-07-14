"""
Mermaid diagram processor for markdown documents.

This module handles the conversion of Mermaid diagrams in markdown to images
that can be embedded in the final document.
"""

import re
import base64
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import hashlib


class MermaidProcessor:
    """
    Processes Mermaid diagrams in markdown content.
    
    Converts Mermaid code blocks to images and updates the markdown
    to reference the generated images.
    """
    
    def __init__(self, output_format: str = "png", theme: str = "default"):
        """
        Initialize the Mermaid processor.
        
        Args:
            output_format: Image format for diagrams (png, svg)
            theme: Mermaid theme (default, dark, forest, etc.)
        """
        self.output_format = output_format.lower()
        self.theme = theme
        self.diagram_cache: Dict[str, str] = {}
        
    def process_markdown(self, content: str, output_dir: Optional[Path] = None) -> str:
        """
        Process markdown content and convert Mermaid diagrams to images.
        
        Args:
            content: Markdown content with Mermaid diagrams
            output_dir: Directory to save diagram images
            
        Returns:
            Updated markdown content with image references
        """
        if output_dir is None:
            output_dir = Path.cwd() / "output"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Find all Mermaid code blocks
        mermaid_pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = re.finditer(mermaid_pattern, content, re.DOTALL | re.IGNORECASE)
        
        processed_content = content
        offset = 0
        
        for match in matches:
            diagram_code = match.group(1).strip()
            
            # Generate unique filename based on diagram content
            diagram_hash = hashlib.md5(diagram_code.encode()).hexdigest()[:8]
            image_filename = f"mermaid_diagram_{diagram_hash}.{self.output_format}"
            image_path = output_dir / image_filename
            
            try:
                # Generate the diagram image
                self._generate_diagram(diagram_code, image_path)
                
                # Replace the Mermaid code block with an image reference
                # Use file:// URL for PDF generation to work with WeasyPrint
                image_ref = f"![Mermaid Diagram](file://{image_path.absolute()})"
                
                start_pos = match.start() + offset
                end_pos = match.end() + offset
                
                processed_content = (
                    processed_content[:start_pos] + 
                    image_ref + 
                    processed_content[end_pos:]
                )
                
                # Update offset for subsequent replacements
                offset += len(image_ref) - (end_pos - start_pos)
                
            except Exception as e:
                # If diagram generation fails, leave the original code block
                # but add an error comment
                error_comment = f"\n<!-- Mermaid diagram generation failed: {str(e)} -->\n"
                
                start_pos = match.end() + offset
                processed_content = (
                    processed_content[:start_pos] + 
                    error_comment + 
                    processed_content[start_pos:]
                )
                offset += len(error_comment)
        
        return processed_content
    
    def _generate_diagram(self, diagram_code: str, output_path: Path) -> None:
        """
        Generate a Mermaid diagram image.
        
        Args:
            diagram_code: Mermaid diagram code
            output_path: Path to save the generated image
        """
        # Check cache first
        cache_key = f"{diagram_code}_{self.theme}_{self.output_format}"
        if cache_key in self.diagram_cache:
            cached_path = Path(self.diagram_cache[cache_key])
            if cached_path.exists():
                # Copy cached file to output location
                import shutil
                shutil.copy2(cached_path, output_path)
                return
        
        # Create temporary file for Mermaid code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as temp_file:
            temp_file.write(diagram_code)
            temp_mmd_path = Path(temp_file.name)
        
        try:
            # Try different methods to generate the diagram
            success = False
            
            # Method 1: Try mermaid-cli (mmdc)
            if not success:
                success = self._try_mermaid_cli(temp_mmd_path, output_path)
            
            # Method 2: Try playwright with mermaid-py
            if not success:
                success = self._try_mermaid_py(diagram_code, output_path)
            
            # Method 3: Try Node.js mermaid directly
            if not success:
                success = self._try_node_mermaid(temp_mmd_path, output_path)
            
            if not success:
                raise RuntimeError("All Mermaid generation methods failed")
            
            # Cache the successful result
            self.diagram_cache[cache_key] = str(output_path)
            
        finally:
            # Clean up temporary file
            temp_mmd_path.unlink(missing_ok=True)
    
    def _try_mermaid_cli(self, input_path: Path, output_path: Path) -> bool:
        """Try generating diagram using mermaid-cli (mmdc)."""
        try:
            cmd = [
                "mmdc",
                "-i", str(input_path),
                "-o", str(output_path),
                "-t", self.theme,
                "-f"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0 and output_path.exists()
            
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _try_mermaid_py(self, diagram_code: str, output_path: Path) -> bool:
        """Try generating diagram using simple text-to-image fallback."""
        try:
            # For now, create a simple placeholder image with the diagram type
            first_line = diagram_code.split('\n')[0].strip()
            diagram_type = "unknown"
            
            if first_line.startswith(('graph', 'flowchart')):
                diagram_type = "flowchart"
            elif first_line.startswith('sequenceDiagram'):
                diagram_type = "sequence"
            elif first_line.startswith('classDiagram'):
                diagram_type = "class"
            elif first_line.startswith('stateDiagram'):
                diagram_type = "state"
            elif first_line.startswith('erDiagram'):
                diagram_type = "er"
            elif first_line.startswith('gantt'):
                diagram_type = "gantt"
            elif first_line.startswith('pie'):
                diagram_type = "pie"
            
            # Create a simple SVG placeholder
            if self.output_format == "svg":
                svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="200" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
  <text x="200" y="80" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#495057">
    Mermaid {diagram_type.title()} Diagram
  </text>
  <text x="200" y="110" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#6c757d">
    (Diagram generation not available)
  </text>
  <text x="200" y="130" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#6c757d">
    Install mermaid-cli for full support
  </text>
</svg>"""
                output_path.write_text(svg_content, encoding='utf-8')
                return True
            else:
                # For PNG, create a simple text file that can be converted later
                # This is a fallback - in production you'd want proper image generation
                return False
            
        except Exception:
            return False
    
    def _try_node_mermaid(self, input_path: Path, output_path: Path) -> bool:
        """Try generating diagram using Node.js mermaid directly."""
        try:
            # Create a simple Node.js script to generate the diagram
            node_script = f"""
const mermaid = require('mermaid');
const fs = require('fs');
const {{ JSDOM }} = require('jsdom');

const dom = new JSDOM('<!DOCTYPE html><div id="mermaid"></div>');
global.window = dom.window;
global.document = dom.window.document;

mermaid.initialize({{ 
    theme: '{self.theme}',
    startOnLoad: false 
}});

const diagramCode = fs.readFileSync('{input_path}', 'utf8');

mermaid.render('diagram', diagramCode).then((result) => {{
    fs.writeFileSync('{output_path}', result.svg);
    console.log('Diagram generated successfully');
}}).catch((error) => {{
    console.error('Error generating diagram:', error);
    process.exit(1);
}});
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
                temp_file.write(node_script)
                temp_js_path = Path(temp_file.name)
            
            try:
                result = subprocess.run(
                    ["node", str(temp_js_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return result.returncode == 0 and output_path.exists()
                
            finally:
                temp_js_path.unlink(missing_ok=True)
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def extract_mermaid_diagrams(self, content: str) -> List[Tuple[str, str]]:
        """
        Extract all Mermaid diagrams from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of tuples (diagram_code, diagram_type)
        """
        mermaid_pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = re.finditer(mermaid_pattern, content, re.DOTALL | re.IGNORECASE)
        
        diagrams = []
        for match in matches:
            diagram_code = match.group(1).strip()
            
            # Try to determine diagram type from the first line
            first_line = diagram_code.split('\n')[0].strip()
            diagram_type = "unknown"
            
            if first_line.startswith(('graph', 'flowchart')):
                diagram_type = "flowchart"
            elif first_line.startswith('sequenceDiagram'):
                diagram_type = "sequence"
            elif first_line.startswith('classDiagram'):
                diagram_type = "class"
            elif first_line.startswith('stateDiagram'):
                diagram_type = "state"
            elif first_line.startswith('erDiagram'):
                diagram_type = "er"
            elif first_line.startswith('gantt'):
                diagram_type = "gantt"
            elif first_line.startswith('pie'):
                diagram_type = "pie"
            
            diagrams.append((diagram_code, diagram_type))
        
        return diagrams
    
    def validate_mermaid_syntax(self, diagram_code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Mermaid diagram syntax.
        
        Args:
            diagram_code: Mermaid diagram code
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic syntax validation
            lines = diagram_code.strip().split('\n')
            if not lines:
                return False, "Empty diagram"
            
            first_line = lines[0].strip()
            
            # Check for valid diagram types
            valid_starts = [
                'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
                'stateDiagram', 'erDiagram', 'gantt', 'pie', 'journey',
                'gitgraph', 'mindmap', 'timeline'
            ]
            
            if not any(first_line.startswith(start) for start in valid_starts):
                return False, f"Unknown diagram type: {first_line}"
            
            # Additional validation could be added here
            return True, None
            
        except Exception as e:
            return False, str(e)


def preprocess_mermaid(content: str, output_dir: Optional[Path] = None, 
                      image_format: str = "png", theme: str = "default") -> str:
    """
    Convenience function to preprocess Mermaid diagrams in markdown.
    
    Args:
        content: Markdown content with Mermaid diagrams
        output_dir: Directory to save diagram images
        image_format: Image format for diagrams (png, svg)
        theme: Mermaid theme
        
    Returns:
        Processed markdown content
    """
    processor = MermaidProcessor(output_format=image_format, theme=theme)
    return processor.process_markdown(content, output_dir)
