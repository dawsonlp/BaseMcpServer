"""
Markdown to HTML converter implementation.
"""

import time
from pathlib import Path
from typing import Optional
import markdown
from datetime import datetime

from domain import (
    Document, DocumentFormat, ConversionOptions, ConversionResult, 
    DocumentConverter
)
from domain.exceptions import ConversionError
from .mermaid_processor import preprocess_mermaid


class MarkdownToHtmlConverter(DocumentConverter):
    """
    Converts markdown documents to HTML format.
    
    This converter generates clean, standalone HTML files with basic styling.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the converter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir or Path("output")
        
        # Ensure directory exists
        self.output_dir.mkdir(exist_ok=True)
    
    @property
    def source_format(self) -> DocumentFormat:
        """The source format this converter accepts."""
        return DocumentFormat.MARKDOWN
    
    @property
    def target_format(self) -> DocumentFormat:
        """The target format this converter produces."""
        return DocumentFormat.HTML
    
    @property
    def name(self) -> str:
        """Human-readable name of this converter."""
        return "Markdown to HTML Converter"
    
    def convert(self, document: Document, options: ConversionOptions) -> ConversionResult:
        """
        Convert a markdown document to HTML.
        
        Args:
            document: The source markdown document
            options: Conversion options and settings
            
        Returns:
            ConversionResult with the conversion outcome
        """
        start_time = time.time()
        
        try:
            # Validate the document
            self.validate_document(document)
            
            # Step 1: Convert markdown to HTML
            html_content = self._markdown_to_html(document, options)
            
            # Step 2: Wrap in complete HTML document if requested
            if options.standalone:
                html_content = self._create_standalone_html(html_content, document, options)
            
            # Step 3: Save to file if requested
            output_file_path = None
            if options.save_to_file:
                output_file_path = self._generate_output_path(document, options)
                output_file_path.write_text(html_content, encoding='utf-8')
            
            # Calculate conversion time
            conversion_time = time.time() - start_time
            
            return ConversionResult.success_result(
                output_content=html_content,
                output_file_path=output_file_path,
                target_format=self.target_format,
                engine_used="python-markdown",
                conversion_time_seconds=conversion_time,
                metadata={
                    "original_word_count": document.word_count,
                    "original_char_count": document.character_count,
                    "standalone": options.standalone,
                    "include_css": options.include_css,
                }
            )
            
        except Exception as e:
            conversion_time = time.time() - start_time
            
            return ConversionResult.error_result(
                error_message=str(e),
                error_details=f"Conversion failed after {conversion_time:.2f} seconds",
                target_format=self.target_format,
                conversion_time_seconds=conversion_time
            )
    
    def _markdown_to_html(self, document: Document, options: ConversionOptions) -> str:
        """Convert markdown content to HTML."""
        try:
            # Step 1: Preprocess Mermaid diagrams
            output_dir = Path(options.output_directory) if options.output_directory else self.output_dir
            processed_content = preprocess_mermaid(
                document.content, 
                output_dir=output_dir,
                image_format="svg",  # SVG works better in HTML
                theme="default"
            )
            
            # Step 2: Configure markdown with useful extensions
            md = markdown.Markdown(
                extensions=[
                    'extra',      # Tables, fenced code blocks, etc.
                    'codehilite', # Syntax highlighting
                    'toc',        # Table of contents
                    'meta',       # Metadata support
                ]
            )
            
            html_content = md.convert(processed_content)
            return html_content
            
        except Exception as e:
            raise ConversionError(
                source_format=self.source_format.value,
                target_format=self.target_format.value,
                message="Failed to convert markdown to HTML",
                details=str(e)
            )
    
    def _create_standalone_html(self, html_content: str, document: Document, options: ConversionOptions) -> str:
        """Create a complete HTML document with styling."""
        title = options.title or document.metadata.title or "Document"
        author = options.author or document.metadata.author
        
        # Basic CSS for clean styling
        css = """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        
        h1 {
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        
        pre {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            margin: 1rem 0;
            padding-left: 1rem;
            color: #666;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 0.5rem;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
        }
        
        .metadata {
            font-size: 0.9rem;
            color: #666;
            border-top: 1px solid #eee;
            margin-top: 2rem;
            padding-top: 1rem;
        }
        """ if options.include_css else ""
        
        # Build complete HTML document
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>"""
        
        if css:
            html_doc += f"""
    <style>
{css}
    </style>"""
        
        html_doc += """
</head>
<body>
"""
        
        html_doc += html_content
        
        # Add metadata if available
        if author or document.metadata.created_at:
            html_doc += """
    <div class="metadata">"""
            if author:
                html_doc += f"""
        <p><strong>Author:</strong> {author}</p>"""
            if document.metadata.created_at:
                html_doc += f"""
        <p><strong>Created:</strong> {document.metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>"""
            html_doc += """
    </div>"""
        
        html_doc += """
</body>
</html>"""
        
        return html_doc
    
    def _generate_output_path(self, document: Document, options: ConversionOptions) -> Path:
        """Generate the output file path."""
        if options.filename:
            filename = options.filename
        elif document.metadata.title:
            # Use document title, sanitized for filename
            filename = "".join(c for c in document.metadata.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = filename.replace(' ', '_')
        else:
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"document_{timestamp}"
        
        # Ensure .html extension
        if not filename.endswith('.html'):
            filename += '.html'
        
        # Use custom output directory if specified
        output_dir = Path(options.output_directory) if options.output_directory else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir / filename
