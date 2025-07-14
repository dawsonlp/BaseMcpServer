"""
Markdown to PDF converter implementation.
"""

import time
from pathlib import Path
from typing import Optional
import markdown
import jinja2
from datetime import datetime

from domain import (
    Document, DocumentFormat, ConversionOptions, ConversionResult, 
    DocumentConverter, PDFEngine
)
from domain.exceptions import ConversionError, TemplateError
from .mermaid_processor import preprocess_mermaid


class MarkdownToPdfConverter(DocumentConverter):
    """
    Converts markdown documents to PDF format.
    
    This converter first converts markdown to HTML, then uses various PDF engines
    to generate the final PDF output.
    """
    
    def __init__(self, template_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Initialize the converter.
        
        Args:
            template_dir: Directory containing HTML templates
            output_dir: Directory for output files
        """
        self.template_dir = template_dir or Path("templates")
        self.output_dir = output_dir or Path("output")
        
        # Ensure directories exist
        self.template_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    @property
    def source_format(self) -> DocumentFormat:
        """The source format this converter accepts."""
        return DocumentFormat.MARKDOWN
    
    @property
    def target_format(self) -> DocumentFormat:
        """The target format this converter produces."""
        return DocumentFormat.PDF
    
    @property
    def name(self) -> str:
        """Human-readable name of this converter."""
        return "Markdown to PDF Converter"
    
    def convert(self, document: Document, options: ConversionOptions) -> ConversionResult:
        """
        Convert a markdown document to PDF.
        
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
            
            # Step 2: Convert HTML to PDF using specified engine
            output_file_path = self._generate_output_path(document, options)
            self._html_to_pdf(html_content, output_file_path, options)
            
            # Calculate conversion time
            conversion_time = time.time() - start_time
            
            return ConversionResult.success_result(
                output_file_path=output_file_path,
                target_format=self.target_format,
                engine_used=options.pdf_engine.value,
                conversion_time_seconds=conversion_time,
                metadata={
                    "original_word_count": document.word_count,
                    "original_char_count": document.character_count,
                    "pdf_engine": options.pdf_engine.value,
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
                image_format="png",  # PNG works better in PDFs
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
                target_format="HTML (intermediate)",
                message="Failed to convert markdown to HTML",
                details=str(e)
            )
    
    def _apply_template(self, html_content: str, document: Document, options: ConversionOptions) -> str:
        """Apply Jinja2 template to HTML content."""
        try:
            template = self.jinja_env.get_template(options.template_name)
            
            # Prepare template context
            context = {
                'content': html_content,
                'title': options.title or document.metadata.title or "Document",
                'author': options.author or document.metadata.author,
                'subject': options.subject or document.metadata.subject,
                'created_at': document.metadata.created_at,
                'word_count': document.word_count,
                'character_count': document.character_count,
            }
            
            # Add custom options to context
            if options.custom_options:
                context.update(options.custom_options)
            
            return template.render(**context)
            
        except jinja2.TemplateNotFound:
            raise TemplateError(
                template_name=options.template_name,
                message="Template not found",
                details=f"Template '{options.template_name}' not found in {self.template_dir}"
            )
        except Exception as e:
            raise TemplateError(
                template_name=options.template_name,
                message="Template rendering failed",
                details=str(e)
            )
    
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
        
        # Ensure .pdf extension
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Use custom output directory if specified
        output_dir = Path(options.output_directory) if options.output_directory else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir / filename
    
    def _html_to_pdf(self, html_content: str, output_path: Path, options: ConversionOptions) -> None:
        """Convert HTML to PDF using the specified engine."""
        engine = options.pdf_engine
        
        if engine == PDFEngine.WEASYPRINT:
            self._weasyprint_to_pdf(html_content, output_path, options)
        elif engine == PDFEngine.REPORTLAB:
            self._reportlab_to_pdf(html_content, output_path, options)
        elif engine == PDFEngine.PANDOC:
            self._pandoc_to_pdf(html_content, output_path, options)
        else:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message=f"Unsupported PDF engine: {engine.value}",
                details=f"Available engines: {[e.value for e in PDFEngine]}"
            )
    
    def _weasyprint_to_pdf(self, html_content: str, output_path: Path, options: ConversionOptions) -> None:
        """Convert HTML to PDF using WeasyPrint."""
        try:
            import weasyprint
            
            # If the content doesn't look like a complete HTML document, wrap it
            if not html_content.strip().startswith('<!DOCTYPE') and not html_content.strip().startswith('<html'):
                # Wrap in basic HTML structure
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #ddd; margin: 0; padding-left: 20px; color: #666; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
            
            # Create HTML document
            html_doc = weasyprint.HTML(string=html_content)
            
            # Generate PDF
            html_doc.write_pdf(str(output_path))
            
        except ImportError:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="WeasyPrint not available",
                details="Install WeasyPrint: pip install weasyprint"
            )
        except Exception as e:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="WeasyPrint conversion failed",
                details=str(e)
            )
    
    def _reportlab_to_pdf(self, html_content: str, output_path: Path, options: ConversionOptions) -> None:
        """Convert HTML to PDF using ReportLab (basic implementation)."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter, A4
            from html2text import html2text
            
            # Convert HTML to plain text (ReportLab doesn't handle HTML directly)
            text_content = html2text(html_content)
            
            # Choose page size
            page_size = A4 if options.page_size == "A4" else letter
            
            # Create PDF
            c = canvas.Canvas(str(output_path), pagesize=page_size)
            width, height = page_size
            
            # Simple text rendering (this is a basic implementation)
            y_position = height - 50
            for line in text_content.split('\n'):
                if y_position < 50:  # Start new page
                    c.showPage()
                    y_position = height - 50
                
                c.drawString(50, y_position, line[:80])  # Limit line length
                y_position -= 15
            
            c.save()
            
        except ImportError:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="ReportLab not available",
                details="Install ReportLab: pip install reportlab"
            )
        except Exception as e:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="ReportLab conversion failed",
                details=str(e)
            )
    
    def _pandoc_to_pdf(self, html_content: str, output_path: Path, options: ConversionOptions) -> None:
        """Convert HTML to PDF using Pandoc."""
        try:
            import subprocess
            import tempfile
            
            # Write HTML to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
                temp_file.write(html_content)
                temp_html_path = temp_file.name
            
            try:
                # Build pandoc command
                cmd = [
                    'pandoc',
                    temp_html_path,
                    '-o', str(output_path),
                    '--pdf-engine=weasyprint',  # Use weasyprint as PDF engine
                ]
                
                # Add page size if specified
                if options.page_size:
                    cmd.extend(['-V', f'papersize={options.page_size.lower()}'])
                
                # Run pandoc
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
            finally:
                # Clean up temporary file
                Path(temp_html_path).unlink(missing_ok=True)
                
        except subprocess.CalledProcessError as e:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="Pandoc conversion failed",
                details=f"Pandoc error: {e.stderr}"
            )
        except FileNotFoundError:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="Pandoc not found",
                details="Install Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="Pandoc conversion failed",
                details=str(e)
            )
