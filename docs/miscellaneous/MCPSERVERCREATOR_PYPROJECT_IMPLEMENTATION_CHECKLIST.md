# mcpservercreator v1.2.0 - pyproject.toml Implementation Checklist

**Date Started**: September 27, 2025  
**Objective**: Replace requirements.txt with pyproject.toml generation for pipx compatibility  
**Target Version**: 1.1.0 → 1.2.0

## **📋 Implementation Checklist**

### **Phase 1: Analysis & Design**
- [ ] Analyze current `_create_requirements_file()` function in server.py
- [ ] Review existing server pyproject.toml files (jira-helper, worldcontext) for best practices
- [ ] Design pyproject.toml template structure for generated servers
- [ ] Define dependency management strategy (core vs. optional dependencies)

### **Phase 2: Implementation**
- [ ] Create `_create_pyproject_file()` function with proper template
- [ ] Remove `_create_requirements_file()` function completely
- [ ] Update `create_server_files()` to call pyproject instead of requirements
- [ ] Ensure proper Python version requirements (>=3.11)
- [ ] Include necessary dependencies: mcp>=1.13.1, mcp-commons>=1.0.0

### **Phase 3: Template Structure Design**
- [ ] Define build system configuration (setuptools)
- [ ] Set up project metadata (name, version, description, author)
- [ ] Configure entry points for main script
- [ ] Define package discovery (src layout)
- [ ] Add development dependencies section if needed

### **Phase 4: Integration & Testing**
- [ ] Test pyproject.toml generation with simple server creation
- [ ] Verify mcp-manager can install generated servers with pipx (default)
- [ ] Test server functionality after installation
- [ ] Ensure proper package structure and imports work correctly

### **Phase 5: Code Quality & Documentation**
- [ ] Add comprehensive docstring to `_create_pyproject_file()`
- [ ] Update existing docstrings referencing requirements.txt
- [ ] Add logging for pyproject.toml creation process
- [ ] Version bump: 1.1.0 → 1.2.0

### **Phase 6: Deployment & Validation**
- [ ] Update mcpservercreator itself via mcp-manager
- [ ] Create test server to validate end-to-end functionality  
- [ ] Test letter-frequency server creation as practical example
- [ ] Document changes in improvement summary

### **Phase 7: Clean-up & Future-proofing**
- [ ] Remove any leftover references to requirements.txt in code/docs
- [ ] Ensure generated servers follow modern Python packaging standards
- [ ] Verify compatibility with Python 3.11+ and latest pip/pipx
- [ ] Commit changes with clear changelog message

---

## **🎯 Expected Outcomes**

### **Technical Benefits**
- Generated servers compatible with pipx-default installation
- Modern Python packaging standards compliance
- Cleaner dependency management
- Better integration with mcp-manager v0.3.0

### **User Benefits**
- Generated servers work with default mcp-manager commands
- No need for `--no-pipx` workarounds
- Professional-quality server packages
- Improved development experience

---

## **🔧 Implementation Notes**

### **Key Files to Modify**
- `servers/mcpservercreator/src/server.py` - Main implementation
- `servers/mcpservercreator/pyproject.toml` - Version bump

### **Template Structure Reference**
```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "server-name"
version = "1.0.0"
description = "Generated MCP server description"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "Author Name", email = "author@example.com"},
]
dependencies = [
    "mcp>=1.13.1",
    "mcp-commons>=1.0.0",
    # Additional dependencies as needed
]

[project.scripts]
server-name = "main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"
```

### **Dependencies to Include**
- **Core**: mcp>=1.13.1, mcp-commons>=1.0.0
- **Common**: collections (built-in), string (built-in)
- **Optional**: Based on user code snippet analysis

---

## **📊 Progress Tracking**

**Started**: September 27, 2025 1:58 PM  
**Phases Completed**: 0/7  
**Items Completed**: 0/28  
**Current Phase**: Phase 1 - Analysis & Design

---

## **🚨 Critical Success Factors**

1. **Compatibility**: Must work with mcp-manager v0.3.0 pipx-default
2. **Standards Compliance**: Follow modern Python packaging best practices
3. **Functionality**: Generated servers must work identically to current approach
4. **Clean Migration**: Complete removal of requirements.txt approach
5. **User Experience**: Seamless operation with no breaking changes

---

**Next Steps**: Begin Phase 1 analysis by examining current requirements.txt generation approach and studying existing pyproject.toml examples.
