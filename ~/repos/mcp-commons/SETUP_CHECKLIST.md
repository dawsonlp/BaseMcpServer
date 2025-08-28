# MCP Commons PyPI Publication Setup Checklist

## Repository Setup
- [ ] Directory structure created (`~/repos/mcp-commons`)
- [ ] Git repository initialized (`git init`)
- [ ] Remote origin configured to new GitHub repository
- [ ] Initial commit completed

## Security & Credentials Setup
- [ ] `.gitignore` configured to exclude `.env`, `dist/`, `build/`, `__pycache__/`
- [ ] `.env.example` created with placeholder values (no real tokens)
- [ ] PyPI account created/verified at https://pypi.org
- [ ] Test PyPI account created/verified at https://test.pypi.org
- [ ] PyPI API token obtained and stored in `~/.env` as `PYPI_API_TOKEN`
- [ ] Test PyPI API token obtained and stored in `~/.env` as `TESTPYPI_API_TOKEN`

## Code Migration from BaseMcpServer
- [ ] Source code copied from `libs/mcp-commons/src/` to `src/`
- [ ] Tests copied from `libs/mcp-commons/tests/` to `tests/`
- [ ] `pyproject.toml` adapted for standalone package
- [ ] `README.md` updated for standalone package
- [ ] Dependencies verified and tested
- [ ] Git history preserved (optional, using `git subtree`)

## Build & Testing Setup
- [ ] Build tools installed: `pip install build twine`
- [ ] Package builds successfully: `python -m build`
- [ ] Package validation passes: `twine check dist/*`
- [ ] Local import tests pass
- [ ] Virtual environment testing completed

## PyPI Publication Process
- [ ] Test PyPI account configured in local environment
- [ ] Package uploaded to test PyPI: `twine upload --repository testpypi dist/*`
- [ ] Installation from test PyPI verified
- [ ] Basic functionality testing from test PyPI completed
- [ ] Package uploaded to production PyPI: `twine upload dist/*`
- [ ] Installation from production PyPI verified

## CI/CD Pipeline Setup (Optional but Recommended)
- [ ] GitHub Actions workflow created (`.github/workflows/test.yml`)
- [ ] GitHub Actions workflow for PyPI publishing (`.github/workflows/publish.yml`)
- [ ] GitHub repository secrets configured:
  - [ ] `PYPI_API_TOKEN` added to repository secrets
  - [ ] `TESTPYPI_API_TOKEN` added to repository secrets
- [ ] Automated tests run on pull requests
- [ ] Automated publishing on version tags (e.g., `v1.0.1`)

## Documentation Updates
- [ ] `README.md` updated with installation instructions
- [ ] Usage examples validated and working
- [ ] API documentation complete
- [ ] `CHANGELOG.md` created for version tracking
- [ ] License file included (MIT)

## Version Management
- [ ] Semantic versioning strategy documented
- [ ] Initial version set to `1.0.0` in `pyproject.toml`
- [ ] Version bumping process documented
- [ ] Release process documented

## Server Migration & Testing
- [ ] `BaseMcpServer/servers/jira-helper/requirements.txt` updated to use `mcp-commons>=1.0.0`
- [ ] `BaseMcpServer/servers/worldcontext/requirements.txt` updated to use `mcp-commons>=1.0.0`
- [ ] `BaseMcpServer/servers/jira-helper/pyproject.toml` updated to remove `file://` references
- [ ] `BaseMcpServer/servers/worldcontext/pyproject.toml` updated to remove `file://` references
- [ ] pipx installations work correctly for both servers
- [ ] mcpmanager deployment works without absolute paths
- [ ] All server tests pass with PyPI-installed mcp-commons

## Final Validation
- [ ] Clean environment test: Fresh virtual env + pip install mcp-commons
- [ ] Import test: `from mcp_commons import create_mcp_adapter, bulk_register_tools`
- [ ] Server integration test: Both jira-helper and worldcontext work
- [ ] Performance verification: No regression in registration times
- [ ] Documentation accuracy: All examples work as documented

## Post-Publication Cleanup
- [ ] `BaseMcpServer/libs/mcp-commons/` directory removed
- [ ] BaseMcpServer documentation updated to reference new PyPI package
- [ ] Migration notes documented for future reference
- [ ] Temporary workaround files cleaned up

---

## Quick Commands Reference

### Build and Test Locally
```bash
# Build package
python -m build

# Check package
twine check dist/*

# Test locally
pip install dist/mcp_commons-*.whl
python -c "from mcp_commons import create_mcp_adapter; print('✅ Success!')"
```

### Publish to Test PyPI
```bash
# Upload to test PyPI
twine upload --repository testpypi dist/* --username __token__ --password $TESTPYPI_API_TOKEN

# Test install from test PyPI  
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-commons
```

### Publish to Production PyPI
```bash
# Upload to production PyPI
twine upload dist/* --username __token__ --password $PYPI_API_TOKEN

# Test install from PyPI
pip install mcp-commons
```

### Server Testing
```bash
# Test jira-helper with PyPI mcp-commons
cd BaseMcpServer/servers/jira-helper
pip install mcp-commons>=1.0.0  # instead of local editable install
PYTHONPATH=src python -m pytest src/tests/ -v

# Test worldcontext with PyPI mcp-commons  
cd BaseMcpServer/servers/worldcontext
pip install mcp-commons>=1.0.0
python src/main.py help
```

---

## Success Criteria

✅ **Publication Success**: `pip install mcp-commons` works from any environment  
✅ **Server Integration**: Both servers deploy via mcpmanager without absolute paths  
✅ **Functionality**: All 23 jira-helper tools + 6 worldcontext tools register correctly  
✅ **Testing**: All test suites pass with PyPI-installed library  
✅ **Documentation**: Professional package with clear usage examples  
✅ **Performance**: No regression in tool registration performance  

---

## Current Status (Based on Terminal Session)

✅ **MCP Consolidation Complete**: Successfully consolidated both servers  
✅ **Local Testing**: All tests passing (62/62 for jira-helper)  
✅ **pipx Deployment**: Both servers deploy successfully via mcpmanager  
✅ **Functionality Verified**: 23 jira-helper tools registering via mcp-commons  
✅ **Integration Working**: worldcontext also using mcp-commons successfully  

**Next Step**: Execute this checklist to get mcp-commons published to PyPI and eliminate absolute path dependencies completely.
