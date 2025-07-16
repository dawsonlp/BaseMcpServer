# Extension Guide for Jira Helper MCP Server

This document describes how to extend the Jira Helper server with new adapters, use cases, and functionality while maintaining the hexagonal architecture principles.

## 🏗️ Architecture Extension Points

The hexagonal architecture provides clear extension points at each layer:

```
┌─────────────────────────────────────────────────────────────┐
│                 NEW ADAPTERS                                │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   CLI Adapter   │  │  REST Adapter   │  ← Extension     │
│  │   (Future)      │  │   (Future)      │    Points        │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               APPLICATION LAYER                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  NEW USE CASES  │  │ NEW SERVICES    │  ← Extension     │
│  │                 │  │                 │    Points        │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 DOMAIN LAYER                                │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  NEW MODELS     │  │ NEW SERVICES    │  ← Extension     │
│  │                 │  │                 │    Points        │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              INFRASTRUCTURE LAYER                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ NEW REPOSITORIES│  │ NEW ADAPTERS    │  ← Extension     │
│  │                 │  │                 │    Points        │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 🔌 Adding New Adapters

### 1. CLI Adapter Example

Create a new CLI adapter that uses the same use cases as the MCP adapter:

```python
# src/adapters/cli_adapter.py
import click
from application.simplified_use_cases import ListProjectsUseCase, GetIssueDetailsUseCase
from application.services import JiraApplicationService
from application.base_use_case import UseCaseFactory

class CliAdapter:
    def __init__(self, use_case_factory: UseCaseFactory):
        self.factory = use_case_factory
    
    @click.group()
    def cli(self):
        """Jira Helper CLI."""
        pass
    
    @cli.command()
    @click.option('--instance', default=None, help='Jira instance name')
    def list_projects(self, instance):
        """List all Jira projects."""
        use_case = self.factory.create_use_case(ListProjectsUseCase)
        result = asyncio.run(use_case.execute(instance))
        
        if result.success:
            for project in result.data['projects']:
                click.echo(f"{project['key']}: {project['name']}")
        else:
            click.echo(f"Error: {result.error}", err=True)
    
    @cli.command()
    @click.argument('issue_key')
    @click.option('--instance', default=None, help='Jira instance name')
    def get_issue(self, issue_key, instance):
        """Get issue details."""
        use_case = self.factory.create_use_case(GetIssueDetailsUseCase)
        result = asyncio.run(use_case.execute(issue_key, instance))
        
        if result.success:
            issue = result.data['issue']
            click.echo(f"Key: {issue['key']}")
            click.echo(f"Summary: {issue['summary']}")
            click.echo(f"Status: {issue['status']}")
        else:
            click.echo(f"Error: {result.error}", err=True)

# Usage
if __name__ == '__main__':
    # Setup dependencies (same as MCP adapter)
    factory = create_use_case_factory()
    adapter = CliAdapter(factory)
    adapter.cli()
```

### 2. REST API Adapter Example

Create a REST API using FastAPI:

```python
# src/adapters/rest_adapter.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from application.simplified_use_cases import *
from application.base_use_case import UseCaseFactory

app = FastAPI(title="Jira Helper API")

class RestAdapter:
    def __init__(self, use_case_factory: UseCaseFactory):
        self.factory = use_case_factory
        self.setup_routes()
    
    def setup_routes(self):
        @app.get("/projects")
        async def list_projects(instance: str = None):
            """List all Jira projects."""
            use_case = self.factory.create_use_case(ListProjectsUseCase)
            result = await use_case.execute(instance)
            
            if result.success:
                return result.data
            else:
                raise HTTPException(status_code=500, detail=result.error)
        
        @app.get("/issues/{issue_key}")
        async def get_issue(issue_key: str, instance: str = None):
            """Get issue details."""
            use_case = self.factory.create_use_case(GetIssueDetailsUseCase)
            result = await use_case.execute(issue_key, instance)
            
            if result.success:
                return result.data
            else:
                raise HTTPException(status_code=500, detail=result.error)
        
        @app.post("/issues")
        async def create_issue(request: CreateIssueRequest):
            """Create a new issue."""
            use_case = self.factory.create_use_case(CreateIssueUseCase)
            result = await use_case.execute(
                project_key=request.project_key,
                summary=request.summary,
                description=request.description,
                issue_type=request.issue_type,
                priority=request.priority,
                assignee=request.assignee,
                labels=request.labels,
                instance_name=request.instance_name
            )
            
            if result.success:
                return result.data
            else:
                raise HTTPException(status_code=500, detail=result.error)

