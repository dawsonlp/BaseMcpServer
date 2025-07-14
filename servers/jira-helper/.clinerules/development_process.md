# Jira Helper Development Process

## Project Structure & Sources Root

### **Critical: `src/` is a Sources Root Directory**
- The `src/` directory is configured as a sources root in this project
- Python imports work directly from module names without `src.` prefix
- Example: `from domain.models import IssueLink` (NOT `from src.domain.models import IssueLink`)

### **Correct Command Execution**
```bash
# Run tests (from project root)
cd servers/jira-helper
PYTHONPATH=src python -m pytest src/tests/ -v

# Run the server
cd servers/jira-helper
PYTHONPATH=src python src/main.py

# Install dependencies
cd servers/jira-helper
pip install -r requirements.txt
```

### **Directory Structure**
```
servers/jira-helper/
├── src/                    # Sources root - all imports start here
│   ├── domain/            # Domain layer (framework-agnostic)
│   ├── application/       # Application layer (use cases)
│   ├── infrastructure/    # Infrastructure layer (external adapters)
│   ├── adapters/          # Adapter layer (MCP integration)
│   └── tests/             # Test files
├── requirements.txt
├── pytest.ini
└── README.md
```

## Testing Conventions

### **Test Organization**
- Tests are located in `src/tests/`
- Test files follow naming: `test_*.py`
- Separate unit tests from integration tests
- Use descriptive test class and method names

### **Test Execution**
```bash
# Run all tests
PYTHONPATH=src python -m pytest src/tests/ -v

# Run specific test file
PYTHONPATH=src python -m pytest src/tests/test_issue_link_model.py -v

# Run with coverage
PYTHONPATH=src python -m pytest src/tests/ --cov=src --cov-report=html
```

### **Test Dependencies**
- Use `pytest` for test framework
- Use `pytest-asyncio` for async tests
- Use `unittest.mock` for mocking
- Mock external dependencies (Jira API, etc.)

## Architecture Patterns

### **Hexagonal Architecture Layers**
1. **Domain Layer** (`src/domain/`)
   - Framework-agnostic business logic
   - Models, exceptions, ports (interfaces)
   - No external dependencies

2. **Application Layer** (`src/application/`)
   - Use cases orchestrating domain logic
   - Depends only on domain layer
   - Handles application-specific workflows

3. **Infrastructure Layer** (`src/infrastructure/`)
   - External system adapters (Jira API, config, etc.)
   - Implements domain ports
   - Framework-specific code

4. **Adapter Layer** (`src/adapters/`)
   - MCP server integration
   - Translates between MCP and use cases
   - Entry point for external requests

### **Import Patterns**
```python
# Domain layer - no external imports
from domain.models import IssueLink
from domain.exceptions import InvalidLinkTypeError

# Application layer - domain only
from domain.services import IssueLinkService
from application.use_cases import CreateIssueLinkUseCase

# Infrastructure layer - domain + external
from domain.ports import IssueLinkPort
from infrastructure.jira_client import JiraIssueLinkAdapter

# Adapter layer - all layers
from application.use_cases import CreateIssueLinkUseCase
from adapters.mcp_adapter import mcp
```

## Development Workflow

### **Before Making Changes**
1. Ensure you're in the correct directory: `servers/jira-helper`
2. Activate virtual environment if using one
3. Set PYTHONPATH when running commands: `PYTHONPATH=src`

### **Running the Application**
```bash
cd servers/jira-helper
PYTHONPATH=src python src/main.py
```

### **Testing Changes**
```bash
cd servers/jira-helper
PYTHONPATH=src python -m pytest src/tests/ -v
```

### **Adding New Features**
1. Start with domain models and exceptions
2. Define ports (interfaces) in domain layer
3. Implement use cases in application layer
4. Create infrastructure adapters
5. Add MCP tools in adapter layer
6. Write comprehensive tests

## Common Pitfalls to Avoid

### **Import Errors**
- ❌ `from src.domain.models import IssueLink`
- ✅ `from domain.models import IssueLink`

### **Wrong Directory**
- ❌ Running commands from `/Users/ldawson/repos/BaseMcpServer`
- ✅ Running commands from `servers/jira-helper`

### **Missing PYTHONPATH**
- ❌ `python -m pytest src/tests/`
- ✅ `PYTHONPATH=src python -m pytest src/tests/`

### **Layer Violations**
- ❌ Domain importing from infrastructure
- ❌ Application importing from adapters
- ✅ Dependencies point inward toward domain

## Configuration Files

### **pytest.ini**
- Configured for async testing
- Sets up test discovery patterns
- May include PYTHONPATH configuration

### **requirements.txt**
- All Python dependencies
- Pin versions for reproducibility
- Separate dev dependencies if needed

## Debugging Tips

### **Import Issues**
1. Check current working directory
2. Verify PYTHONPATH includes `src`
3. Ensure no circular imports
4. Check for typos in module names

### **Test Issues**
1. Verify test file naming (`test_*.py`)
2. Check async test decorators (`@pytest.mark.asyncio`)
3. Ensure proper mocking of external dependencies
4. Validate test isolation (no shared state)

## MCP Server Specifics

### **Server Entry Point**
- Main server file: `src/main.py`
- MCP adapter: `src/adapters/mcp_adapter.py`
- Configuration: `config.yaml`

### **Tool Development**
1. Implement use case in application layer
2. Add tool in MCP adapter
3. Handle errors gracefully
4. Provide clear documentation

This documentation should be referenced whenever working on the Jira Helper project to ensure consistent development practices and avoid common issues.
