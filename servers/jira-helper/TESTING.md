# Testing Guide for Jira Helper

This document explains how to run tests for the Jira Helper hexagonal architecture.

## Prerequisites

Ensure you have the project's virtual environment set up and activated:

```bash
# Activate the project virtual environment
source .venv/bin/activate

# Verify pytest is installed
pip list | grep pytest
```

If pytest is not installed, install the testing dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

### Architecture Tests

Run the architecture validation tests to verify the hexagonal architecture is working correctly:

```bash
# Run architecture tests with verbose output
pytest src/tests/test_architecture.py -v

# Run all tests
pytest -v
```

### Test Categories

The architecture tests validate:

1. **Dependency Flow**: Ensures domain layer has no infrastructure dependencies
2. **Domain Logic**: Tests core business logic independently of frameworks
3. **Use Cases**: Tests application layer with mocked dependencies
4. **Error Handling**: Verifies proper error handling across layers
5. **Configuration**: Tests configuration adapter integration

### Expected Output

When tests pass, you should see output like:

```
============================================= test session starts ==============================================
platform darwin -- Python 3.13.5, pytest-8.4.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/ldawson/repos/BaseMcpServer/servers/jira-helper
configfile: pytest.ini
plugins: anyio-4.9.0, mock-3.14.1, asyncio-1.0.0
asyncio: mode=Mode.STRICT

src/tests/test_architecture.py::TestArchitectureDependencies::test_domain_has_no_infrastructure_dependencies PASSED [ 10%]
src/tests/test_architecture.py::TestArchitectureDependencies::test_application_has_no_infrastructure_dependencies PASSED [ 20%]
src/tests/test_architecture.py::TestArchitectureDependencies::test_domain_services_use_ports_not_implementations PASSED [ 30%]
src/tests/test_architecture.py::TestDomainLogic::test_jira_instance_validation PASSED [ 40%]
src/tests/test_architecture.py::TestDomainLogic::test_jira_issue_creation PASSED [ 50%]
src/tests/test_architecture.py::TestDomainLogic::test_jira_project_creation PASSED [ 60%]
src/tests/test_architecture.py::TestUseCasesWithMocks::test_list_projects_use_case PASSED [ 70%]
src/tests/test_architecture.py::TestUseCasesWithMocks::test_get_issue_details_use_case PASSED [ 80%]
src/tests/test_architecture.py::TestConfigurationAdapter::test_configuration_adapter_creation PASSED [ 90%]
src/tests/test_architecture.py::TestErrorHandling::test_use_case_error_handling PASSED [100%]

======================================== 10 passed, 1 warning in 0.05s =========================================
```

## Test Configuration

The project uses `pytest.ini` for test configuration:

- **Test Discovery**: Automatically finds tests in `src/tests/`
- **Async Support**: Configured for async/await testing
- **Verbose Output**: Shows detailed test results
- **Warning Suppression**: Filters out non-critical warnings

## Benefits of This Testing Approach

### 1. **Framework Independence**
Tests verify that core business logic can be tested without MCP framework dependencies.

### 2. **Clean Architecture Validation**
Tests ensure dependencies flow in the correct direction (domain → application → infrastructure → adapters).

### 3. **Mocked Dependencies**
Use cases are tested with mocked services, allowing fast, isolated testing.

### 4. **Error Handling Verification**
Tests confirm that errors are properly handled and propagated through all layers.

## Adding New Tests

When adding new functionality:

1. **Domain Tests**: Test pure business logic in isolation
2. **Use Case Tests**: Test application logic with mocked dependencies
3. **Integration Tests**: Test infrastructure adapters with real or containerized services

Example test structure:

```python
@pytest.mark.asyncio
async def test_new_use_case(self):
    """Test new use case with mocked dependencies."""
    # Arrange
    mock_service = AsyncMock()
    mock_service.method.return_value = expected_result
    use_case = NewUseCase(mock_service)
    
    # Act
    result = await use_case.execute(input_data)
    
    # Assert
    assert result.success is True
    assert result.data == expected_data
    mock_service.method.assert_called_once_with(input_data)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're in the project directory and virtual environment is activated
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Path Issues**: Tests should be run from the `servers/jira-helper` directory

### Debug Mode

Run tests with more verbose output for debugging:

```bash
pytest src/tests/test_architecture.py -v -s --tb=long
```

This approach follows Python testing best practices and keeps the testing setup simple and maintainable.
