# MCP Resource System Design for Jira Helper Workflow Graphs

## Executive Summary

This document outlines the design for implementing MCP (Model Context Protocol) resources to serve workflow graph images, replacing the current base64 string approach that returns unwieldy 50,000+ character responses.

**Status:** Design Complete - Ready for Implementation  
**Priority:** Medium (UX improvement, not critical functionality)  
**Estimated Effort:** 4-6 hours implementation + testing  

---

## Current Problem Analysis

### Issue: Unmanageable Base64 Responses
```json
// Current response format (truncated for readability)
{
  "success": true,
  "graph": "iVBORw0KGgoAAAANSUhEUgAACJ0AAAZHCAYAAADEkJHgAAAAOnRFWHRTb2Z0d2FyZQBNYXRwbG90bGli...50,244 more characters..."
}
```

### Problems with Current Approach:
- **Massive Response Size**: 50,000+ character strings in JSON responses
- **Poor UX**: Base64 strings can't be directly viewed or opened
- **Protocol Inefficiency**: Violates MCP best practices for binary data
- **Memory Usage**: Large strings consume excessive memory in MCP clients
- **Copy/Paste Issues**: Impossible to manually work with the data

### Current Implementation Location:
- **File**: `src/infrastructure/graph_generator.py`
- **Method**: `MatplotlibGenerator._export_to_base64()`
- **Tool**: `generate_project_workflow_graph`

---

## MCP Resource Solution Architecture

### Core Concept: Resource-Based Image Serving

Instead of returning base64 data inline, save generated images as MCP resources and return clean URIs that can be accessed by MCP clients.

### Resource Storage Strategy

#### 1. Resource Directory Structure
```
~/.mcp_servers/resources/jira-helper/
├── workflow_graphs/
│   ├── ATP_Task_20250926_142555.png
│   ├── PROJ_Story_20250926_143210.png
│   └── DEV_Bug_20250926_144030.png
└── metadata/
    ├── ATP_Task_20250926_142555.json
    └── PROJ_Story_20250926_143210.json
```

#### 2. File Naming Convention
**Format**: `workflow_{project}_{issue_type}_{timestamp}.png`  
**Examples**:
- `workflow_ATP_Task_20250926_142555.png`
- `workflow_MYPROJECT_Story_20250926_143210.png`
- `workflow_DEVOPS_Bug_20250926_144030.png`

#### 3. Metadata Structure
```json
{
  "project_key": "ATP",
  "issue_type": "Task",
  "created_at": "2025-09-26T14:25:55Z",
  "format": "png",
  "size_bytes": 45231,
  "dimensions": {"width": 1400, "height": 1000},
  "graph_stats": {
    "nodes": 5,
    "transitions": 8,
    "layout": "spring"
  },
  "resource_uri": "mcp://jira-helper/workflow_graphs/ATP_Task_20250926_142555.png"
}
```

### MCP Resource Registration

#### mcp-commons Resource Configuration
```python
# In main.py - Add resource configuration
from mcp_commons import run_mcp_server, create_mcp_app

def create_resource_config():
    """Configure MCP resources for workflow graphs."""
    resource_dir = Path.home() / ".mcp_servers" / "resources" / "jira-helper"
    resource_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        "workflow_graphs": {
            "path": resource_dir / "workflow_graphs",
            "mime_type": "image/png",
            "max_age_hours": 1,  # Auto-cleanup after 1 hour
            "max_files": 100     # Limit total files
        }
    }
```

### Modified Tool Response Format

#### New Response Structure
```json
{
  "success": true,
  "message": "Workflow graph generated successfully",
  "resource": {
    "uri": "mcp://jira-helper/workflow_graphs/ATP_Task_20250926_142555.png",
    "type": "image/png",
    "description": "ATP Task workflow graph with 5 nodes and 8 transitions"
  },
  "graph_info": {
    "project": "ATP",
    "issue_type": "Task",
    "nodes": 5,
    "transitions": 8,
    "layout": "spring",
    "created_at": "2025-09-26T14:25:55Z"
  }
}
```

#### Benefits of New Response:
- **Compact**: ~200 characters vs 50,000+
- **Clickable**: URIs can be opened directly by MCP clients
- **Cacheable**: Resources can be cached by protocol layer
- **Metadata Rich**: Includes graph statistics and creation info

---

## Implementation Plan

### Phase 1: Core Resource Infrastructure (2 hours)

