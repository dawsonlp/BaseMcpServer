"""
Main CLI application for document processing.

This module provides a Typer-based command-line interface that uses
the application layer to perform document conversions.
"""

import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from application import (
    DocumentProcessingService, ConvertDocumentUseCase, 
    ListConvertersUseCase, ValidateInputUseCase
)
from domain import DocumentFormat

# Initialize CLI app and console
app = typer.Typer(
    name="mdproc",
    help="Convert markdown documents to various formats (PDF, HTML, DOCX, TXT)",
    add_completion=False
)
console = Console()


def get_service() -> DocumentProcessingService:
    """Get the document processing service."""
    return DocumentProcessingService()


@app.command()
def convert(
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i", 
        help="Input markdown file path"
    ),
    content: Optional[str] = typer.Option(
        None, "--content", "-c",
        help="Markdown content as string"
    ),
    output_format: str = typer.Option(
        "pdf", "--format", "-f",
        help="Output format (pdf, html, docx, txt)"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Output filename (without extension)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-d",
        help="Output directory"
    ),
    title: Optional[str] = typer.Option(
        None, "--title", "-t",
        help="Document title"
    ),
    author: Optional[str] = typer.Option(
        None, "--author", "-a",
        help="Document author"
    ),
    subject: Optional[str] = typer.Option(
        None, "--subject", "-s",
        help="Document subject"
    ),
    pdf_engine: str = typer.Option(
        "weasyprint", "--pdf-engine",
        help="PDF engine (weasyprint, reportlab, pandoc)"
    ),
    no_css: bool = typer.Option(
        False, "--no-css",
        help="Disable CSS styling (HTML only)"
    ),
    no_standalone: bool = typer.Option(
        False, "--no-standalone",
        help="Don't create standalone document (HTML only)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Verbose output"
    )
):
    """
    Convert a markdown document to the specified format.
    
    Examples:
        mdproc convert -i document.md -f pdf
        mdproc convert -c "# Hello World" -f html -o hello
        mdproc convert -i README.md -f docx --title "My Document"
    """
    # Validate inputs
    if not content and not input_file:
        console.print("[red]Error: Either --input or --content must be provided[/red]")
        raise typer.Exit(1)
    
    if content and input_file:
        console.print("[red]Error: Cannot specify both --input and --content[/red]")
        raise typer.Exit(1)
    
    # Read content from file if needed
    if input_file:
        if not input_file.exists():
            console.print(f"[red]Error: Input file not found: {input_file}[/red]")
            raise typer.Exit(1)
        
        try:
            content = input_file.read_text(encoding='utf-8')
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            raise typer.Exit(1)
    
    # Initialize service and use case
    service = get_service()
    use_case = ConvertDocumentUseCase(service)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"Converting to {output_format.upper()}...", total=None)
        
        # Execute conversion
        response = use_case.execute(
            content=content,
            input_file=str(input_file) if input_file else None,
            output_format=output_format,
            output_file=output_file,
            output_directory=str(output_dir) if output_dir else None,
            title=title,
            author=author,
            subject=subject,
            pdf_engine=pdf_engine,
            include_css=not no_css,
            standalone=not no_standalone
        )
    
    # Display results
    if response.success:
        console.print(f"[green]✅ Conversion successful![/green]")
        
        if response.output_file:
            console.print(f"📁 Output file: [blue]{response.output_file}[/blue]")
        
        if verbose and response.file_size:
            console.print(f"📊 File size: {response.file_size:,} bytes")
        
        if verbose and response.conversion_time:
            console.print(f"⏱️  Conversion time: {response.conversion_time:.3f} seconds")
        
        if verbose and response.engine_used:
            console.print(f"🔧 Engine: {response.engine_used}")
        
    else:
        console.print(f"[red]❌ Conversion failed: {response.error_message}[/red]")
        raise typer.Exit(1)


@app.command()
def formats():
    """List all available output formats and converters."""
    service = get_service()
    use_case = ListConvertersUseCase(service)
    
    conversions = use_case.execute()
    
    console.print(Panel.fit("📋 Available Formats", style="blue"))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Source Format", style="cyan")
    table.add_column("Target Formats", style="green")
    
    for source, targets in conversions.items():
        table.add_row(source.upper(), ", ".join(t.upper() for t in targets))
    
    console.print(table)
    
    # Show format details
    console.print("\n[bold]Format Details:[/bold]")
    format_info = {
        "PDF": "Portable Document Format - High quality, printable documents",
        "HTML": "HyperText Markup Language - Web-ready documents with styling",
        "DOCX": "Microsoft Word Document - Editable Word documents",
        "TXT": "Plain Text - Simple, readable text files"
    }
    
    for fmt, description in format_info.items():
        console.print(f"  [cyan]{fmt}[/cyan]: {description}")


