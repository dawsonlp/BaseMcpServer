# Document Processor MCP Server - Setup Complete

## ✅ Registration Complete

The Document Processor MCP Server has been successfully registered with Cline and is ready to use!

## Configuration

**Cline MCP Settings:**
```json
"document-processor": {
  "url": "http://localhost:3000/mcp",
  "apiKey": "doc_processor_api_key",
  "disabled": false,
  "autoApprove": []
}
```

## How to Use

### 1. Start the Docker Container
```bash
cd servers/document-processor
docker run -d --name document-processor \
  -p 3000:3000 \
  -v $(pwd)/test_output:/app/output \
  document-processor:latest \
  python3.13 /app/src/server.py streamable-http
```

### 2. Restart VS Code
Restart VS Code for Cline to pick up the new MCP server configuration.

### 3. Available Tools in Cline
Once connected, you'll have access to these document processing tools:

- **convert_markdown_to_html** - Convert markdown to styled HTML
- **convert_markdown_to_pdf** - Convert markdown to PDF (multiple engines)
- **convert_markdown_to_docx** - Convert markdown to Word document
- **convert_markdown_to_text** - Convert markdown to plain text
- **list_output_files** - List all generated files
- **get_server_info** - Get server configuration

### 4. Example Usage
```
convert_markdown_to_html(
  markdown_text="# My Document\n\nThis is **bold** text.",
  filename="my_doc",
  template="professional.html"
)
```

## Architecture
- **Clean Hexagonal Architecture** with Domain, Application, Infrastructure layers
- **Docker-based** with all dependencies (Pandoc, TeXLive, WeasyPrint, etc.)
- **HTTP Transport** using FastMCP and streamable-http
- **Multiple PDF Engines** (WeasyPrint, Pandoc, ReportLab, pdfkit)
- **Template Support** with Jinja2 for professional document formatting

## Files Generated
All converted documents are saved to the mounted output directory and can be accessed both from within the container and on the host system.

The Document Processor MCP Server is now fully operational and integrated with Cline! 🎉