#### 1.1 Update `graph_generator.py`
```python
# Replace _export_to_base64() method with:
def _save_to_resource_file(self, workflow: WorkflowGraph, format: str) -> dict:
    """Save matplotlib figure to resource file and return metadata."""
    
    # Create resource directory
    resource_dir = Path.home() / ".mcp_servers" / "resources" / "jira-helper" / "workflow_graphs"
    resource_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"workflow_{workflow.project_key}_{workflow.issue_type}_{timestamp}.png"
    filepath = resource_dir / filename
    
    # Save image
    plt.savefig(filepath, format='png', bbox_inches='tight', dpi=150,
               facecolor='white', edgecolor='none', pad_inches=0.5)
    plt.close()
    
    # Create resource URI
    resource_uri = f"mcp://jira-helper/workflow_graphs/{filename}"
    
    # Return metadata
    return {
        "uri": resource_uri,
        "filepath": str(filepath),
        "filename": filename,
        "size_bytes": filepath.stat().st_size,
        "created_at": datetime.now().isoformat() + "Z"
    }
```

#### 1.2 Modify `generate_visual_graph()` method
```python
async def generate_visual_graph(self, workflow: WorkflowGraph, format: str = "png") -> dict:
    """Generate a visual graph and return resource metadata."""
    if not self.is_available():
        raise JiraGraphLibraryNotAvailable(["matplotlib", "networkx"])

    try:
        # Create NetworkX graph
        graph = self._create_networkx_graph(workflow)
        
        if graph.number_of_nodes() == 0:
            logger.warning("Empty workflow graph")
            return {"error": "Empty workflow - no nodes to display"}
        
        # Render and save to resource
        resource_info = self._render_and_save_graph(graph, workflow, format)
        
        return {
            "resource": resource_info,
            "graph_stats": {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "layout": self._get_layout_name(graph)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate visual graph: {str(e)}")
        return {"error": f"Graph generation failed: {str(e)}"}
```

### Phase 2: Resource Cleanup System (1 hour)

#### 2.1 Automatic Cleanup Service
```python
# New file: src/infrastructure/resource_cleanup.py
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

class ResourceCleanupService:
    """Service to clean up old workflow graph resources."""
    
    def __init__(self, max_age_hours: int = 1, max_files: int = 100):
        self.max_age_hours = max_age_hours
        self.max_files = max_files
        self.resource_dir = Path.home() / ".mcp_servers" / "resources" / "jira-helper" / "workflow_graphs"
    
    async def cleanup_old_files(self):
        """Remove files older than max_age_hours."""
        if not self.resource_dir.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        
        for file_path in self.resource_dir.glob("*.png"):
            if file_path.stat().st_mtime < cutoff_time.timestamp():
                file_path.unlink()
                logger.debug(f"Cleaned up old resource: {file_path.name}")
    
    async def enforce_file_limit(self):
        """Keep only the most recent max_files."""
        if not self.resource_dir.exists():
            return
        
        files = list(self.resource_dir.glob("*.png"))
        if len(files) <= self.max_files:
            return
        
        # Sort by modification time, newest first
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Remove excess files
        for file_path in files[self.max_files:]:
            file_path.unlink()
            logger.debug(f"Removed excess resource: {file_path.name}")
    
    async def periodic_cleanup(self):
        """Run cleanup periodically."""
        while True:
            try:
                await self.cleanup_old_files()
                await self.enforce_file_limit()
            except Exception as e:
                logger.error(f"Resource cleanup error: {e}")
            
            # Run cleanup every 15 minutes
            await asyncio.sleep(900)
```

#### 2.2 Integration with Main Server
```python
# In main.py - Add cleanup service
async def start_background_services():
    """Start background services."""
    cleanup_service = ResourceCleanupService()
    asyncio.create_task(cleanup_service.periodic_cleanup())

# Modify main() to start background services
def main():
    # ... existing code ...
    
    if transport == "stdio":
        logger.info("🚀 Starting Jira Helper MCP server with stdio transport")
        # Start background services
        asyncio.run(start_background_services())
        
        run_mcp_server(
            server_name=server_name,
            tools_config=get_tools_config(),
            transport="stdio",
            resources_config=create_resource_config()  # Add resource config
        )
```

### Phase 3: MCP Resource Registration (1-2 hours)

#### 3.1 Resource Configuration in mcp-commons
```python
# In main.py - Add resource configuration function
def create_resource_config():
    """Create MCP resource configuration."""
    resource_dir = Path.home() / ".mcp_servers" / "resources" / "jira-helper"
    
    return {
        "workflow_graphs": {
            "base_path": resource_dir / "workflow_graphs",
            "mime_type": "image/png",
            "description": "Generated Jira workflow graphs",
            "access_pattern": "mcp://jira-helper/workflow_graphs/{filename}"
        }
    }

# Modify server initialization calls
run_mcp_server(
    server_name=server_name,
    tools_config=get_tools_config(),
    resources_config=create_resource_config(),  # Add this line
    transport="stdio"
)
```

### Phase 4: Tool Response Updates (1 hour)

