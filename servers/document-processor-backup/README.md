# Document Processor MCP Server

A Model Context Protocol (MCP) server that converts markdown text to various document formats including PDF, HTML, Microsoft Word, and plain text. Designed to run in Docker containers with mounted volumes for file input/output.

## Features

- **Multiple Output Formats**: Convert markdown to PDF, HTML, DOCX, and plain text
- **Multiple PDF Engines**: Support for WeasyPrint, pdfkit, ReportLab, and Pandoc
- **HTML Templates**: Customizable Jinja2 templates for HTML output
- **Docker Ready**: Ubuntu-based container with all document processing tools
- **Volume Mounting**: Easy file access through mounted directories
- **MCP Protocol**: Full compliance with Model Context Protocol v1.10.1+

## Quick Start

### Docker (Recommended)

1. **Build the image**:
   ```bash
   cd servers/document-processor
   docker build -f docker/Dockerfile -t document-processor .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name document-processor \
     -p 7502:7502 \
     -v $(pwd)/output:/app/output \
     -v $(pwd)/input:/app/input \
     -v $(pwd)/templates:/app/templates \
     document-processor
   ```

3. **Test the server**:
   ```bash
   curl -X POST http://localhost:7502/tools/convert_markdown_to_pdf \
     -H "Content-Type: application/json" \
     -d '{"markdown_text": "# Hello World\n\nThis is a test document."}'
   ```

### Local Development

1. **Setup environment**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Run locally**:
   ```bash
   source venv/bin/activate
   cd src
   python main.py streamable-http
   ```

## Available Tools

### convert_markdown_to_pdf
Convert markdown text to PDF format.

**Parameters:**
- `markdown_text` (string, required): The markdown content to convert
- `filename` (string, optional): Output filename without extension
- `engine` (string, optional): PDF engine (weasyprint, pdfkit, reportlab, pandoc)
- `template` (string, optional): HTML template name for styling

### convert_markdown_to_html
Convert markdown text to HTML format.

**Parameters:**
- `markdown_text` (string, required): The markdown content to convert
- `filename` (string, optional): Output filename without extension
- `template` (string, optional): Template name for styling

### convert_markdown_to_docx
Convert markdown text to Microsoft Word document.

**Parameters:**
- `markdown_text` (string, required): The markdown content to convert
- `filename` (string, optional): Output filename without extension

### convert_markdown_to_text
Convert markdown text to plain text.

**Parameters:**
- `markdown_text` (string, required): The markdown content to convert
- `filename` (string, optional): Output filename without extension

### list_output_files
List all files in the output directory with details.

### get_server_info
Get server configuration and capabilities.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_NAME` | document-processor | MCP server name |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 7502 | Server port |
| `API_KEY` | doc_processor_api_key | API key for authentication |
| `OUTPUT_DIRECTORY` | /app/output | Output files directory |
| `INPUT_DIRECTORY` | /app/input | Input files directory |
| `HTML_TEMPLATE_DIR` | /app/templates | HTML templates directory |
| `PDF_ENGINE` | weasyprint | Default PDF engine |
| `MAX_FILE_SIZE_MB` | 50 | Maximum file size limit |

### Custom Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## HTML Templates

Templates use Jinja2 syntax with markdown content available as `{{ content }}`.

### Built-in Templates
- **professional.html**: Formal document styling with header/footer
- **simple.html**: Clean, minimal styling

### Custom Templates
Create your own templates in the templates directory:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Custom Template</title>
    <style>
        body { font-family: Arial, sans-serif; }
        h1 { color: #2c3e50; }
    </style>
</head>
<body>
    {{ content }}
</body>
</html>
```

## MCP Client Integration

### Claude Desktop
Add to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "document-processor": {
      "url": "http://localhost:7502/mcp",
      "apiKey": "doc_processor_api_key",
      "disabled": false
    }
  }
}
```

### Cline (VS Code)
Add to Cline MCP settings:

```json
{
  "mcpServers": {
    "document-processor": {
      "url": "http://localhost:7502/mcp",
      "apiKey": "doc_processor_api_key",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Docker Commands Reference

### Build multi-architecture image
```bash
# Use the provided build script for multi-arch builds
chmod +x docker/build.sh
./docker/build.sh
```

### Run with custom port
```bash
docker run -d \
  --name document-processor \
  -p 8080:7502 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/templates:/app/templates \
  document-processor
```

### Run with custom environment
```bash
docker run -d \
  --name document-processor \
  -p 7502:7502 \
  -e PDF_ENGINE=pandoc \
  -e MAX_FILE_SIZE_MB=100 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/templates:/app/templates \
  document-processor
```

### View logs
```bash
docker logs -f document-processor
```

### Stop and remove
```bash
docker stop document-processor
docker rm document-processor
```

## Supported Formats

| Format | Engine Options | Features |
|--------|---------------|----------|
| PDF | WeasyPrint (default) | Best CSS support, modern HTML to PDF |
| PDF | pdfkit | Requires wkhtmltopdf, good for complex layouts |
| PDF | ReportLab | Basic PDF generation, lightweight |
| PDF | Pandoc | Universal converter, requires pandoc |
| HTML | Built-in | Markdown to HTML with optional templates |
| DOCX | python-docx | Microsoft Word document format |
| TXT | html2text | Clean plain text conversion |

## Project Structure

```
servers/document-processor/
├── src/
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── server.py        # MCP tools and resources
│   └── config.py        # Configuration management
├── docker/
│   ├── Dockerfile       # Container definition
│   ├── build.sh         # Multi-arch build script
│   └── templates/       # Default HTML templates
├── requirements.txt     # Python dependencies
├── .env.example        # Environment configuration
├── setup.sh            # Local development setup
└── README.md           # This file
```

## Troubleshooting

### Common Issues
1. **WeasyPrint fails**: Use different PDF engine (`-e PDF_ENGINE=reportlab`)
2. **Permission errors**: Check volume mount permissions
3. **Large files**: Increase `MAX_FILE_SIZE_MB` setting
4. **Template not found**: Ensure template exists in templates directory

### System Requirements
- **Docker**: For containerized deployment
- **Python 3.13+**: For local development
- **System packages**: Installed automatically in Docker

## Security
- API key authentication for MCP connections
- Non-root user in Docker container
- File size limits to prevent abuse
- Input validation for all parameters

## License
This project follows the same license as the parent MCP server project.