@app.command()
def validate(
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i",
        help="Input markdown file to validate"
    ),
    content: Optional[str] = typer.Option(
        None, "--content", "-c",
        help="Markdown content to validate"
    )
):
    """
    Validate markdown input before conversion.
    
    Examples:
        mdproc validate -i document.md
        mdproc validate -c "# Hello World"
    """
    if not content and not input_file:
        console.print("[red]Error: Either --input or --content must be provided[/red]")
        raise typer.Exit(1)
    
    service = get_service()
    use_case = ValidateInputUseCase(service)
    
    result = use_case.execute(
        content=content,
        input_file=str(input_file) if input_file else None
    )
    
    if result["valid"]:
        console.print("[green]✅ Input is valid![/green]")
    else:
        console.print("[red]❌ Input validation failed[/red]")
        for error in result["errors"]:
            console.print(f"  [red]Error: {error}[/red]")
    
    # Show warnings
    for warning in result["warnings"]:
        console.print(f"  [yellow]Warning: {warning}[/yellow]")
    
    # Show info
    if result["info"]:
        console.print("\n[bold]Document Information:[/bold]")
        info = result["info"]
        
        if "word_count" in info:
            console.print(f"  📝 Words: {info['word_count']}")
        if "character_count" in info:
            console.print(f"  📄 Characters: {info['character_count']}")
        if "line_count" in info:
            console.print(f"  📏 Lines: {info['line_count']}")
        if "file_size" in info:
            console.print(f"  📊 File size: {info['file_size']} bytes")
        if "markdown_features" in info and info["markdown_features"]:
            console.print(f"  🎨 Features: {', '.join(info['markdown_features'])}")
    
    if not result["valid"]:
        raise typer.Exit(1)


@app.command()
def example():
    """Show usage examples."""
    examples = [
        ("Convert file to PDF", "mdproc convert -i document.md -f pdf"),
        ("Convert with custom title", "mdproc convert -i README.md -f pdf --title 'My Document'"),
        ("Convert string to HTML", "mdproc convert -c '# Hello World' -f html -o hello"),
        ("Convert to Word document", "mdproc convert -i notes.md -f docx --author 'John Doe'"),
        ("Convert to plain text", "mdproc convert -i article.md -f txt"),
        ("Use ReportLab for PDF", "mdproc convert -i doc.md -f pdf --pdf-engine reportlab"),
        ("Validate before converting", "mdproc validate -i document.md"),
        ("List available formats", "mdproc formats"),
    ]
    
    console.print(Panel.fit("📚 Usage Examples", style="blue"))
    
    for description, command in examples:
        console.print(f"\n[bold cyan]{description}:[/bold cyan]")
        syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
        console.print(syntax)


def version_callback(value: bool):
    """Handle version flag."""
    if value:
        console.print("Markdown Processor CLI v1.0.0")
        console.print("Built with hexagonal architecture")
        
        # Show Docker info if running in container
        if is_running_in_docker():
            console.print("🐳 Running in Docker container")
            console.print("Registry: dawsonlp/mdproc")
        
        raise typer.Exit()


def is_running_in_docker() -> bool:
    """Check if we're running inside a Docker container."""
    try:
        # Check for .dockerenv file
        if Path("/.dockerenv").exists():
            return True
        
        # Check cgroup for docker
        with open("/proc/1/cgroup", "r") as f:
            return "docker" in f.read()
    except:
        return False


def show_docker_help():
    """Show Docker-specific help and usage examples."""
    console.print(Panel.fit("🐳 mdproc Docker Container", style="blue"))
    
    console.print("\n[bold]Quick Start:[/bold]")
    console.print("# Recommended alias (like compiler containers)")
    console.print("[cyan]alias mdproc='docker run --rm -v $(pwd):/workspace dawsonlp/mdproc'[/cyan]")
    console.print("\n# Use like a local CLI")
    console.print("[cyan]mdproc convert -i document.md -f pdf[/cyan]")
    console.print("[cyan]mdproc formats[/cyan]")
    console.print("[cyan]mdproc --version[/cyan]")
    
    console.print("\n[bold]Direct Usage:[/bold]")
    console.print("[cyan]docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i doc.md -f pdf[/cyan]")
    
    console.print("\n[bold]Volume Mounting:[/bold]")
    console.print("Mount your current directory to access files:")
    console.print("[cyan]-v $(pwd):/workspace[/cyan]")
    console.print("This allows mdproc to read your markdown files and write output files.")
    
    console.print("\n[bold]Volume Convention:[/bold]")
    console.print("  [yellow]/workspace[/yellow] - Mount your project directory here")
    
    console.print("\n[bold]Examples:[/bold]")
    examples = [
        "docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i README.md -f pdf",
        "docker run --rm -v $(pwd):/workspace dawsonlp/mdproc convert -i doc.md -f html",
        "docker run --rm dawsonlp/mdproc formats",
        "docker run --rm dawsonlp/mdproc --version"
    ]
    
    for example in examples:
        console.print(f"  [cyan]{example}[/cyan]")
    
    console.print("\n[bold]For more help:[/bold] docker run --rm dawsonlp/mdproc convert --help")


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version information"
    )
):
    """
    Markdown Processor CLI - Convert markdown to PDF, HTML, DOCX, and TXT.
    
    A clean, fast, and reliable document conversion tool built with
    hexagonal architecture principles.
    """
    pass


if __name__ == "__main__":
    app()
