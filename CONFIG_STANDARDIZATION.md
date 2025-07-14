# MCP Server Configuration Standardization

## Overview

This document outlines the standardization of configuration management across all MCP servers in the BaseMcpServer project.

## Core Principle

**One Config, One Parser Rule**: Each MCP server must use exactly one configuration file format and one parsing library to handle all configuration needs.

## Decision: Migration to python-decouple

### Problem Statement

The original configuration approach using `python-dotenv` had limitations:
- Poor handling of multi-line JSON values in .env files
- Parsing errors with complex configuration data (e.g., JIRA_INSTANCES JSON)
- Inconsistent behavior across different deployment environments

### Solution

Replace `python-dotenv` with `python-decouple` across all MCP servers.

### Why python-decouple?

1. **Better Multi-line Support**: Handles complex values including multi-line JSON
2. **Drop-in Replacement**: Minimal code changes required
3. **Robust Parsing**: More reliable than python-dotenv for complex configurations
4. **Consistent Behavior**: Works reliably across different environments
5. **Active Maintenance**: Well-maintained library with good documentation

## Implementation Standards

### Requirements File Standard

All MCP server `requirements.txt` files must include:

```
# Core MCP dependencies (Python 3.13+)
mcp>=1.11.0
pydantic-settings>=2.10.1
python-decouple>=3.8
uvicorn>=0.35.0
typer>=0.16.0
```

**Note**: `python-dotenv` is explicitly replaced with `python-decouple`

### Configuration Code Standard

All `config.py` files must use this pattern:

```python
import os
from decouple import config
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Use decouple for complex values
    server_name: str = config('SERVER_NAME', default='default-server')
    api_key: str = config('API_KEY', default='example_key')
    
    # For JSON values, use decouple with cast
    @property
    def complex_config(self):
        import json
        return json.loads(config('COMPLEX_CONFIG', default='{}'))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### .env File Format

The .env file format remains unchanged:
- Simple key=value pairs for basic configuration
- Multi-line JSON values are supported and properly parsed
- No format changes required for existing configurations

## Affected Servers

The following servers require updates:

1. **jira-helper**: Primary driver for this change (multi-line JSON issue)
2. **document-processor**: Consistency update
3. **mcpservercreator**: Consistency update  
4. **template**: Updated to serve as template for new servers

## Benefits

1. **Consistency**: All servers use the same configuration approach
2. **Reliability**: Robust parsing of complex configuration data
3. **Maintainability**: Single approach reduces cognitive overhead
4. **Compatibility**: Existing .env files continue to work without changes
5. **Future-Proof**: Better foundation for complex configuration needs

## Migration Timeline

1. **Phase 1**: Update requirements.txt files
2. **Phase 2**: Update config.py files
3. **Phase 3**: Test and redeploy servers
4. **Phase 4**: Verify functionality

## Testing Criteria

- [ ] All servers start without configuration parsing errors
- [ ] Multi-line JSON values (like JIRA_INSTANCES) parse correctly
- [ ] Existing .env files work without modification
- [ ] All MCP tools and resources function as expected

## Rollback Plan

If issues arise:
1. Revert requirements.txt changes
2. Revert config.py changes
3. Redeploy with original python-dotenv approach
4. Investigate and address root cause

## Future Considerations

This standardization provides a foundation for:
- More complex configuration schemas
- Environment-specific configuration overrides
- Configuration validation and type checking
- Centralized configuration management

---

**Decision Date**: January 13, 2025  
**Status**: Approved for Implementation  
**Next Review**: After successful deployment
