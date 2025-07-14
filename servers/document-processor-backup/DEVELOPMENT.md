# Document Processor MCP Server - Development Guide

## 🚧 Current Status (macOS → Ubuntu Handoff)

### What's Been Built ✅
- **Complete hexagonal architecture** with Domain, Application, Infrastructure layers
- **Docker containerization** with Ubuntu 25.04 + Python 3.13
- **All document processing dependencies** installed in Docker
- **Core conversion logic** tested and working (markdown → HTML verified)
- **MCP protocol integration** framework in place
- **Cline configuration** updated for HTTP-based MCP server

### What's Broken ❌
- **FastMCP server registration** - AttributeError on `_tools` attribute
- **Server startup** - crashes immediately due to architecture mismatch
- **MCP protocol** - not accessible due to startup failure

### The Core Issue
```python
# In servers/document-processor/src/server.py line 96:
for tool_name, tool_func in server._tools.items():  # ❌ _tools doesn't exist
    srv._tools[tool_name] = tool_func                # ❌ _tools doesn't exist

# Error:
AttributeError: 'FastMCP' object has no attribute '_tools'. Did you mean: 'tool'?
```

## 🐧 Ubuntu 25.04 Development Setup

### 1. System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install document processing tools
sudo apt install -y \
    pandoc \
    texlive-full \
    texlive-xetex \
    texlive-luatex \
    wkhtmltopdf \
    libreoffice \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    python3-pip \
    build-essential \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info

# Install additional fonts for better PDF rendering
sudo apt install -y \
    fonts-liberation \
    fonts-dejavu \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji
```

### 2. Python Environment Setup
```bash
# Navigate to project
cd servers/document-processor

# Create Python virtual environment
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Verify installations
pandoc --version
python --version
pip list | grep mcp
```

### 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env
```

## 🏗️ Architecture Overview

### Directory Structure
```
src/
├── domain/              # Business logic (pure Python)
│   ├── models.py       # Data models and enums
│   └── ports.py        # Abstract interfaces
├── application/         # Use cases and orchestration
│   └── use_cases.py    # Business workflows
├── infrastructure/      # External dependencies
│   ├── converters.py   # Document conversion implementations
│   ├── storage.py      # File system operations
│   ├── templates.py    # Jinja2 template rendering
│   └── config.py       # Configuration provider
├── adapters/           # MCP protocol integration
│   └── mcp_adapter.py  # FastMCP tool registration
├── config.py           # Settings and environment variables
├── server.py           # Server factory and wiring
└── main.py             # Entry point and CLI
```

### Key Components
- **Domain Layer**: Pure business logic, no external dependencies
- **Application Layer**: Use cases that orchestrate domain objects
- **Infrastructure Layer**: Concrete implementations (Pandoc, WeasyPrint, etc.)
- **Adapter Layer**: MCP protocol integration

## 🐛 Known Issues & Fixes

### Issue 1: FastMCP Tool Registration
**Problem**: Trying to access private `_tools` attribute that doesn't exist.

**Current Code** (broken):
```python
# server.py lines 96-99
for tool_name, tool_func in server._tools.items():
    srv._tools[tool_name] = tool_func
```

**Solution Options**:

**Option A**: Direct tool registration (recommended)
```python
# Replace register_tools_and_resources function with direct registration
def register_tools_and_resources(srv: FastMCP):
    # Create components
    config_provider = SettingsConfigurationProvider()
    file_storage = LocalFileStorage()
    template_renderer = Jinja2TemplateRenderer(config_provider.get_template_directory())
    document_converter = MarkdownConverter(template_renderer)
    
    # Create use cases
    convert_use_case = ConvertDocumentUseCase(...)
    
    # Register tools directly
    @srv.tool()
    def convert_markdown_to_html(markdown_text: str, filename: str = None, template_name: str = None) -> str:
        # Implementation using convert_use_case
        pass
```

**Option B**: Fix main.py to use create_document_processor_server directly
```python
# In main.py start_server function:
from server import create_document_processor_server
mcp_server = create_document_processor_server()  # Already has tools registered
```

