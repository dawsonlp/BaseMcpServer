# Jira Helper Cline Compatibility Design Document

## Executive Summary

Based on our analysis of Cline MCP compatibility issues (GitHub issue #4391) and successful test server implementation, this document outlines the design changes needed to make the Jira Helper server fully compatible with Cline.

## Current State Analysis

### Existing Architecture
The Jira Helper currently implements a **dual adapter architecture**:

1. **Direct MCP Adapter** (`src/main.py`) - Uses FastMCP with default transport (STDIO)
2. **Streamable HTTP Adapter** (`src/streamable_main.py`) - Uses `transport="streamable-http"`
3. **Custom HTTP Adapter** (`src/http_main.py`) - Custom Starlette-based REST API

### Critical Compatibility Issues Identified

#### 1. StreamableHttpTransport is Broken in Cline
- **Issue**: [#3315](https://github.com/cline/cline/issues/3315) - Cline sends GET requests instead of POST
- **Impact**: `src/streamable_main.py` will not work with Cline
- **Current Status**: Broken and unusable with Cline

#### 2. Missing SSE Transport Implementation
- **Issue**: No SSE transport option currently available
- **Impact**: Cannot use the working HTTP transport method for Cline
- **Required**: New SSE transport entry point needed

#### 3. Configuration Complexity
- **Issue**: Multiple entry points create confusion
- **Impact**: Users don't know which transport to use with Cline
- **Required**: Clear guidance and simplified configuration

## Recommended Design Changes

### 1. Add SSE Transport Support

#### New Entry Point: `src/sse_main.py`
```python
"""
SSE transport entry point for Cline compatibility.
Uses the same FastMCP server with SSE transport.
"""
from adapters.mcp_adapter import mcp

def main():
    # Use SSE transport - the only HTTP transport that works with Cline
    mcp.run(transport="sse")

if __name__ == "__main__":
    main()
```

#### Benefits
- **Cline Compatible**: Uses working SSE transport
- **Minimal Changes**: Reuses existing FastMCP server and tools
- **DRY Compliance**: Shares all business logic with other adapters

### 2. Transport Strategy Matrix

| Transport | Entry Point | Use Case | Cline Compatible |
|-----------|-------------|----------|------------------|
| STDIO | `src/main.py` | Local development, traditional MCP clients | ✅ Yes |
| SSE | `src/sse_main.py` | **Cline integration, remote HTTP** | ✅ Yes |
| StreamableHttp | `src/streamable_main.py` | Other MCP clients (not Cline) | ❌ No |
| Custom HTTP | `src/http_main.py` | REST API, Docker deployment | ⚠️ Not MCP |

### 3. Deprecation Strategy

#### Phase 1: Add SSE Support (Immediate)
- Create `src/sse_main.py` with SSE transport
- Update documentation to recommend SSE for Cline
- Test SSE transport with Cline

#### Phase 2: Update Documentation (Short-term)
- Mark `streamable_main.py` as "Not compatible with Cline"
- Provide clear guidance on transport selection
- Update README with Cline-specific instructions

#### Phase 3: Consider Deprecation (Long-term)
- Monitor Cline issue #4391 for StreamableHttp fixes
- Consider removing `streamable_main.py` if not fixed
- Focus development on STDIO and SSE transports

### 4. Configuration Recommendations

#### For Cline Users (Recommended)
```json
{
  "mcpServers": {
    "jira-helper": {
      "url": "http://localhost:8000/sse",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

#### For Local Development
```json
{
  "mcpServers": {
    "jira-helper": {
      "command": "python",
      "args": ["/path/to/jira-helper/src/main.py"],
      "env": {
        "JIRA_API_TOKEN": "your_token"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Implementation Plan

### Step 1: Create SSE Entry Point
- **File**: `src/sse_main.py`
- **Content**: Minimal wrapper using existing FastMCP server with SSE transport
- **Testing**: Verify works with test-mcp-server pattern

### Step 2: Update Docker Support
- **File**: `Dockerfile.sse`
- **Purpose**: Docker container for SSE transport
- **Base**: Similar to existing `Dockerfile.http`

### Step 3: Update Documentation
- **Files**: `README.md`, `DUAL_ADAPTER_ARCHITECTURE.md`
- **Content**: Clear transport selection guidance
- **Focus**: Cline compatibility recommendations

### Step 4: Add Docker Compose
- **File**: `docker-compose.sse.yml`
- **Purpose**: Easy SSE deployment
- **Configuration**: Port 8000 with SSE transport

### Step 5: Create Test Scripts
- **File**: `test_cline_compatibility.py`
- **Purpose**: Automated testing of Cline compatibility
- **Coverage**: SSE transport, tool execution, error handling

## Risk Assessment

### Low Risk
- **SSE Transport Addition**: Uses existing FastMCP framework
- **Documentation Updates**: No code changes required
- **Docker Configuration**: Standard containerization

### Medium Risk
- **Transport Selection Confusion**: Multiple entry points may confuse users
- **Maintenance Overhead**: Additional entry point to maintain

### High Risk
- **Cline Compatibility Changes**: Future Cline updates may break SSE transport
- **StreamableHttp Future**: If fixed, may need to reconsider strategy

## Mitigation Strategies

### 1. Clear Documentation
- Provide decision matrix for transport selection
- Include troubleshooting guide for common issues
- Link to Cline compatibility guide

### 2. Automated Testing
- Test all transports in CI/CD pipeline
- Include Cline-specific compatibility tests
- Monitor for transport regressions

### 3. Version Monitoring
- Track Cline issue #4391 for updates
- Test with new Cline versions
- Adapt strategy based on fixes

## Success Metrics

### Immediate (1 week)
- [ ] SSE transport entry point created and tested
- [ ] Docker configuration for SSE transport
- [ ] Documentation updated with Cline guidance

### Short-term (1 month)
- [ ] Cline users successfully using SSE transport
- [ ] Reduced support requests about transport issues
- [ ] Clear migration path from StreamableHttp

### Long-term (3 months)
- [ ] Stable Cline integration with SSE transport
- [ ] Decision on StreamableHttp deprecation
- [ ] Streamlined transport architecture

## Technical Specifications

### SSE Transport Requirements
- **Port**: 8000 (default FastMCP port)
- **Endpoint**: `/sse` (FastMCP SSE endpoint)
- **Protocol**: Server-Sent Events over HTTP
- **Authentication**: Same as existing transports

### Configuration Schema
```yaml
# config.yaml - same for all transports
jira_instances:
  default:
    url: "https://your-instance.atlassian.net"
    username: "your-email@domain.com"
    api_token: "${JIRA_API_TOKEN}"
```

### Environment Variables
- `JIRA_API_TOKEN`: Required for all transports
- `PORT`: Optional, defaults to 8000 for SSE
- `LOG_LEVEL`: Optional, defaults to INFO

## Conclusion

The addition of SSE transport support will make the Jira Helper fully compatible with Cline while maintaining the existing dual adapter architecture. This approach:

1. **Solves immediate Cline compatibility issues**
2. **Maintains backward compatibility** with existing deployments
3. **Provides clear migration path** from broken StreamableHttp
4. **Follows established patterns** from successful test server

The implementation is low-risk and high-impact, providing Cline users with a reliable way to use the Jira Helper while preserving all existing functionality for other use cases.

## Next Steps

1. **Review and approve** this design document
2. **Implement SSE transport** entry point
3. **Test with Cline** using established patterns
4. **Update documentation** with clear guidance
5. **Deploy and monitor** for compatibility issues

This design ensures the Jira Helper remains a robust, multi-transport MCP server while providing excellent Cline compatibility through the proven SSE transport method.
