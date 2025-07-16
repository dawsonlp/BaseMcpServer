# MCP Multi-Server Deployment Plan

## Overview
Deploy multiple MCP servers in a single Docker container using Starlette + Uvicorn architecture (following MCP_STREAMABLE_HTTP_GUIDE.md). Each server will be accessible via different routes with individual health checks, metrics, and documentation.

## Target Architecture
```
Single Docker Container (localhost:8000)
├── /jira-helper/
│   ├── /mcp → MCP streamable HTTP endpoint
│   ├── /health → Service health check
│   ├── /metrics → Service metrics
│   └── /docs → API documentation
├── /document-processor/
│   ├── /mcp → MCP streamable HTTP endpoint
│   ├── /health → Service health check
│   ├── /metrics → Service metrics
│   └── /docs → API documentation
├── /health → Global health check (all services)
├── /metrics → Global metrics aggregation
└── /docs → Global documentation page
```

## Development Checklist

### Phase 1: Project Structure Setup
- [ ] Create `multi-mcp-server/` directory structure
- [ ] Set up base configuration system
- [ ] Create requirements.txt with all dependencies
- [ ] Set up logging configuration
- [ ] Create base Docker configuration

### Phase 2: Core Application Framework
- [ ] Create main Starlette application (`main.py`)
- [ ] Implement global health check endpoint
- [ ] Implement global metrics endpoint
- [ ] Implement global documentation page
- [ ] Set up CORS middleware
- [ ] Create service registry system

### Phase 3: MCP Server Integration (Hexagonal Architecture)
- [ ] Import existing jira-helper service (symlink or copy to services/)
- [ ] Modify jira-helper MCP adapter to support streamable HTTP transport
- [ ] Create multi-server adapter that can mount existing MCP adapters
- [ ] Implement service registry for dynamic service discovery
- [ ] Test jira-helper integration without changing core business logic
- [ ] Add document-processor service integration (same pattern)
- [ ] Verify MCP protocol compatibility across all services
- [ ] Ensure each service maintains independent deployability

### Phase 4: Health Monitoring System
- [ ] Individual service health checks
- [ ] Global health aggregation logic
- [ ] Health check response formatting
- [ ] Service status tracking
- [ ] Error handling and recovery
- [ ] Health check caching/optimization

### Phase 5: Metrics and Observability
- [ ] Individual service metrics collection
- [ ] Global metrics aggregation
- [ ] Prometheus-compatible metrics format
- [ ] Request/response timing metrics
- [ ] Error rate tracking
- [ ] Resource usage monitoring

### Phase 6: Documentation System
- [ ] Auto-generate API docs for each MCP server
- [ ] Create global documentation index
- [ ] OpenAPI/Swagger integration
- [ ] Interactive API documentation
- [ ] Service capability documentation
- [ ] Usage examples and guides

### Phase 7: Configuration Management
- [ ] Multi-service configuration schema
- [ ] Environment variable handling
- [ ] Secrets management
- [ ] Configuration validation
- [ ] Hot-reload capability (development)
- [ ] Production configuration security

### Phase 8: Docker Deployment
- [ ] Multi-stage Dockerfile
- [ ] Docker Compose configuration
- [ ] Volume mounting for configs
- [ ] Environment variable setup
- [ ] Health check configuration
- [ ] Resource limits and optimization

### Phase 9: Testing and Validation
- [ ] Unit tests for core framework
- [ ] Integration tests for MCP servers
- [ ] Health check endpoint testing
- [ ] Load testing for multiple services
- [ ] Docker deployment testing
- [ ] End-to-end client testing

### Phase 10: Documentation and Deployment
- [ ] README with deployment instructions
- [ ] Configuration examples
- [ ] Troubleshooting guide
- [ ] Performance tuning guide
- [ ] Security best practices
- [ ] Production deployment checklist

## Technical Specifications