# Request models
class CreateIssueRequest(BaseModel):
    project_key: str
    summary: str
    description: str
    issue_type: str = "Story"
    priority: str = None
    assignee: str = None
    labels: list[str] = None
    instance_name: str = None

# Usage
if __name__ == '__main__':
    import uvicorn
    factory = create_use_case_factory()
    adapter = RestAdapter(factory)
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. WebSocket Adapter Example

For real-time updates:

```python
# src/adapters/websocket_adapter.py
import asyncio
import websockets
import json
from application.simplified_use_cases import *

class WebSocketAdapter:
    def __init__(self, use_case_factory: UseCaseFactory):
        self.factory = use_case_factory
        self.clients = set()
    
    async def register_client(self, websocket):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
    
    async def handle_message(self, websocket, path):
        """Handle incoming WebSocket messages."""
        async for message in websocket:
            try:
                data = json.loads(message)
                command = data.get('command')
                params = data.get('params', {})
                
                if command == 'list_projects':
                    use_case = self.factory.create_use_case(ListProjectsUseCase)
                    result = await use_case.execute(params.get('instance'))
                elif command == 'get_issue':
                    use_case = self.factory.create_use_case(GetIssueDetailsUseCase)
                    result = await use_case.execute(
                        params.get('issue_key'),
                        params.get('instance')
                    )
                else:
                    result = {"success": False, "error": f"Unknown command: {command}"}
                
                await websocket.send(json.dumps(result.to_dict() if hasattr(result, 'to_dict') else result))
                
            except Exception as e:
                error_response = {"success": False, "error": str(e)}
                await websocket.send(json.dumps(error_response))
    
    async def broadcast_update(self, message):
        """Broadcast update to all connected clients."""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )

# Usage
async def main():
    factory = create_use_case_factory()
    adapter = WebSocketAdapter(factory)
    
    start_server = websockets.serve(adapter.handle_message, "localhost", 8765)
    await start_server
    await asyncio.Future()  # Run forever

if __name__ == '__main__':
    asyncio.run(main())
```

## 📝 Adding New Use Cases

### 1. Create Domain Model (if needed)

```python
# src/domain/models.py
@dataclass
@validate_required_fields(['id', 'name', 'type'])
class JiraWorkflow(BaseModel):
    """Represents a Jira workflow."""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    statuses: List[str] = field(default_factory=list)
    transitions: List[WorkflowTransition] = field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None
```

### 2. Create Use Case

```python
# src/application/simplified_use_cases.py
class GetWorkflowDetailsUseCase(BaseQueryUseCase):
    """Get detailed information about a Jira workflow."""
    
    def __init__(self, workflow_service):
        super().__init__()
        self._workflow_service = workflow_service
    
    async def execute(self, workflow_id: str, instance_name: Optional[str] = None):
        """Execute the get workflow details use case."""
        self._validate_required_params(workflow_id=workflow_id)
        
        def result_mapper(workflow):
            return {
                "workflow": workflow.to_dict(),
                "instance": instance_name or "default"
            }
        
        return await self.execute_query(
            lambda: self._workflow_service.get_workflow(workflow_id, instance_name),
            result_mapper,
            workflow_id=workflow_id,
            instance_name=instance_name
        )
```

### 3. Add Infrastructure Support (if needed)

```python
# src/infrastructure/jira_workflow_repository.py
class JiraWorkflowRepository(BaseJiraAdapter):
    """Repository for Jira workflow operations."""
    
    async def get_workflow(self, workflow_id: str, instance_name: str) -> JiraWorkflow:
        """Get workflow details from Jira."""
        client = self._client_factory.get_client(instance_name)
        
        try:
            # Use Jira API to get workflow details
            workflow_data = client.workflow(workflow_id)
            
            return JiraWorkflow(
                id=workflow_data.id,
                name=workflow_data.name,
                type=workflow_data.type,
                description=workflow_data.description,
                statuses=[status.name for status in workflow_data.statuses],
                transitions=[
                    WorkflowTransition(
                        id=trans.id,
                        name=trans.name,
                        to_status=trans.to.name
                    )
                    for trans in workflow_data.transitions
                ]
            )
        except Exception as e:
            raise JiraDomainException(f"Failed to get workflow {workflow_id}: {str(e)}")
```

### 4. Add to MCP Adapter

