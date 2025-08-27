"""
Use Case Tests - Focused Edition.

Tests for core application layer functionality.
Focuses on business rules, validation, and error handling.
Mock orchestration tests removed for improved agility.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from application.base_use_case import BaseUseCase, UseCaseResult
from application.services import ValidationService
from domain.exceptions import JiraDomainException, JiraValidationError


class TestBaseUseCase:
    """Test BaseUseCase core functionality."""

    @pytest.fixture
    def mock_service(self):
        """Mock service for testing."""
        mock = Mock()
        mock.get_data = AsyncMock(return_value="test_data")
        mock.process_data = AsyncMock(return_value="processed_data")
        return mock

    @pytest.fixture
    def base_use_case(self, mock_service):
        """Create BaseUseCase with mock service."""
        return BaseUseCase(service=mock_service)

    @pytest.mark.asyncio
    async def test_execute_simple_success(self, base_use_case, mock_service):
        """Test successful execution with proper result structure."""
        result = await base_use_case.execute_simple(
            lambda: mock_service.get_data(),
            operation_name="test_operation"
        )

        assert result.success is True
        assert result.data == "test_data"
        assert result.error is None
        assert result.details["operation_name"] == "test_operation"

    @pytest.mark.asyncio
    async def test_execute_simple_error_handling(self, base_use_case, mock_service):
        """Test error handling preserves error information."""
        mock_service.get_data.side_effect = Exception("Test error")

        result = await base_use_case.execute_simple(
            lambda: mock_service.get_data(),
            operation_name="test_operation"
        )

        assert result.success is False
        assert result.data is None
        assert result.error == "Test error"
        assert result.details["operation_name"] == "test_operation"

    @pytest.mark.asyncio
    async def test_execute_simple_jira_domain_error_handling(self, base_use_case, mock_service):
        """Test JiraDomainException handling preserves domain error context."""
        mock_service.get_data.side_effect = JiraDomainException("Domain error")

        result = await base_use_case.execute_simple(
            lambda: mock_service.get_data(),
            operation_name="domain_operation"
        )

        assert result.success is False
        assert result.data is None
        assert "Domain error" in result.error
        assert result.details["operation_name"] == "domain_operation"


class TestValidationService:
    """Test ValidationService basic validation rules."""

    def test_validate_issue_key_success(self):
        """Test basic issue key validation accepts reasonable inputs."""
        # Any non-empty strings should pass - let Jira validate format
        ValidationService.validate_issue_key("TEST-123")
        ValidationService.validate_issue_key("PROJECT-456")
        ValidationService.validate_issue_key("anything-goes")
        ValidationService.validate_issue_key("EVEN_UNDERSCORES")
        ValidationService.validate_issue_key("123-NUMBERS")

    def test_validate_issue_key_failures(self):
        """Test basic issue key validation rejects clearly invalid inputs."""
        # Only test basic sanity checks
        with pytest.raises(JiraValidationError):
            ValidationService.validate_issue_key("")  # Empty

        with pytest.raises(JiraValidationError):
            ValidationService.validate_issue_key("   ")  # Whitespace only

        with pytest.raises(JiraValidationError):
            ValidationService.validate_issue_key("x" * 101)  # Unreasonably long

    def test_validate_project_key_success(self):
        """Test basic project key validation accepts reasonable inputs."""
        # Any non-empty strings should pass - let Jira validate format
        ValidationService.validate_project_key("TEST")
        ValidationService.validate_project_key("PROJECT")
        ValidationService.validate_project_key("test")  # lowercase now OK
        ValidationService.validate_project_key("TEST123")  # numbers now OK
        ValidationService.validate_project_key("TEST_KEY")  # underscores now OK

    def test_validate_project_key_failures(self):
        """Test basic project key validation rejects clearly invalid inputs."""
        # Only test basic sanity checks
        with pytest.raises(JiraValidationError):
            ValidationService.validate_project_key("")  # Empty

        with pytest.raises(JiraValidationError):
            ValidationService.validate_project_key("   ")  # Whitespace only

        with pytest.raises(JiraValidationError):
            ValidationService.validate_project_key("x" * 51)  # Unreasonably long

    def test_validate_summary_success(self):
        """Test basic summary validation accepts reasonable inputs."""
        ValidationService.validate_summary("This is a valid summary")
        ValidationService.validate_summary("Short")  # No minimum length now
        ValidationService.validate_summary("x" * 999)  # Generous limit

    def test_validate_summary_failures(self):
        """Test basic summary validation rejects clearly invalid inputs."""
        # Only test basic sanity checks
        with pytest.raises(JiraValidationError):
            ValidationService.validate_summary("")  # Empty

        with pytest.raises(JiraValidationError):
            ValidationService.validate_summary("   ")  # Whitespace only

        with pytest.raises(JiraValidationError):
            ValidationService.validate_summary("x" * 1001)  # Unreasonably long


class TestUseCaseErrorHandling:
    """Test use case error handling patterns."""

    @pytest.fixture
    def failing_service(self):
        """Mock service that fails with different error types."""
        mock = Mock()
        mock.domain_error = AsyncMock(side_effect=JiraDomainException("Domain failure"))
        mock.validation_error = AsyncMock(side_effect=JiraValidationError(["Invalid data"]))
        mock.system_error = AsyncMock(side_effect=Exception("System failure"))
        return mock

    @pytest.fixture
    def error_use_case(self, failing_service):
        """Create use case with failing service."""
        return BaseUseCase(service=failing_service)

    @pytest.mark.asyncio
    async def test_handles_jira_domain_exception(self, error_use_case, failing_service):
        """Test JiraDomainException is properly handled and reported."""
        result = await error_use_case.execute_simple(
            lambda: failing_service.domain_error(),
            operation_name="domain_test"
        )

        assert result.success is False
        assert "Domain failure" in result.error
        assert result.data is None
        assert result.details["operation_name"] == "domain_test"

    @pytest.mark.asyncio
    async def test_handles_jira_validation_exception(self, error_use_case, failing_service):
        """Test JiraValidationError is properly handled and reported."""
        result = await error_use_case.execute_simple(
            lambda: failing_service.validation_error(),
            operation_name="validation_test"
        )

        assert result.success is False
        assert "Invalid data" in result.error
        assert result.data is None

    @pytest.mark.asyncio
    async def test_handles_system_exception(self, error_use_case, failing_service):
        """Test generic exceptions are properly handled."""
        result = await error_use_case.execute_simple(
            lambda: failing_service.system_error(),
            operation_name="system_test"
        )

        assert result.success is False
        assert "System failure" in result.error
        assert result.data is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