### Dependencies
```
# Core MCP and web framework
mcp>=1.11.0
starlette>=0.47.1
uvicorn>=0.35.0
fastapi>=0.116.1

# HTTP and async support
httpx>=0.28.1
httpx-sse>=0.4.1
anyio>=4.9.0
h11>=0.16.0
httpcore>=1.0.9

# Data validation and settings
pydantic>=2.11.7
pydantic-settings>=2.10.1
pydantic_core>=2.33.2

# Configuration and utilities
pyyaml>=6.0
click>=8.2.1

# Additional dependencies
jira>=3.5.0
prometheus-client>=0.20.0
python-multipart>=0.0.20
sse-starlette>=2.4.1

# Type checking and validation
annotated-types>=0.7.0
typing-extensions>=4.14.1
typing-inspection>=0.4.1

# JSON schema and validation
jsonschema>=4.24.0
jsonschema-specifications>=2025.4.1
referencing>=0.36.2
rpds-py>=0.26.0

# Utilities
attrs>=25.3.0
certifi>=2025.7.14
idna>=3.10
sniffio>=1.3.1
```

### Configuration Structure
```yaml
server:
  name: multi-mcp-server
  host: 0.0.0.0
  port: 8000
  debug: false
  log_level: INFO

services:
  jira-helper:
    enabled: true
    path: /jira-helper
    config_file: jira-helper-config.yaml
  
  document-processor:
    enabled: true
    path: /document-processor
    config_file: document-processor-config.yaml

global:
  cors_origins: ["*"]
  health_check_interval: 30
  metrics_enabled: true
```

### Directory Structure
```
multi-mcp-server/
├── main.py                 # Main Starlette application entry point
├── config.yaml            # Global multi-server configuration
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Orchestration
├── README.md              # Deployment guide
├── src/
│   ├── __init__.py
│   ├── multi_server_adapter.py  # Main HTTP adapter (hexagonal port)
│   ├── config.py          # Configuration management
│   ├── health.py          # Global health check system
│   ├── metrics.py         # Global metrics collection
│   ├── docs.py            # Global documentation generation
│   └── service_registry.py # Service discovery and mounting
├── services/              # Imported existing services (symlinks or copies)
│   ├── jira-helper/       # → ../servers/jira-helper/src/
│   └── document-processor/ # → ../servers/document-processor/src/
├── configs/
│   ├── jira-helper-config.yaml
│   └── document-processor-config.yaml
├── templates/
│   ├── global_docs.html   # Global documentation template
│   └── service_docs.html  # Service documentation template
└── tests/
    ├── test_multi_server_adapter.py
    ├── test_health.py
    ├── test_metrics.py
    ├── test_service_registry.py
    └── test_integration.py
```

**Key Architectural Changes:**
- `multi_server_adapter.py`: The main hexagonal adapter that hosts multiple MCP adapters
- `services/`: Symlinks or imports to existing service implementations
- `service_registry.py`: Manages service discovery and mounting
- Preserves existing service directory structures unchanged

## Implementation Notes

### Hexagonal Architecture Compliance
The jira-helper uses hexagonal architecture where the MCP server is just one of many possible adapters. The multi-server deployment must respect this architecture:

**Current jira-helper Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Adapters (Ports)                        │
├─────────────────────────────────────────────────────────────┤
│  Direct MCP     │  Streamable    │  CLI Adapter │  Web API  │
│  Adapter        │  HTTP MCP      │  (future)    │  Adapter  │
│  (existing)     │  Adapter (new) │              │  (future) │
│                 │                │              │           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Shared MCP Tool Definitions                  │ │
│  │  (DRY - used by both MCP adapters)                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Application Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Use Cases: ListProjectsUseCase, GetIssueDetailsUseCase,   │
│  CreateIssueUseCase, TransitionIssueUseCase, etc.          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Domain Layer                              │
├─────────────────────────────────────────────────────────────┤
│  Services: IssueService, WorkflowService, ProjectService   │
│  Models: Issue, Project, Workflow                          │
│  Ports: Repository interfaces                              │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                         │
├─────────────────────────────────────────────────────────────┤
│  JiraApiRepository, JiraClientFactory, ConfigAdapter       │
│  GraphvizGenerator, LoggerAdapter                          │
└─────────────────────────────────────────────────────────────┘
```

**Key DRY Architecture Points:**
- Both MCP adapters share the same tool definitions
- Both adapters use the same underlying use cases and domain logic
- Only the transport mechanism differs (direct I/O vs HTTP)
- No duplication of business logic or MCP tool implementations

### Multi-Server Integration Strategy
Instead of wrapping MCP servers, we need to:

1. **Reuse Existing Architecture**: Import and reuse the existing domain, application, and infrastructure layers
2. **Create New Adapter**: Build a multi-server HTTP adapter that can host multiple MCP adapters
3. **Preserve Separation**: Keep the MCP functionality as one deployment option among many

**Proposed Multi-Server Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│              Multi-Server HTTP Adapter                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ /jira-helper│  │ /doc-proc   │  │ /service-n  │        │
│  │    MCP      │  │    MCP      │  │    MCP      │        │
│  │  Adapter    │  │  Adapter    │  │  Adapter    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  Existing Application + Domain + Infrastructure Layers     │
│  (Unchanged - reused from each service)                    │
└─────────────────────────────────────────────────────────────┘
```

