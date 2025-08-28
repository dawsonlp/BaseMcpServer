"""
Tests for MCP Result Adapter

Tests the core adapter function that replaces all MCP wrapper boilerplate.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from mcp_commons import (
    create_mcp_adapter,
    validate_use_case_result
)
from mcp_commons.adapters import get_adapter_stats
from application.base_use_case import UseCaseResult


class TestCreateMcpAdapter:
    """Test the create_mcp_adapter function."""

    @pytest.mark.asyncio
    async def test_successful_use_case_result(self):
        """Test adapter with successful UseCaseResult."""
        # Create mock use case method
        mock_data = {"projects": [{"key": "TEST", "name": "Test Project"}], "count": 1}
        mock_result = UseCaseResult(success=True, data=mock_data, error=None, details={})

        mock_use_case = AsyncMock(return_value=mock_result)
        mock_use_case.__name__ = "test_use_case"
        mock_use_case.__doc__ = "Test use case"
        mock_use_case.__annotations__ = {"instance_name": str}

        # Create adapter
        adapted_method = create_mcp_adapter(mock_use_case)

        # Test execution
        result = await adapted_method(instance_name="test")

        # Verify result is the data directly (not wrapped in UseCaseResult)
        assert result == mock_data
        assert "projects" in result
        assert result["count"] == 1

        # Verify original method was called with correct args
        mock_use_case.assert_called_once_with(instance_name="test")

    @pytest.mark.asyncio
    async def test_failed_use_case_result(self):
        """Test adapter with failed UseCaseResult."""
        # Create mock failed result
        mock_result = UseCaseResult(
            success=False,
            data=None,
            error="Test error",
            details={"code": "TEST_ERROR"}
        )

        mock_use_case = AsyncMock(return_value=mock_result)
        mock_use_case.__name__ = "test_use_case"

        # Create adapter
        adapted_method = create_mcp_adapter(mock_use_case)

        # Test execution
        result = await adapted_method(test_param="value")

        # Verify error format
        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["details"]["code"] == "TEST_ERROR"

        mock_use_case.assert_called_once_with(test_param="value")

    @pytest.mark.asyncio
    async def test_non_use_case_result(self):
        """Test adapter with non-UseCaseResult return value."""
        # Create mock that returns dict directly
        mock_data = {"direct": "result"}
        mock_use_case = AsyncMock(return_value=mock_data)
        mock_use_case.__name__ = "test_use_case"

        # Create adapter
        adapted_method = create_mcp_adapter(mock_use_case)

        # Test execution
        result = await adapted_method()

        # Should return the data as-is
        assert result == mock_data
        assert result["direct"] == "result"

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test adapter handles exceptions properly."""
        # Create mock that raises exception
        mock_use_case = AsyncMock(side_effect=ValueError("Test exception"))
        mock_use_case.__name__ = "test_use_case"

        # Create adapter
        adapted_method = create_mcp_adapter(mock_use_case)

        # Test execution
        result = await adapted_method(param="value")

        # Verify error handling
        assert result["success"] is False
        assert "Unexpected error: Test exception" in result["error"]
        assert result["details"]["method"] == "test_use_case"
        assert result["details"]["parameters"]["param"] == "value"

    def test_metadata_preservation(self):
        """Test that function metadata is preserved."""
        # Create mock with metadata
        mock_use_case = AsyncMock()
        mock_use_case.__name__ = "original_name"
        mock_use_case.__doc__ = "Original docstring"
        mock_use_case.__annotations__ = {"param": str, "return": dict[str, Any]}

        # Create adapter
        adapted_method = create_mcp_adapter(mock_use_case)

        # Verify metadata preservation
        assert adapted_method.__name__ == "original_name"
        assert adapted_method.__doc__ == "Original docstring"
        assert adapted_method.__annotations__ == {"param": str, "return": dict[str, Any]}
        assert hasattr(adapted_method, '__signature__')


class TestValidateUseCaseResult:
    """Test the validate_use_case_result function."""

    def test_valid_use_case_result(self):
        """Test validation of valid UseCaseResult."""
        result = UseCaseResult(
            success=True,
            data={"test": "data"},
            error=None,
            details={"info": "test"}
        )

        assert validate_use_case_result(result) is True

    def test_invalid_type(self):
        """Test validation fails for non-UseCaseResult."""
        assert validate_use_case_result({"not": "use_case_result"}) is False
        assert validate_use_case_result("string") is False
        assert validate_use_case_result(None) is False

    def test_missing_attributes(self):
        """Test validation fails for missing attributes."""
        # Create mock object missing required attributes
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {}
        # Missing error and details attributes

        assert validate_use_case_result(mock_result) is False

    def test_invalid_attribute_types(self):
        """Test validation fails for invalid attribute types."""
        # Create UseCaseResult with invalid types
        result = UseCaseResult(
            success="not_boolean",  # Should be bool
            data={},
            error=123,  # Should be str or None
            details="not_dict"  # Should be dict
        )

        assert validate_use_case_result(result) is False


class TestGetAdapterStats:
    """Test the get_adapter_stats function."""

    def test_adapter_stats(self):
        """Test adapter statistics."""
        stats = get_adapter_stats()

        # mcp-commons returns AdapterStats dataclass, not dict
        assert hasattr(stats, 'version')
        assert hasattr(stats, 'boilerplate_lines_eliminated') 
        assert hasattr(stats, 'description')

        assert stats.boilerplate_lines_eliminated == 500
        assert "boilerplate" in stats.description.lower()


@pytest.mark.asyncio
async def test_integration_with_real_use_case_pattern():
    """Integration test with realistic use case pattern."""

    # Simulate a real use case execute method
    async def mock_list_projects_execute(instance_name: str = None) -> UseCaseResult:
        """Mock list projects use case."""
        if instance_name == "invalid":
            return UseCaseResult(
                success=False,
                data=None,
                error="Invalid instance",
                details={"instance_name": instance_name}
            )

        return UseCaseResult(
            success=True,
            data={
                "projects": [
                    {"key": "PROJ1", "name": "Project 1"},
                    {"key": "PROJ2", "name": "Project 2"}
                ],
                "count": 2,
                "instance": instance_name or "default"
            },
            error=None,
            details={"query_time": "0.1s"}
        )

    # Add metadata to mock
    mock_list_projects_execute.__name__ = "execute"
    mock_list_projects_execute.__doc__ = "Execute list projects use case"

    # Create adapter
    adapted_method = create_mcp_adapter(mock_list_projects_execute)

    # Test successful execution
    result = await adapted_method(instance_name="test")
    assert result["count"] == 2
    assert len(result["projects"]) == 2
    assert result["instance"] == "test"

    # Test failed execution
    error_result = await adapted_method(instance_name="invalid")
    assert error_result["success"] is False
    assert error_result["error"] == "Invalid instance"
    assert error_result["details"]["instance_name"] == "invalid"
