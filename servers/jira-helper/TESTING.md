# Testing Guide for Jira Helper MCP Server

This document describes the comprehensive testing approach implemented for the hexagonal architecture.

## 🧪 Testing Philosophy

The hexagonal architecture enables **independent testing at each layer**, ensuring:
- **Domain logic** can be tested without external dependencies
- **Use cases** can be tested with mocked services
- **Infrastructure** can be tested with real or mock external systems
- **Integration** tests verify complete workflows

## 📁 Test Structure

```
src/tests/
├── __init__.py                 # Test configuration
├── test_domain.py             # Domain layer tests (pure business logic)
├── test_use_cases.py          # Application layer tests (use cases)
└── test_integration.py        # Infrastructure & integration tests
```

## 🏗️ Testing Layers

### 1. Domain Layer Tests (`test_domain.py`)

**Purpose**: Test pure business logic without external dependencies

**Characteristics**:
- ✅ No external API calls
- ✅ No file system access
- ✅ No network dependencies
- ✅ Fast execution (< 1ms per test)
- ✅ Property-based testing for complex logic

**Example**:
```python
class TestJiraIssueModel:
    def test_issue_creation_with_valid_data(self):
        """Test creating a JiraIssue with valid data."""
        issue = JiraIssue(
            key="TEST-123",
            summary="Test issue",
            status="Open",
            # ... other required fields
        )
        assert issue.key == "TEST-123"
        assert issue.is_valid()
    
    def test_issue_validation_failures(self):
        """Test issue validation with invalid data."""
        with pytest.raises(JiraValidationError):
            JiraIssue(key="", summary="Test")  # Empty key should fail
```

**Coverage**:
- Domain model validation
- Business rule enforcement
- Data transformation logic
- Exception handling

### 2. Application Layer Tests (`test_use_cases.py`)

**Purpose**: Test use case orchestration and application services

**Characteristics**:
- ✅ Mock all external dependencies
- ✅ Test complete workflows
- ✅ Test error handling scenarios
- ✅ Test validation logic
- ✅ Fast execution with mocked services

**Example**:
```python
class TestGetIssueDetailsUseCase:
    @pytest.fixture
    def mock_issue_service(self):
        mock = Mock()
        mock.get_issue = AsyncMock(return_value=sample_jira_issue)
        return mock
    
    @pytest.mark.asyncio
    async def test_successful_issue_retrieval(self, mock_issue_service):
        """Test successful issue details retrieval."""
        use_case = GetIssueDetailsUseCase(issue_service=mock_issue_service)
        
        result = await use_case.execute("TEST-123", "production")
        
        assert result.success is True
        assert result.data["issue"]["key"] == "TEST-123"
        mock_issue_service.get_issue.assert_called_once_with("TEST-123", "production")
```

**Coverage**:
- Use case execution paths
- Error handling and recovery
- Input validation
- Result transformation
- Service orchestration

### 3. Infrastructure Layer Tests (`test_integration.py`)

**Purpose**: Test external system integration and infrastructure components

**Characteristics**:
- ✅ Test with real or mock external systems
- ✅ Test configuration loading
- ✅ Test API client behavior
- ✅ Test error scenarios (network failures, auth errors)
- ✅ Performance and concurrency testing

**Example**:
```python
class TestJiraApiRepository:
    @pytest.fixture
    def mock_jira_client(self):
        client = Mock()
        client.issue.return_value = mock_jira_issue_response
        return client
    
    @pytest.mark.asyncio
    async def test_get_issue_integration(self, jira_repository, mock_jira_client):
        """Test issue retrieval through Jira API."""
        result = await jira_repository.get_issue("TEST-123", "production")
        
        assert isinstance(result, JiraIssue)
        assert result.key == "TEST-123"
        mock_jira_client.issue.assert_called_once_with("TEST-123")
```

**Coverage**:
- API client integration
- Configuration management
- External service communication
- Error handling and retries
- Performance characteristics

## 🚀 Running Tests

### Quick Test Execution
```bash
# Run all tests
python run_tests.py

# Run specific test file
python run_tests.py test_domain.py
python run_tests.py test_use_cases.py
python run_tests.py test_integration.py

# Run with verbose output
python run_tests.py -v

# Run with coverage
python run_tests.py --cov=src --cov-report=html
```

### Test Categories

