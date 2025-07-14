"""
Markdown to TXT converter implementation.
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


class MarkdownToTxtConverter(DocumentConverter):
    """
    Converts markdown documents to plain text format.
    
    This converter creates clean, readable plain text files while preserving structure.
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
        return DocumentFormat.TXT
    
    @property
    def name(self) -> str:
        """Human-readable name of this converter."""
        return "Markdown to TXT Converter"
    
    def convert(self, document: Document, options: ConversionOptions) -> ConversionResult:
        """
        Convert a markdown document to plain text.
        
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
            
            # Step 1: Convert markdown to HTML first
            html_content = self._markdown_to_html(document, options)
            
            # Step 2: Convert HTML to clean text
            text_content = self._html_to_text(html_content, options)
            
            # Step 3: Save to file if requested
            output_file_path = None
            if options.save_to_file:
                output_file_path = self._generate_output_path(document, options)
                output_file_path.write_text(text_content, encoding='utf-8')
            
            # Calculate conversion time
            conversion_time = time.time() - start_time
            
            return ConversionResult.success_result(
                output_content=text_content,
                output_file_path=output_file_path,
                target_format=self.target_format,
                engine_used="html2text",
                conversion_time_seconds=conversion_time,
                metadata={
                    "original_word_count": document.word_count,
                    "original_char_count": document.character_count,
                    "output_word_count": len(text_content.split()),
                    "output_char_count": len(text_content),
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
            # Configure markdown with useful extensions
            md = markdown.Markdown(
                extensions=[
                    'extra',      # Tables, fenced code blocks, etc.
                    'codehilite', # Syntax highlighting
                    'toc',        # Table of contents
                    'meta',       # Metadata support
                ]
            )
            
            html_content = md.convert(document.content)
            return html_content
            
        except Exception as e:
            raise ConversionError(
                source_format=self.source_format.value,
                target_format="HTML (intermediate)",
                message="Failed to convert markdown to HTML",
                details=str(e)
            )
    
    def _html_to_text(self, html_content: str, options: ConversionOptions) -> str:
        """Convert HTML to clean plain text."""
        try:
            import html2text
            
            # Configure html2text for clean output
            h = html2text.HTML2Text()
            h.ignore_links = False  # Keep links as text
            h.ignore_images = True  # Skip images
            h.ignore_emphasis = False  # Keep bold/italic as text markers
            h.body_width = 0  # No line wrapping
            h.unicode_snob = True  # Use unicode characters
            h.bypass_tables = False  # Process tables
            
            # Convert to text
            text_content = h.handle(html_content)
            
            # Clean up the output
            text_content = self._clean_text_output(text_content)
            
            return text_content
            
        except ImportError:
            # Fallback: simple HTML tag removal
            return self._simple_html_to_text(html_content)
        except Exception as e:
            raise ConversionError(
                source_format="HTML",
                target_format=self.target_format.value,
                message="Failed to convert HTML to text",
                details=str(e)
            )
    
    def _simple_html_to_text(self, html_content: str) -> str:
        """Simple fallback HTML to text conversion."""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces to single
        text = text.strip()
        
        return text
    
    def _clean_text_output(self, text: str) -> str:
        """Clean up the text output for better readability."""
        import re
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up list formatting
        text = re.sub(r'\n\s*\*\s+', '\n• ', text)  # Convert * to bullet
        text = re.sub(r'\n\s*-\s+', '\n• ', text)   # Convert - to bullet
        
        # Clean up heading formatting (remove extra #)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Ensure single trailing newline
        text = text.rstrip() + '\n'
        
        return text
    
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
        
        # Ensure .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Use custom output directory if specified
        output_dir = Path(options.output_directory) if options.output_directory else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir / filename