### Issue 2: MCP Adapter Implementation
The `MCPDocumentProcessorAdapter` needs to properly register tools with FastMCP.

**Check**: `src/adapters/mcp_adapter.py` - verify the `register_tools` method uses correct FastMCP API.

## 🧪 Development Workflow

### Step 1: Fix Server Registration
```bash
# Test basic server startup
cd src
python main.py --help

# Try to start server (will likely fail initially)
python main.py streamable-http
```

### Step 2: Debug Import Issues
```bash
# Test individual components
python -c "from domain.models import DocumentFormat; print('Domain OK')"
python -c "from infrastructure.converters import MarkdownConverter; print('Infrastructure OK')"
python -c "from application.use_cases import ConvertDocumentUseCase; print('Application OK')"
```

### Step 3: Test Document Conversion
```bash
# Run the standalone test
python ../test_conversion.py
```

### Step 4: Test MCP Server
```bash
# Start server
python main.py streamable-http

# In another terminal, test HTTP endpoint
curl -X POST http://localhost:7502/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer doc_processor_api_key" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## 🔧 Quick Fixes to Try

### Fix 1: Simplify main.py
Replace the complex registration with direct server creation:

```python
# In main.py start_server function, replace:
mcp_server = FastMCP(settings.server_name)
register_tools_and_resources(mcp_server)

# With:
from server import create_document_processor_server
mcp_server = create_document_processor_server()
```

### Fix 2: Check MCP Adapter
Verify `src/adapters/mcp_adapter.py` uses correct FastMCP tool registration:

```python
def register_tools(self, mcp_server: FastMCP):
    @mcp_server.tool()  # ✅ Correct way
    def convert_markdown_to_html(...):
        pass
```

### Fix 3: Verify Dependencies
```bash
# Check if all required packages are installed
pip install mcp fastmcp markdown weasyprint python-docx reportlab jinja2 aiofiles pydantic-settings
```

## 📋 Testing Checklist

### Local Development Tests
- [ ] Server starts without errors
- [ ] Basic imports work
- [ ] Document conversion works (test_conversion.py)
- [ ] MCP tools are registered
- [ ] HTTP endpoint responds
- [ ] Tools can be called via MCP protocol

### Integration Tests
- [ ] Markdown → HTML conversion
- [ ] Markdown → PDF conversion (multiple engines)
- [ ] Markdown → DOCX conversion
- [ ] Markdown → Text conversion
- [ ] Template rendering works
- [ ] File output and retrieval

### MCP Protocol Tests
- [ ] `tools/list` returns available tools
- [ ] `tools/call` executes conversions
- [ ] Error handling works properly
- [ ] Authentication with API key

## 🎯 Success Criteria

1. **Server starts successfully** on `python main.py streamable-http`
2. **MCP tools are accessible** via HTTP API
3. **Document conversion works** for all formats
4. **Can integrate with Cline** via HTTP transport
5. **All tests pass** including the existing test_conversion.py

## 📝 Next Steps Priority

1. **Fix server startup** - get basic MCP server running
2. **Test document conversion** - verify core functionality
3. **Debug MCP integration** - ensure tools are properly registered
4. **Test with Cline** - verify end-to-end integration
5. **Optimize and containerize** - back to Docker once working

## 🔗 Reference Files

- **Main entry point**: `src/main.py`
- **Server factory**: `src/server.py` 
- **MCP adapter**: `src/adapters/mcp_adapter.py`
- **Test script**: `test_conversion.py`
- **Requirements**: `requirements.txt`
- **Configuration**: `src/config.py`

## 💡 Alternative Approach

If the hexagonal architecture proves too complex, consider simplifying to match the pattern used in `jira-helper` or `mcpservercreator` servers - direct tool registration without the complex adapter layer.

---

**Ready to continue development on Ubuntu 25.04!** 🚀

The foundation is solid, just need to fix the FastMCP integration issues.