### Service Integration Pattern
Each service maintains its hexagonal architecture:
- **Domain Layer**: Business logic remains unchanged
- **Application Layer**: Use cases remain unchanged  
- **Infrastructure Layer**: Jira clients, config adapters remain unchanged
- **New Adapter Layer**: Multi-server HTTP adapter that mounts existing MCP adapters

This ensures:
- ✅ **Architecture Preservation**: Each service keeps its clean architecture
- ✅ **Deployment Flexibility**: MCP server is one option (CLI, web API, etc. remain possible)
- ✅ **Code Reuse**: No duplication of business logic
- ✅ **Independent Evolution**: Each service can evolve independently

### Health Check Strategy
- **Individual**: Each service reports its own health status
- **Global**: Aggregates all service health into overall system status
- **Graceful Degradation**: System remains partially functional if one service fails

### Configuration Best Practices
- Environment-specific configs
- Secrets externalization
- Validation on startup
- Hot-reload for development
- Immutable production configs

### Security Considerations
- No secrets in Docker images
- Proper CORS configuration
- Input validation
- Rate limiting (future enhancement)
- Authentication/authorization (future enhancement)

## Success Criteria
- [ ] All MCP servers accessible via their respective routes
- [ ] Global and individual health checks working
- [ ] Comprehensive API documentation available
- [ ] Docker deployment working on localhost
- [ ] Configuration management functional
- [ ] Metrics collection operational
- [ ] Error handling and logging working
- [ ] Performance acceptable for development use

## Revised Implementation Strategy

Based on architectural analysis, we should proceed more carefully:

### Step 1: Add Streamable HTTP Adapter to jira-helper (DRY Architecture)
- [ ] Create new streamable HTTP adapter alongside existing direct MCP adapter
- [ ] Extract shared MCP tool definitions to avoid duplication between adapters
- [ ] Ensure both adapters use the same underlying use cases and domain logic
- [ ] Add Docker deployment capability for streamable HTTP adapter
- [ ] Test both deployment methods (direct MCP + streamable HTTP) work independently
- [ ] Document the dual-adapter pattern and shared tool architecture

### Step 2: Create Template from jira-helper
- [ ] Extract the streamable HTTP + Docker pattern from jira-helper
- [ ] Create documentation for applying this pattern to other MCP servers
- [ ] Apply the pattern to document-processor (or another service)
- [ ] Validate that the pattern works across different service types

### Step 3: Design Multi-Server Combination
- [ ] Analyze how to combine multiple individual streamable HTTP MCP servers
- [ ] Design the external multi-server adapter architecture
- [ ] Plan the routing, health checks, and documentation aggregation
- [ ] Implement the multi-server deployment

## Immediate Next Steps
1. **Focus on jira-helper first**: Add streamable HTTP transport support
2. **Add Docker deployment**: Create containerized deployment for jira-helper
3. **Test and validate**: Ensure the individual service works properly
4. **Document the pattern**: Create reusable template for other services
5. **Scale to multiple services**: Only after individual pattern is proven

This approach ensures we:
- ✅ Respect the existing hexagonal architecture
- ✅ Create a proven pattern before scaling
- ✅ Maintain individual service deployability
- ✅ Build incrementally with validation at each step

---
*This plan will be updated as development progresses and requirements evolve.*
