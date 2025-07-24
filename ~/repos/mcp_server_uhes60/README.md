# UHES60 MCP Server

A demonstration MCP (Model Context Protocol) server built with hexagonal architecture, showcasing tools, prompts, and resources. This server provides personalized greeting functionality and serves as a complete example of how to build production-ready MCP servers.

## Features

- **Tool**: `say_hello` - Generate personalized greetings with different styles (formal, casual, enthusiastic)
- **Prompt**: `greeting_template` - Get greeting templates for different occasions
- **Resource**: `greetings.txt` - Access greeting examples and tips

## Architecture

This server follows **Hexagonal Architecture** (Ports and Adapters) with **Domain-Driven Design** patterns:

- **Domain Layer**: Core business logic (greeting services, models)
- **Application Layer**: Use cases and validation
- **Infrastructure Layer**: File system and configuration adapters
- **Adapter Layer**: MCP protocol implementation

## Installation

### Prerequisites

- Python 3.11 or higher
- [mcp-manager](https://github.com/dawsonlp/BaseMcpServer/tree/main/utils/mcp_manager) installed

### Install with mcp-manager

1. **Install the server**:
   ```bash
   mcp-manager install local uhes60 --source ~/repos/mcp_server_uhes60 --pipx --force
   ```

2. **Configure for Cline/VSCode**:
   ```bash
   mcp-manager configure vscode
   ```

3. **Verify installation**:
   ```bash
   mcp-manager list
   ```

### Manual Installation (Alternative)

If you prefer to install manually:

1. **Clone or download this repository**
2. **Install dependencies**:
   ```bash
   cd ~/repos/mcp_server_uhes60
   pip install -r requirements.txt
   ```
3. **Test the server**:
   ```bash
   python src/main.py
   ```

## Usage

Once installed and configured, you can use the server in Cline:

### Tool Usage
```
Use the say_hello tool with name "Alice" and style "enthusiastic"
```

### Prompt Usage
```
Use the greeting_template prompt for a "birthday" occasion with "formal" style
```

### Resource Access
```
Show me the greetings.txt resource
```

## Configuration

The server supports optional configuration via `config.yaml`:

```yaml
# Server settings
name: "uhes60-mcp"
version: "1.0.0"

# Resource settings
greetings_file: "greetings.txt"

# Default greeting style (formal, casual, enthusiastic)
default_style: "casual"
```

## Development

### Project Structure

```
mcp_server_uhes60/
├── README.md                   # This file
├── pyproject.toml             # Package configuration
├── requirements.txt           # Dependencies
├── config.yaml.example       # Configuration template
├── src/                       # Source code
│   ├── main.py               # Entry point
│   ├── domain/               # Business logic
│   │   ├── models.py         # Domain models
│   │   ├── services.py       # Business services
│   │   └── results.py        # Result types
│   ├── application/          # Use cases
│   │   ├── use_cases.py      # Application logic
│   │   └── validation.py     # Input validation
│   ├── infrastructure/       # External services
│   │   ├── file_adapter.py   # File operations
│   │   └── config_adapter.py # Configuration
│   └── adapters/             # Framework adapters
│       └── mcp_adapter.py    # MCP protocol
├── resources/                # Static resources
│   └── greetings.txt         # Greeting examples
└── tests/                    # Test files
    └── test_domain.py        # Domain tests
```

### Running Tests

```bash
cd ~/repos/mcp_server_uhes60
python -m pytest tests/
```

### Development Mode

For development, you can run the server directly:

```bash
cd ~/repos/mcp_server_uhes60
python src/main.py
```

## API Reference

### Tools

#### `say_hello`
Generate a personalized greeting for someone.

**Parameters:**
- `name` (string, required): The name of the person to greet
- `style` (string, optional): The style of greeting ("formal", "casual", "enthusiastic"). Default: "casual"

**Returns:**
```json
{
  "greeting": "Hey Alice! How's it going?",
  "recipient": "Alice",
  "style": "casual",
  "success": true
}
```

### Prompts

#### `greeting_template`
Generate greeting templates for different occasions.

**Parameters:**
- `occasion` (string, optional): The occasion for the greeting. Default: "general"
- `style` (string, optional): The style of greeting. Default: "casual"

### Resources

#### `file://greetings.txt`
A collection of greeting examples in different styles with tips for usage.

## Troubleshooting

### Server Won't Start
1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Verify Python version: `python --version` (should be 3.11+)
3. Check mcp-manager installation: `mcp-manager --version`

### Tool Not Found
1. Ensure server is installed: `mcp-manager list`
2. Reconfigure Cline: `mcp-manager configure vscode`
3. Restart VSCode/Cline

### Import Errors
This server uses absolute imports only. If you see import errors, ensure you're running from the correct directory and all dependencies are installed.

## Contributing

This server serves as a reference implementation. To extend it:

1. **Add new tools**: Create use cases in `application/use_cases.py`
2. **Add business logic**: Extend services in `domain/services.py`
3. **Add external integrations**: Create adapters in `infrastructure/`
4. **Add tests**: Create test files in `tests/`

## License

This project is part of the BaseMcpServer repository and follows the same license terms.

## Related

- [BaseMcpServer](https://github.com/dawsonlp/BaseMcpServer) - The main repository
- [MCP Setup Guide](https://github.com/dawsonlp/BaseMcpServer/blob/main/docs/BUILD_A_NEW_MCP.md) - Complete guide for building MCP servers
- [mcp-manager](https://github.com/dawsonlp/BaseMcpServer/tree/main/utils/mcp_manager) - MCP server management tool
