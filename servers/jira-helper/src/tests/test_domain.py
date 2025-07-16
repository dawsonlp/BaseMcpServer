"""
Domain Layer Tests.

Tests for pure business logic without external dependencies.
All ports/interfaces are mocked to test domain logic in isolation.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from domain.base import BaseResult, FieldValidator
from domain.exceptions import (
    JiraDomainException,
    JiraInstanceNotFound,
    JiraValidationError,
)
from domain.models import (
    CustomFieldMapping,
    IssueCreateRequest,
    IssueTransitionRequest,
    JiraComment,
    JiraInstance,
    JiraIssue,
    JiraProject,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
    WorkflowTransition,
)
from domain.services import (
    IssueService,
    ProjectService,
    WorkflowService,
)


class TestDomainModels:
    """Test domain models and their validation."""

    def test_jira_issue_creation(self):
        """Test JiraIssue model creation and validation."""
        issue = JiraIssue(
            key="TEST-123",
            id="12345",
            summary="Test issue",
            description="Test description",
            status="Open",
            issue_type="Story",
            priority="Medium",
            assignee="john.doe",
            reporter="jane.doe",
            created="2024-01-01T10:00:00Z",
            updated="2024-01-01T11:00:00Z",
            components=["Backend"],
            labels=["bug", "urgent"],
            url="https://test.atlassian.net/browse/TEST-123"
        )

        assert issue.key == "TEST-123"
        assert issue.summary == "Test issue"
        assert issue.status == "Open"
        assert "bug" in issue.labels

    def test_jira_project_creation(self):
        """Test JiraProject model creation."""
        project = JiraProject(
            key="TEST",
            name="Test Project",
            id="10001",
            lead_name="John Doe",
            lead_email="john@example.com",
            url="https://test.atlassian.net/projects/TEST"
        )

        assert project.key == "TEST"
        assert project.name == "Test Project"
        assert project.lead_name == "John Doe"

    def test_issue_create_request_validation(self):
        """Test IssueCreateRequest validation."""
        # Valid request
        request = IssueCreateRequest(
            project_key="TEST",
            summary="Test issue",
            description="Test description",
            issue_type="Story",
            priority="Medium",
            assignee="john.doe",
            labels=["test"]
        )

        assert request.project_key == "TEST"
        assert request.summary == "Test issue"

    def test_workflow_transition_model(self):
        """Test WorkflowTransition model."""
        transition = WorkflowTransition(
            id="11",
            name="Start Progress",
            to_status="In Progress"
        )

        assert transition.id == "11"
        assert transition.name == "Start Progress"
        assert transition.to_status == "In Progress"

    def test_jira_comment_model(self):
        """Test JiraComment model."""
        comment = JiraComment(
            id="10001",
            author_name="John Doe",
            author_key="john.doe",
            body="This is a test comment",
            created="2024-01-01T10:00:00Z",
            updated="2024-01-01T10:00:00Z"
        )

        assert comment.id == "10001"
        assert comment.author_name == "John Doe"
        assert comment.body == "This is a test comment"


class TestDomainExceptions:
    """Test domain-specific exceptions."""

    def test_jira_validation_error(self):
        """Test JiraValidationError exception."""
        with pytest.raises(JiraValidationError) as exc_info:
            raise JiraValidationError(["Invalid input"])

        assert "Invalid input" in str(exc_info.value)

    def test_jira_domain_exception(self):
        """Test JiraDomainException exception."""
        with pytest.raises(JiraDomainException) as exc_info:
            raise JiraDomainException("Jira domain error")

        assert str(exc_info.value) == "Jira domain error"

    def test_jira_instance_not_found(self):
        """Test JiraInstanceNotFound exception."""
        with pytest.raises(JiraInstanceNotFound) as exc_info:
            raise JiraInstanceNotFound("test_instance", ["prod", "staging"])

        assert "test_instance" in str(exc_info.value)
        assert "prod, staging" in str(exc_info.value)


class TestBaseResult:
    """Test BaseResult utility class."""

    def test_success_result(self):
        """Test successful BaseResult."""
        result = BaseResult.success({"key": "value"})

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_failure_result(self):
        """Test failure BaseResult."""
        result = BaseResult.failure("Something went wrong")

        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"

    def test_result_with_details(self):
        """Test BaseResult with details."""
        result = BaseResult.success(
            data={"key": "value"},
            details={"operation": "test"}
        )

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.details == {"operation": "test"}


class TestFieldValidator:
    """Test FieldValidator utility class."""

    def test_validate_required_fields_success(self):
        """Test successful required field validation."""
        data = {"name": "John", "email": "john@example.com"}

        # Should not raise exception
        FieldValidator.validate_required_fields(data, ["name", "email"])

    def test_validate_required_fields_missing(self):
        """Test required field validation with missing field."""
        data = {"name": "John"}

        with pytest.raises(JiraValidationError) as exc_info:
            FieldValidator.validate_required_fields(data, ["name", "email"])

        assert "email" in str(exc_info.value)

    def test_validate_required_fields_empty(self):
        """Test required field validation with empty field."""
        data = {"name": "", "email": "john@example.com"}

        with pytest.raises(JiraValidationError) as exc_info:
            FieldValidator.validate_required_fields(data, ["name", "email"])

        assert "name" in str(exc_info.value)


class TestDomainServices:
    """Test domain services with mocked dependencies."""

    @pytest.fixture
    def mock_jira_repository(self):
        """Mock JiraRepository for testing."""
        mock_repo = Mock()
        mock_repo.get_issue = AsyncMock()
        mock_repo.create_issue = AsyncMock()
        mock_repo.add_comment = AsyncMock()
        mock_repo.get_projects = AsyncMock()
        mock_repo.get_transitions = AsyncMock()
        mock_repo.transition_issue = AsyncMock()
        return mock_repo

    @pytest.fixture
    def mock_config_provider(self):
        """Mock ConfigurationProvider for testing."""
        mock_config = Mock()
        mock_config.get_instance_config = Mock()
        mock_config.get_default_instance = Mock()
        mock_config.get_all_instances = Mock()
        return mock_config

    @pytest.fixture
    def issue_service(self, mock_jira_repository, mock_config_provider):
        """Create IssueService with mocked dependencies."""
        return IssueService(
            jira_repository=mock_jira_repository,
            config_provider=mock_config_provider
        )

    @pytest.fixture
    def project_service(self, mock_jira_repository, mock_config_provider):
        """Create ProjectService with mocked dependencies."""
        return ProjectService(
            jira_repository=mock_jira_repository,
            config_provider=mock_config_provider
        )

    @pytest.fixture
    def workflow_service(self, mock_jira_repository, mock_config_provider):
        """Create WorkflowService with mocked dependencies."""
        return WorkflowService(
            jira_repository=mock_jira_repository,
            config_provider=mock_config_provider
        )

    @pytest.mark.asyncio
    async def test_issue_service_get_issue(self, issue_service, mock_jira_repository):
        """Test IssueService.get_issue method."""
        # Setup mock
        mock_issue = JiraIssue(
            key="TEST-123",
            id="12345",
            summary="Test issue",
            description="Test description",
            status="Open",
            issue_type="Story",
            priority="Medium",
            assignee="john.doe",
            reporter="jane.doe",
            created="2024-01-01T10:00:00Z",
            updated="2024-01-01T11:00:00Z",
            components=[],
            labels=[],
            url="https://test.atlassian.net/browse/TEST-123"
        )
        mock_jira_repository.get_issue.return_value = mock_issue

        # Execute
        result = await issue_service.get_issue("TEST-123", "default")

        # Verify
        assert result == mock_issue
        mock_jira_repository.get_issue.assert_called_once_with("TEST-123", "default")

    @pytest.mark.asyncio
    async def test_issue_service_create_issue(self, issue_service, mock_jira_repository):
        """Test IssueService.create_issue method."""
        # Setup mock
        mock_created_issue = JiraIssue(
            key="TEST-124",
            id="12346",
            summary="New test issue",
            description="New test description",
            status="Open",
            issue_type="Story",
            priority="Medium",
            assignee=None,
            reporter="jane.doe",
            created="2024-01-01T12:00:00Z",
            updated="2024-01-01T12:00:00Z",
            components=[],
            labels=["test"],
            url="https://test.atlassian.net/browse/TEST-124"
        )
        mock_jira_repository.create_issue.return_value = mock_created_issue

        # Create request
        request = IssueCreateRequest(
            project_key="TEST",
            summary="New test issue",
            description="New test description",
            issue_type="Story",
            priority="Medium",
            assignee=None,
            labels=["test"]
        )

        # Execute
        result = await issue_service.create_issue(request, "default")

        # Verify
        assert result == mock_created_issue
        mock_jira_repository.create_issue.assert_called_once_with(request, "default")

    @pytest.mark.asyncio
    async def test_project_service_get_projects(self, project_service, mock_jira_repository):
        """Test ProjectService.get_projects method."""
        # Setup mock
        mock_projects = [
            JiraProject(
                key="TEST1",
                name="Test Project 1",
                id="10001",
                lead_name="John Doe",
                lead_email="john@example.com",
                url="https://test.atlassian.net/projects/TEST1"
            ),
            JiraProject(
                key="TEST2",
                name="Test Project 2",
                id="10002",
                lead_name="Jane Doe",
                lead_email="jane@example.com",
                url="https://test.atlassian.net/projects/TEST2"
            )
        ]
        mock_jira_repository.get_projects.return_value = mock_projects

        # Execute
        result = await project_service.get_projects("default")

        # Verify
        assert len(result) == 2
        assert result[0].key == "TEST1"
        assert result[1].key == "TEST2"
        mock_jira_repository.get_projects.assert_called_once_with("default")

    @pytest.mark.asyncio
    async def test_workflow_service_get_transitions(self, workflow_service, mock_jira_repository):
        """Test WorkflowService.get_available_transitions method."""
        # Setup mock
        mock_transitions = [
            WorkflowTransition(id="11", name="Start Progress", to_status="In Progress"),
            WorkflowTransition(id="21", name="Done", to_status="Done")
        ]
        mock_jira_repository.get_transitions.return_value = mock_transitions

        # Execute
        result = await workflow_service.get_available_transitions("TEST-123", "default")

        # Verify
        assert len(result) == 2
        assert result[0].name == "Start Progress"
        assert result[1].name == "Done"
        mock_jira_repository.get_transitions.assert_called_once_with("TEST-123", "default")

    @pytest.mark.asyncio
    async def test_workflow_service_transition_issue(self, workflow_service, mock_jira_repository):
        """Test WorkflowService.transition_issue method."""
        # Setup mock
        mock_updated_issue = JiraIssue(
            key="TEST-123",
            id="12345",
            summary="Test issue",
            description="Test description",
            status="In Progress",  # Status changed
            issue_type="Story",
            priority="Medium",
            assignee="john.doe",
            reporter="jane.doe",
            created="2024-01-01T10:00:00Z",
            updated="2024-01-01T13:00:00Z",  # Updated time changed
            components=[],
            labels=[],
            url="https://test.atlassian.net/browse/TEST-123"
        )
        mock_jira_repository.transition_issue.return_value = mock_updated_issue

        # Create request
        request = IssueTransitionRequest(
            issue_key="TEST-123",
            transition_name="Start Progress",
            comment="Starting work on this issue"
        )

        # Execute
        result = await workflow_service.transition_issue(request, "default")

        # Verify
        assert result == mock_updated_issue
        assert result.status == "In Progress"
        mock_jira_repository.transition_issue.assert_called_once_with(request, "default")


class TestDomainServiceErrorHandling:
    """Test domain service error handling."""

    @pytest.fixture
    def failing_jira_repository(self):
        """Mock JiraRepository that raises exceptions."""
        mock_repo = Mock()
        mock_repo.get_issue = AsyncMock(side_effect=JiraDomainException("API Error"))
        mock_repo.create_issue = AsyncMock(side_effect=JiraDomainException("Creation failed"))
        return mock_repo

    @pytest.fixture
    def failing_issue_service(self, failing_jira_repository):
        """Create IssueService with failing repository."""
        mock_config = Mock()
        return IssueService(
            jira_repository=failing_jira_repository,
            config_provider=mock_config
        )

    @pytest.mark.asyncio
    async def test_issue_service_handles_jira_error(self, failing_issue_service):
        """Test that IssueService properly handles JiraDomainException exceptions."""
        with pytest.raises(JiraDomainException) as exc_info:
            await failing_issue_service.get_issue("TEST-123", "default")

        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_issue_service_handles_creation_error(self, failing_issue_service):
        """Test that IssueService properly handles creation errors."""
        request = IssueCreateRequest(
            project_key="TEST",
            summary="Test issue",
            description="Test description",
            issue_type="Story"
        )

        with pytest.raises(JiraDomainException) as exc_info:
            await failing_issue_service.create_issue(request, "default")

        assert "Creation failed" in str(exc_info.value)


class TestDomainBusinessLogic:
    """Test complex domain business logic."""

    def test_workflow_graph_creation(self):
        """Test WorkflowGraph domain model."""
        nodes = [
            WorkflowNode(id="1", name="Open", status_category="new"),
            WorkflowNode(id="2", name="In Progress", status_category="indeterminate"),
            WorkflowNode(id="3", name="Done", status_category="done")
        ]

        edges = [
            WorkflowEdge(from_node="1", to_node="2", transition_name="Start Progress"),
            WorkflowEdge(from_node="2", to_node="3", transition_name="Done")
        ]

        graph = WorkflowGraph(
            project_key="TEST",
            issue_type="Story",
            nodes=nodes,
            edges=edges
        )

        assert graph.project_key == "TEST"
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2
        assert graph.nodes[0].name == "Open"
        assert graph.edges[0].transition_name == "Start Progress"

    def test_custom_field_mapping(self):
        """Test CustomFieldMapping domain model."""
        mapping = CustomFieldMapping(
            field_id="customfield_10001",
            field_name="Story Points",
            field_type="number",
            description="Estimation in story points"
        )

        assert mapping.field_id == "customfield_10001"
        assert mapping.field_name == "Story Points"
        assert mapping.field_type == "number"

    def test_jira_instance_configuration(self):
        """Test JiraInstance domain model."""
        instance = JiraInstance(
            name="production",
            url="https://company.atlassian.net",
            user="api.user@company.com",
            description="Production Jira instance",
            is_default=True
        )

        assert instance.name == "production"
        assert instance.url == "https://company.atlassian.net"
        assert instance.is_default is True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