#### 4.1 Update Use Case Response Format
```python
# In application/use_cases.py - Modify GenerateWorkflowGraphUseCase
async def execute(self, **kwargs) -> dict:
    # ... existing validation code ...
    
    try:
        # Generate workflow graph (returns resource metadata now)
        graph_result = await self.workflow_service.generate_workflow_graph(
            project_key=project_key,
            issue_type=issue_type,
            format=format,
            instance_name=instance_name
        )
        
        if "error" in graph_result:
            return {"success": False, "error": graph_result["error"]}
        
        # Return new resource-based format
        return {
            "success": True,
            "message": f"Workflow graph generated for {project_key} {issue_type}",
            "resource": graph_result["resource"],
            "graph_info": {
                "project": project_key,
                "issue_type": issue_type,
                "format": format,
                **graph_result["graph_stats"]
            }
        }
        
    except Exception as e:
        logger.error(f"Workflow graph generation failed: {str(e)}")
        return {"success": False, "error": str(e)}
```

---

## Testing Plan

### Unit Tests
```python
# Test file: tests/test_mcp_resources.py
import pytest
from pathlib import Path
from infrastructure.graph_generator import MatplotlibGenerator

class TestMCPResources:
    
    def test_resource_file_creation(self):
        """Test that resource files are created correctly."""
        # Create test workflow
        # Generate graph
        # Verify file exists and has correct name
        pass
    
    def test_resource_cleanup(self):
        """Test automatic resource cleanup."""
        # Create old files
        # Run cleanup
        # Verify old files removed
        pass
    
    def test_resource_uri_format(self):
        """Test resource URI format is correct."""
        # Generate graph
        # Verify URI matches expected format
        pass
```

### Integration Tests
```python
# Test MCP resource access
def test_mcp_resource_access():
    """Test that generated resources are accessible via MCP."""
    # Generate workflow graph
    # Verify resource URI returns image data
    # Verify MIME type is correct
    pass
```

### Manual Testing Checklist
- [ ] Generate workflow graph via MCP tool
- [ ] Verify response contains resource URI instead of base64
- [ ] Test resource URI opens image correctly
- [ ] Verify automatic cleanup removes old files
- [ ] Test file limit enforcement
- [ ] Verify error handling for failed generations

---

## Benefits Analysis

### Immediate Benefits
- **90%+ Response Size Reduction**: From 50KB to <1KB responses
- **Better UX**: Clickable URIs that open images directly
- **Protocol Compliance**: Uses MCP resources as intended
- **Memory Efficiency**: No large strings in memory

### Long-term Benefits
- **Caching**: MCP clients can cache resources
- **Bandwidth**: Reduced network traffic
- **Debugging**: Generated images can be inspected on disk
- **Extensibility**: Framework for other resource types

### Trade-offs
- **Complexity**: Additional file management code
- **Dependencies**: Requires filesystem access
- **Cleanup**: Need to manage temporary files
- **Testing**: More complex integration testing

---

## Migration Strategy

### Backward Compatibility
- Keep existing base64 export as fallback
- Add format parameter: `legacy_base64` vs `resource_uri`
- Gradual migration over 2 release cycles

### Deployment Considerations
- Ensure resource directory permissions
- Test cleanup service in production
- Monitor disk usage patterns
- Plan for container deployment (mounted volumes)

---

## Alternative Approaches Considered

### 1. HTTP Server Approach
**Pros**: Simple, widely supported  
**Cons**: Additional port/service, not MCP-native  
**Verdict**: Rejected - adds complexity without MCP benefits

### 2. Embedded Thumbnails
**Pros**: Small base64 previews + resource URIs  
**Cons**: Still includes base64 data  
**Verdict**: Possible enhancement for future

### 3. External Image Service
**Pros**: Scalable, professional  
**Cons**: Additional infrastructure dependency  
**Verdict**: Overkill for current needs

---

## Future Enhancements

### Enhanced Resource Types
- **SVG Support**: Vector graphics for better scaling
- **Interactive Graphs**: HTML+JavaScript for clickable nodes
- **Multi-format**: Same graph in PNG/SVG/PDF

### Resource Management
- **User Preferences**: Retention time settings
- **Resource Sharing**: Share graphs between sessions
- **Resource History**: Track generated graph history

### Analytics Integration
- **Usage Metrics**: Track most-requested workflows
- **Performance Metrics**: Generation time tracking
- **Resource Metrics**: File size and access patterns

---

## Conclusion

The MCP resource system provides a clean, protocol-compliant solution to the base64 string problem. Implementation is straightforward with mcp-commons support, and the benefits significantly outweigh the additional complexity.

**Recommendation**: Implement when UX improvements are prioritized. The current base64 approach works functionally but provides poor user experience.

**Next Steps**: 
1. Create implementation ticket
2. Set up development environment testing
3. Implement Phase 1 (core infrastructure)
4. Test resource access functionality
5. Complete remaining phases

---

*Last Updated: September 26, 2025*  
*Author: Cline (AI Assistant)*  
*Status: Design Complete - Ready for Implementation*