#### Fast Tests (Domain + Use Cases)
```bash
python -m pytest src/tests/test_domain.py src/tests/test_use_cases.py -v
```
- **Execution time**: < 1 second
- **Dependencies**: None (all mocked)
- **Use case**: Development feedback loop

#### Integration Tests
```bash
python -m pytest src/tests/test_integration.py -v
```
- **Execution time**: 5-10 seconds
- **Dependencies**: Mock external services
- **Use case**: Pre-commit validation

#### End-to-End Tests
```bash
python test_hexagonal_completion.py
```
- **Execution time**: 2-3 seconds
- **Dependencies**: Full system integration
- **Use case**: Deployment validation

## 🎯 Test Patterns

### 1. BaseUseCase Testing Pattern

All use cases follow the same testing pattern:

```python
class TestSomeUseCase:
    @pytest.fixture
    def mock_service(self):
        """Mock the required service dependency."""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_service):
        """Create use case with mocked dependencies."""
        return SomeUseCase(service=mock_service)
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, use_case, mock_service):
        """Test successful use case execution."""
        # Setup
        mock_service.some_method.return_value = expected_result
        
        # Execute
        result = await use_case.execute(input_params)
        
        # Verify
        assert result.success is True
        assert result.data == expected_data
        mock_service.some_method.assert_called_once_with(input_params)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, use_case, mock_service):
        """Test use case error handling."""
        # Setup
        mock_service.some_method.side_effect = SomeException("Error")
        
        # Execute
        result = await use_case.execute(input_params)
        
        # Verify
        assert result.success is False
        assert "Error" in result.error
```

### 2. Repository Testing Pattern

Infrastructure repositories use this pattern:

```python
class TestSomeRepository:
    @pytest.fixture
    def mock_client(self):
        """Mock external client."""
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_client):
        """Create repository with mocked client."""
        return SomeRepository(client=mock_client)
    
    @pytest.mark.asyncio
    async def test_successful_operation(self, repository, mock_client):
        """Test successful repository operation."""
        # Setup mock response
        mock_client.api_call.return_value = mock_response
        
        # Execute
        result = await repository.some_operation(params)
        
        # Verify
        assert isinstance(result, ExpectedModel)
        assert result.property == expected_value
        mock_client.api_call.assert_called_once_with(expected_params)
```

### 3. Error Handling Testing

Comprehensive error testing across all layers:

```python
def test_domain_validation_errors(self):
    """Test domain model validation."""
    with pytest.raises(JiraValidationError) as exc_info:
        JiraIssue(key="", summary="Test")
    
    assert "key" in str(exc_info.value)

@pytest.mark.asyncio
async def test_use_case_error_propagation(self, use_case, mock_service):
    """Test error propagation in use cases."""
    mock_service.method.side_effect = JiraDomainException("API Error")
    
    result = await use_case.execute("input")
    
    assert result.success is False
    assert "API Error" in result.error

@pytest.mark.asyncio
async def test_infrastructure_error_handling(self, repository, mock_client):
    """Test infrastructure error handling."""
    mock_client.api_call.side_effect = ConnectionError("Network error")
    
    with pytest.raises(JiraConnectionError):
        await repository.operation("input")
```

## 📊 Test Coverage Goals

### Coverage Targets
- **Domain Layer**: 95%+ (pure business logic)
- **Application Layer**: 90%+ (use cases and services)
- **Infrastructure Layer**: 80%+ (external integrations)
- **Overall Project**: 85%+

### Coverage Verification
```bash
# Generate coverage report
python run_tests.py --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## 🔄 Continuous Integration

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI Pipeline Tests
```yaml
# Example GitHub Actions workflow
- name: Run Fast Tests
  run: python -m pytest src/tests/test_domain.py src/tests/test_use_cases.py -v

- name: Run Integration Tests
  run: python -m pytest src/tests/test_integration.py -v

- name: Run Architecture Validation
  run: python test_hexagonal_completion.py
```

## 🧩 Test Utilities

### Mock Factories
```python
# src/tests/factories.py
def create_mock_jira_issue(**overrides):
    """Create a mock JiraIssue for testing."""
    defaults = {
        "key": "TEST-123",
        "summary": "Test issue",
        "status": "Open",
        # ... other defaults
    }
    defaults.update(overrides)
    return JiraIssue(**defaults)