```python
# src/adapters/mcp_adapter.py
@srv.tool()
async def get_workflow_details(workflow_id: str, instance_name: str = None) -> dict:
    """
    Get detailed information about a Jira workflow.
    
    Args:
        workflow_id: The workflow ID
        instance_name: Name of the Jira instance to use
        
    Returns:
        A dictionary containing workflow details
    """
    use_case = factory.create_use_case(GetWorkflowDetailsUseCase)
    result = await use_case.execute(workflow_id, instance_name)
    
    if not result.success:
        raise McpError(ErrorCode.INTERNAL_ERROR, result.error)
    
    return result.data
```

## 🔧 Adding New Domain Services

### 1. Define Domain Service

```python
# src/domain/services.py
class WorkflowAnalysisService:
    """Service for analyzing Jira workflows."""
    
    def analyze_workflow_complexity(self, workflow: JiraWorkflow) -> dict:
        """Analyze workflow complexity metrics."""
        return {
            "status_count": len(workflow.statuses),
            "transition_count": len(workflow.transitions),
            "complexity_score": self._calculate_complexity_score(workflow),
            "bottlenecks": self._identify_bottlenecks(workflow),
            "recommendations": self._generate_recommendations(workflow)
        }
    
    def _calculate_complexity_score(self, workflow: JiraWorkflow) -> float:
        """Calculate workflow complexity score."""
        # Complex algorithm here
        base_score = len(workflow.statuses) * 2
        transition_score = len(workflow.transitions) * 1.5
        return base_score + transition_score
    
    def _identify_bottlenecks(self, workflow: JiraWorkflow) -> List[str]:
        """Identify potential workflow bottlenecks."""
        bottlenecks = []
        # Analysis logic here
        return bottlenecks
    
    def _generate_recommendations(self, workflow: JiraWorkflow) -> List[str]:
        """Generate workflow improvement recommendations."""
        recommendations = []
        # Recommendation logic here
        return recommendations
```

### 2. Create Application Service

```python
# src/application/services.py
class WorkflowApplicationService:
    """Application service for workflow operations."""
    
    def __init__(self, workflow_repository, analysis_service):
        self._workflow_repository = workflow_repository
        self._analysis_service = analysis_service
    
    async def get_workflow_analysis(self, workflow_id: str, instance_name: str) -> dict:
        """Get comprehensive workflow analysis."""
        # Get workflow data
        workflow = await self._workflow_repository.get_workflow(workflow_id, instance_name)
        
        # Analyze workflow
        analysis = self._analysis_service.analyze_workflow_complexity(workflow)
        
        return {
            "workflow": workflow.to_dict(),
            "analysis": analysis,
            "instance": instance_name
        }
```

## 🧪 Testing New Extensions

### 1. Test New Use Cases

```python
# src/tests/test_new_use_cases.py
class TestGetWorkflowDetailsUseCase:
    @pytest.fixture
    def mock_workflow_service(self):
        mock = Mock()
        mock.get_workflow = AsyncMock(return_value=sample_workflow)
        return mock
    
    @pytest.fixture
    def use_case(self, mock_workflow_service):
        return GetWorkflowDetailsUseCase(workflow_service=mock_workflow_service)
    
    @pytest.mark.asyncio
    async def test_successful_workflow_retrieval(self, use_case, mock_workflow_service):
        """Test successful workflow details retrieval."""
        result = await use_case.execute("workflow-123", "production")
        
        assert result.success is True
        assert result.data["workflow"]["id"] == "workflow-123"
        mock_workflow_service.get_workflow.assert_called_once_with("workflow-123", "production")
```

### 2. Test New Adapters

```python
# tests/test_cli_adapter.py
class TestCliAdapter:
    @pytest.fixture
    def mock_factory(self):
        factory = Mock()
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value=Mock(success=True, data={"projects": []}))
        factory.create_use_case.return_value = mock_use_case
        return factory
    
    def test_list_projects_command(self, mock_factory):
        """Test CLI list projects command."""
        adapter = CliAdapter(mock_factory)
        runner = CliRunner()
        
        result = runner.invoke(adapter.cli, ['list-projects'])
        
        assert result.exit_code == 0
        mock_factory.create_use_case.assert_called_once()
```

## 🔄 Extension Patterns

### 1. Adapter Pattern Template

