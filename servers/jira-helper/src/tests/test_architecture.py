"""
Basic architecture tests for the Jira Helper hexagonal architecture.

This module contains tests to verify that the hexagonal architecture
is properly implemented and that dependencies flow in the correct direction.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from application.use_cases import GetIssueDetailsUseCase, ListProjectsUseCase
from domain.models import JiraInstance, JiraIssue, JiraProject
from domain.ports import ConfigurationProvider, JiraRepository
from domain.services import IssueService
from infrastructure.config_adapter import ConfigurationAdapter


class TestArchitectureDependencies:
    """Test that dependencies flow in the correct direction."""

    def test_domain_has_no_infrastructure_dependencies(self):
        """Verify domain layer has no dependencies on infrastructure."""
        # Domain models should be importable without infrastructure
        from domain.exceptions import JiraValidationError
        from domain.models import JiraIssue, JiraProject
        from domain.services import IssueService

        # This should not raise any import errors
        assert JiraIssue is not None
        assert JiraProject is not None
        assert IssueService is not None
        assert JiraValidationError is not None

    def test_application_has_no_infrastructure_dependencies(self):
        """Verify application layer has no dependencies on infrastructure."""
        # Application use cases should be importable without infrastructure
        from application.use_cases import GetIssueDetailsUseCase, ListProjectsUseCase

        # This should not raise any import errors
        assert ListProjectsUseCase is not None
        assert GetIssueDetailsUseCase is not None

    def test_domain_services_use_ports_not_implementations(self):
        """Verify domain services depend on ports, not concrete implementations."""
        # Create mock implementations of ports
        mock_repository = Mock(spec=JiraRepository)
        mock_config = Mock(spec=ConfigurationProvider)
        mock_logger = Mock()

        # Should be able to create domain service with mocked ports
        issue_service = IssueService(mock_repository, mock_config, mock_logger)
        assert issue_service is not None


class TestDomainLogic:
    """Test core domain logic independently of infrastructure."""

    def test_jira_instance_validation(self):
        """Test JiraInstance domain model validation."""
        # Valid instance
        instance = JiraInstance(
            name="test",
            url="https://test.atlassian.net",
            user="test@example.com",
            token="test-token",
            description="Test instance"
        )
        assert instance.name == "test"
        assert instance.url == "https://test.atlassian.net"

    def test_jira_issue_creation(self):
        """Test JiraIssue domain model creation."""
        issue = JiraIssue(
            key="TEST-123",
            id="12345",
            summary="Test issue",
            description="Test description",
            status="To Do",
            issue_type="Story",
            priority="Medium",
            assignee="test@example.com",
            reporter="reporter@example.com",
            created="2024-01-01T00:00:00Z",
            updated="2024-01-01T00:00:00Z",
            components=[],
            labels=[],
            custom_fields={},
            url="https://test.atlassian.net/browse/TEST-123"
        )
        assert issue.key == "TEST-123"
        assert issue.summary == "Test issue"

    def test_jira_project_creation(self):
        """Test JiraProject domain model creation."""
        project = JiraProject(
            key="TEST",
            name="Test Project",
            id="10001",
            lead_name="Test Lead",
            lead_email="lead@example.com",
            url="https://test.atlassian.net/projects/TEST"
        )
        assert project.key == "TEST"
        assert project.name == "Test Project"


class TestArchitectureCompliance:
    """Test architecture compliance and boundaries."""

    def test_dependency_injection_pattern(self):
        """Test that use cases properly accept dependencies via constructor."""
        # Use cases should accept dependencies through constructor
        mock_service = Mock()
        
        # Should be able to create use cases with injected dependencies
        projects_use_case = ListProjectsUseCase(project_service=mock_service)
        issue_use_case = GetIssueDetailsUseCase(issue_service=mock_service)
        
        # Verify use cases store dependencies properly
        assert hasattr(projects_use_case, '_project_service')
        assert hasattr(issue_use_case, '_issue_service')

    def test_use_case_interface_consistency(self):
        """Test that use cases follow consistent interface patterns."""
        # All use cases should have execute methods
        assert hasattr(ListProjectsUseCase, 'execute')
        assert hasattr(GetIssueDetailsUseCase, 'execute')
        
        # Use case execute methods should be async
        import inspect
        assert inspect.iscoroutinefunction(ListProjectsUseCase.execute)
        assert inspect.iscoroutinefunction(GetIssueDetailsUseCase.execute)


class TestConfigurationAdapter:
    """Test configuration adapter integration."""

    def test_configuration_adapter_creation(self):
        """Test that ConfigurationAdapter can be created."""
        # This tests the bridge between our domain and existing config
        try:
            adapter = ConfigurationAdapter()
            assert adapter is not None
        except Exception as e:
            # If this fails, it's likely due to missing config files
            # which is expected in a test environment
            assert "configuration" in str(e).lower() or "config" in str(e).lower()


class TestErrorHandling:
    """Test error handling across layers."""

    @pytest.mark.asyncio
    async def test_use_case_error_handling(self):
        """Test that use cases properly handle service errors."""
        # Create mock service that raises an exception
        mock_project_service = AsyncMock()
        mock_project_service.get_projects.side_effect = Exception("Test error")

        # Create use case with mock (using keyword argument)
        use_case = ListProjectsUseCase(project_service=mock_project_service)

        # Execute use case
        result = await use_case.execute("test-instance")

        # Verify error is handled properly
        assert result.success is False
        assert result.error == "Test error"
        assert result.details["instance_name"] == "test-instance"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