```

### Test Fixtures
```python
# src/tests/conftest.py
@pytest.fixture
def sample_jira_issue():
    """Standard test issue."""
    return create_mock_jira_issue()

@pytest.fixture
def mock_jira_client():
    """Mock Jira API client."""
    client = Mock()
    # Setup common mock responses
    return client
```

## 🎯 Testing Best Practices

### 1. Test Independence
- Each test should be completely independent
- No shared state between tests
- Use fresh mocks for each test

### 2. Clear Test Names
```python
def test_get_issue_details_with_valid_key_returns_issue_data(self):
    """Test name describes: input, action, expected outcome."""
    pass

def test_create_issue_with_missing_summary_raises_validation_error(self):
    """Clear description of the test scenario."""
    pass
```

### 3. Arrange-Act-Assert Pattern
```python
def test_something(self):
    # Arrange: Set up test data and mocks
    mock_service.method.return_value = expected_result
    
    # Act: Execute the code under test
    result = use_case.execute(input_data)
    
    # Assert: Verify the outcome
    assert result.success is True
    assert result.data == expected_data
```

### 4. Test Data Management
- Use factories for creating test data
- Keep test data minimal and focused
- Use meaningful test data that reflects real scenarios

### 5. Mock Strategy
- Mock at the boundary of your system under test
- Don't mock what you don't own (use adapters)
- Verify interactions with mocks when behavior matters

## 🚨 Common Testing Pitfalls

### ❌ Avoid These Patterns
```python
# DON'T: Test implementation details
def test_internal_method_called(self):
    use_case._internal_method.assert_called_once()  # ❌

# DON'T: Overly complex test setup
def test_with_complex_setup(self):
    # 50 lines of setup code...  # ❌

# DON'T: Multiple assertions testing different things
def test_everything_at_once(self):
    assert result.success is True
    assert result.data.count == 5
    assert mock.called
    assert other_thing.happened  # ❌
```

### ✅ Prefer These Patterns
```python
# DO: Test behavior and outcomes
def test_successful_issue_creation_returns_issue_key(self):
    result = use_case.execute(valid_input)
    assert result.success is True
    assert result.data["key"].startswith("TEST-")  # ✅

# DO: Simple, focused tests
def test_single_concern(self):
    result = use_case.execute(input)
    assert result.success is True  # ✅

# DO: One assertion per test (when possible)
def test_returns_success_status(self):
    result = use_case.execute(input)
    assert result.success is True  # ✅

def test_returns_expected_data_structure(self):
    result = use_case.execute(input)
    assert "issue" in result.data  # ✅
```

## 📈 Performance Testing

### Load Testing
```python
@pytest.mark.asyncio
async def test_concurrent_issue_retrieval(self):
    """Test concurrent issue retrieval performance."""
    tasks = [
        use_case.execute(f"TEST-{i}", "production")
        for i in range(100)
    ]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    assert all(result.success for result in results)
    assert end_time - start_time < 5.0  # Should complete in < 5 seconds
```

### Memory Testing
```python
def test_memory_usage_within_limits(self):
    """Test memory usage stays within acceptable limits."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operation
    for i in range(1000):
        result = use_case.execute(f"TEST-{i}")
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Should not increase by more than 100MB
    assert memory_increase < 100 * 1024 * 1024
```

## 🔍 Debugging Tests

### Test Debugging Tips
```python
# Use pytest's built-in debugging
def test_something(self):
    import pdb; pdb.set_trace()  # Debugger breakpoint
    result = use_case.execute(input)
    assert result.success is True

# Verbose assertion messages
def test_with_helpful_messages(self):
    result = use_case.execute(input)
    assert result.success is True, f"Expected success but got error: {result.error}"

# Print debugging (remove before commit)
def test_with_debug_output(self):
    result = use_case.execute(input)
    print(f"Result: {result}")  # Temporary debugging
    assert result.success is True
```

### Test Isolation Issues
```bash
# Run single test
python -m pytest src/tests/test_domain.py::TestJiraIssue::test_creation -v

# Run with fresh Python environment
python -m pytest --forked src/tests/test_domain.py

# Clear pytest cache
python -m pytest --cache-clear
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Hexagonal Architecture Testing Patterns](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design Testing](https://martinfowler.com/articles/practical-test-pyramid.html)

---

**This testing approach ensures reliable, maintainable code with comprehensive coverage across all architectural layers.**