```python
# Template for new adapters
class NewAdapter:
    def __init__(self, use_case_factory: UseCaseFactory):
        self.factory = use_case_factory
    
    async def handle_request(self, request_data):
        """Handle incoming request."""
        # 1. Parse request
        command = self._parse_command(request_data)
        params = self._extract_params(request_data)
        
        # 2. Get appropriate use case
        use_case_class = self._get_use_case_class(command)
        use_case = self.factory.create_use_case(use_case_class)
        
        # 3. Execute use case
        result = await use_case.execute(**params)
        
        # 4. Format response
        return self._format_response(result)
    
    def _parse_command(self, request_data):
        """Parse command from request."""
        raise NotImplementedError
    
    def _extract_params(self, request_data):
        """Extract parameters from request."""
        raise NotImplementedError
    
    def _get_use_case_class(self, command):
        """Get use case class for command."""
        raise NotImplementedError
    
    def _format_response(self, result):
        """Format response for this adapter."""
        raise NotImplementedError
```

### 2. Use Case Pattern Template

```python
# Template for new use cases
class NewUseCase(BaseQueryUseCase):  # or BaseCommandUseCase
    def __init__(self, required_service):
        super().__init__()
        self._required_service = required_service
    
    async def execute(self, param1: str, param2: Optional[str] = None):
        """Execute the use case."""
        # 1. Validate parameters
        self._validate_required_params(param1=param1)
        
        # 2. Define result mapper
        def result_mapper(data):
            return {
                "result": data.to_dict(),
                "metadata": {"param1": param1, "param2": param2}
            }
        
        # 3. Execute query/command
        return await self.execute_query(  # or execute_command
            lambda: self._required_service.operation(param1, param2),
            result_mapper,
            param1=param1,
            param2=param2
        )
```

## 📚 Best Practices for Extensions

### 1. Maintain Architecture Boundaries
- **Domain**: Pure business logic, no external dependencies
- **Application**: Orchestration, no framework-specific code
- **Infrastructure**: External integrations, implement domain ports
- **Adapters**: Framework-specific code, translate between frameworks and use cases

### 2. Follow Naming Conventions
- **Use Cases**: `VerbNounUseCase` (e.g., `GetIssueDetailsUseCase`)
- **Services**: `NounService` (e.g., `WorkflowService`)
- **Repositories**: `NounRepository` (e.g., `JiraWorkflowRepository`)
- **Adapters**: `FrameworkAdapter` (e.g., `CliAdapter`, `RestAdapter`)

### 3. Error Handling
- Use domain-specific exceptions in domain layer
- Convert to appropriate format in adapters
- Maintain error context through all layers

### 4. Testing Strategy
- Test each layer independently
- Mock dependencies at layer boundaries
- Use the same test patterns as existing code

### 5. Documentation
- Document new use cases in README.md
- Add examples to this extension guide
- Update architecture diagrams if needed

## 🚀 Deployment Considerations

### 1. Multiple Adapters
You can run multiple adapters simultaneously:

```python
# src/multi_adapter_main.py
import asyncio
from adapters.mcp_adapter import mcp
from adapters.rest_adapter import RestAdapter
from adapters.websocket_adapter import WebSocketAdapter

async def main():
    # Setup shared dependencies
    factory = create_use_case_factory()
    
    # Start multiple adapters
    tasks = [
        # MCP adapter
        asyncio.create_task(mcp.run()),
        
        # REST API adapter
        asyncio.create_task(run_rest_api(factory)),
        
        # WebSocket adapter
        asyncio.create_task(run_websocket_server(factory))
    ]
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Configuration Management
Extend configuration for new adapters:

```yaml
# config.yaml
jira:
  instances:
    production:
      url: "https://company.atlassian.net"
      # ... existing config

adapters:
  mcp:
    enabled: true
  rest:
    enabled: true
    port: 8000
    host: "0.0.0.0"
  websocket:
    enabled: true
    port: 8765
  cli:
    enabled: false
```

## 📈 Performance Considerations

### 1. Shared Use Case Factory
- Reuse the same use case factory across adapters
- Share infrastructure components (repositories, clients)
- Implement proper connection pooling

### 2. Caching
- Add caching at the infrastructure layer
- Cache frequently accessed data (projects, custom fields)
- Implement cache invalidation strategies

### 3. Concurrency
- Use async/await throughout
- Implement proper error handling for concurrent operations
- Consider rate limiting for external APIs

---

**This extension guide ensures that new functionality maintains the hexagonal architecture principles while providing clear patterns for extension.**
