"""
Use Case Tests.

Tests for application layer use cases and services.
Tests complete workflows and error handling scenarios.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from application.base_use_case import (
    BaseUseCase,
    UseCaseFactory,
    UseCaseResult,
)
from application.services import (
    JiraApplicationService,
    ValidationService,
)
from application.use_cases import (
    AddCommentUseCase,
    CreateIssueUseCase,
    GetIssueDetailsUseCase,
    GetIssueTransitionsUseCase,
    ListInstancesUseCase,
    ListProjectsUseCase,
    TransitionIssueUseCase,
)
from domain.exceptions import JiraDomainException, JiraValidationError
from domain.models import (
    JiraComment,
    JiraInstance,
    JiraIssue,
    JiraProject,
    WorkflowTransition,
)


class TestBaseUseCase:
    """Test BaseUseCase functionality."""

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
        """Test successful simple execution."""
        result = await base_use_case.execute_simple(
            lambda: mock_service.get_data(),
            operation="test_operation"
        )

        assert result.success is True
        assert result.data == "test_data"
        assert result.error is None
        assert result.details["operation"] == "test_operation"

    @pytest.mark.asyncio
    async def test_execute_simple_error(self, base_use_case, mock_service):
        """Test error handling in simple execution."""
        mock_service.get_data.side_effect = Exception("Test error")

        result = await base_use_case.execute_simple(
            lambda: mock_service.get_data(),
            operation="test_operation"
        )

        assert result.success is False
        assert result.data is None
        assert result.error == "Test error"
        assert result.details["operation"] == "test_operation"


class TestQueryUseCases:
    """Test query use cases (read operations)."""

    @pytest.fixture
    def mock_project_service(self):
        """Mock project service."""
        mock = Mock()
        mock.get_projects = AsyncMock()
        return mock

    @pytest.fixture
    def mock_issue_service(self):
        """Mock issue service."""
        mock = Mock()
        mock.get_issue = AsyncMock()
        mock.get_issue_with_comments = AsyncMock()
        mock.search_issues = AsyncMock()
        return mock

    @pytest.fixture
    def mock_workflow_service(self):
        """Mock workflow service."""
        mock = Mock()
        mock.get_available_transitions = AsyncMock()
        return mock

    @pytest.fixture
    def mock_instance_service(self):
        """Mock instance service."""
        mock = Mock()
        mock.get_instances = Mock()
        mock.get_default_instance = Mock()
        return mock

    @pytest.mark.asyncio
    async def test_list_projects_use_case(self, mock_project_service):
        """Test ListProjectsUseCase."""
        # Setup mock data
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
        mock_project_service.get_projects.return_value = mock_projects

        # Create use case
        use_case = ListProjectsUseCase(project_service=mock_project_service)

        # Execute
        result = await use_case.execute("test_instance")

        # Verify
        assert result.success is True
        assert result.data["count"] == 2
        assert len(result.data["projects"]) == 2
        assert result.data["projects"][0]["key"] == "TEST1"
        assert result.data["instance"] == "test_instance"
        mock_project_service.get_projects.assert_called_once_with("test_instance")

    @pytest.mark.asyncio
    async def test_get_issue_details_use_case(self, mock_issue_service):
        """Test GetIssueDetailsUseCase."""
        # Setup mock data
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
            components=["Backend"],
            labels=["bug"],
            url="https://test.atlassian.net/browse/TEST-123"
        )
        mock_issue_service.get_issue.return_value = mock_issue

        # Create use case
        use_case = GetIssueDetailsUseCase(issue_service=mock_issue_service)

        # Execute
        result = await use_case.execute("TEST-123", "test_instance")

        # Verify
        assert result.success is True
        assert result.data["issue"]["key"] == "TEST-123"
        assert result.data["issue"]["summary"] == "Test issue"
        assert result.data["instance"] == "test_instance"
        mock_issue_service.get_issue.assert_called_once_with("TEST-123", "test_instance")

    @pytest.mark.asyncio
    async def test_get_issue_transitions_use_case(self, mock_workflow_service):
        """Test GetIssueTransitionsUseCase."""
        # Setup mock data
        mock_transitions = [
            WorkflowTransition(id="11", name="Start Progress", to_status="In Progress"),
            WorkflowTransition(id="21", name="Done", to_status="Done")
        ]
        mock_workflow_service.get_available_transitions.return_value = mock_transitions

        # Create use case
        use_case = GetIssueTransitionsUseCase(workflow_service=mock_workflow_service)

        # Execute
        result = await use_case.execute("TEST-123", "test_instance")

        # Verify
        assert result.success is True
        assert result.data["issue_key"] == "TEST-123"
        assert result.data["transition_count"] == 2
        assert len(result.data["available_transitions"]) == 2
        assert result.data["available_transitions"][0]["name"] == "Start Progress"
        mock_workflow_service.get_available_transitions.assert_called_once_with("TEST-123", "test_instance")

    @pytest.mark.asyncio
    async def test_list_instances_use_case(self, mock_instance_service):
        """Test ListInstancesUseCase."""
        # Setup mock data
        mock_instances = [
            JiraInstance(
                name="production",
                url="https://company.atlassian.net",
                user="api.user@company.com",
                description="Production instance",
                is_default=True
            ),
            JiraInstance(
                name="staging",
                url="https://staging.atlassian.net",
                user="api.user@company.com",
                description="Staging instance",
                is_default=False
            )
        ]
        mock_default = mock_instances[0]

        mock_instance_service.get_instances.return_value = mock_instances
        mock_instance_service.get_default_instance.return_value = mock_default

        # Create use case
        use_case = ListInstancesUseCase(instance_service=mock_instance_service)

        # Execute
        result = await use_case.execute()

        # Verify
        assert result.success is True
        assert result.data["count"] == 2
        assert len(result.data["instances"]) == 2
        assert result.data["default_instance"] == "production"
        assert result.data["instances"][0]["is_default"] is True


class TestCommandUseCases:
    """Test command use cases (write operations)."""

    @pytest.fixture
    def mock_issue_service(self):
        """Mock issue service for commands."""
        mock = Mock()
        mock.create_issue = AsyncMock()
        mock.add_comment = AsyncMock()
        return mock

    @pytest.fixture
    def mock_workflow_service(self):
        """Mock workflow service for commands."""
        mock = Mock()
        mock.transition_issue = AsyncMock()
        mock.change_assignee = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_create_issue_use_case(self, mock_issue_service):
        """Test CreateIssueUseCase."""
        # Setup mock data
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
        mock_issue_service.create_issue.return_value = mock_created_issue

        # Create use case
        use_case = CreateIssueUseCase(issue_service=mock_issue_service)

        # Execute
        result = await use_case.execute(
            project_key="TEST",
            summary="New test issue",
            description="New test description",
            issue_type="Story",
            priority="Medium",
            labels=["test"],
            instance_name="test_instance"
        )

        # Verify
        assert result.success is True
        assert result.data["created"] is True
        assert result.data["key"] == "TEST-124"
        assert result.data["url"] == "https://test.atlassian.net/browse/TEST-124"

        # Verify service was called with correct request
        call_args = mock_issue_service.create_issue.call_args
        request = call_args[0][0]  # First positional argument
        instance = call_args[0][1]  # Second positional argument

        assert request.project_key == "TEST"
        assert request.summary == "New test issue"
        assert request.labels == ["test"]
        assert instance == "test_instance"

    @pytest.mark.asyncio
    async def test_add_comment_use_case(self, mock_issue_service):
        """Test AddCommentUseCase."""
        # Setup mock data
        mock_comment = JiraComment(
            id="10001",
            author_name="John Doe",
            author_key="john.doe",
            body="This is a test comment",
            created="2024-01-01T10:00:00Z",
            updated="2024-01-01T10:00:00Z"
        )
        mock_issue_service.add_comment.return_value = mock_comment

        # Create use case
        use_case = AddCommentUseCase(issue_service=mock_issue_service)

        # Execute
        result = await use_case.execute(
            issue_key="TEST-123",
            comment="This is a test comment",
            instance_name="test_instance"
        )

        # Verify
        assert result.success is True
        assert result.data["added"] is True
        assert result.data["issue_key"] == "TEST-123"
        assert result.data["comment_id"] == "10001"
        assert result.data["comment_body"] == "This is a test comment"

        # Verify service was called correctly
        call_args = mock_issue_service.add_comment.call_args
        request = call_args[0][0]
        instance = call_args[0][1]

        assert request.issue_key == "TEST-123"
        assert request.comment == "This is a test comment"
        assert instance == "test_instance"

    @pytest.mark.asyncio
    async def test_transition_issue_use_case(self, mock_workflow_service):
        """Test TransitionIssueUseCase."""
        # Setup mock data
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
            updated="2024-01-01T13:00:00Z",
            components=[],
            labels=[],
            url="https://test.atlassian.net/browse/TEST-123"
        )
        mock_workflow_service.transition_issue.return_value = mock_updated_issue

        # Create use case
        use_case = TransitionIssueUseCase(workflow_service=mock_workflow_service)

        # Execute
        result = await use_case.execute(
            issue_key="TEST-123",
            transition_name="Start Progress",
            comment="Starting work",
            instance_name="test_instance"
        )

        # Verify
        assert result.success is True
        assert result.data["success"] is True
        assert result.data["issue_key"] == "TEST-123"
        assert result.data["transition_executed"] == "Start Progress"
        assert result.data["new_status"] == "In Progress"
        assert result.data["comment_added"] is True

        # Verify service was called correctly
        call_args = mock_workflow_service.transition_issue.call_args
        request = call_args[0][0]
        instance = call_args[0][1]

        assert request.issue_key == "TEST-123"
        assert request.transition_name == "Start Progress"
        assert request.comment == "Starting work"
        assert instance == "test_instance"


class TestUseCaseErrorHandling:
    """Test use case error handling."""

    @pytest.fixture
    def failing_issue_service(self):
        """Mock issue service that fails."""
        mock = Mock()
        mock.get_issue = AsyncMock(side_effect=JiraDomainException("API Error"))
        mock.create_issue = AsyncMock(side_effect=JiraValidationError(["Invalid data"]))
        return mock

    @pytest.mark.asyncio
    async def test_query_use_case_handles_jira_error(self, failing_issue_service):
        """Test query use case handles JiraError."""
        use_case = GetIssueDetailsUseCase(issue_service=failing_issue_service)

        result = await use_case.execute("TEST-123", "test_instance")

        assert result.success is False
        assert "API Error" in result.error
        assert result.data is None
        assert result.details["issue_key"] == "TEST-123"

    @pytest.mark.asyncio
    async def test_command_use_case_handles_validation_error(self, failing_issue_service):
        """Test command use case handles ValidationError."""
        use_case = CreateIssueUseCase(issue_service=failing_issue_service)

        result = await use_case.execute(
            project_key="TEST",
            summary="Test",
            description="Test description"
        )

        assert result.success is False
        assert "Invalid data" in result.error
        assert result.data is None

    @pytest.mark.asyncio
    async def test_use_case_validates_required_params(self):
        """Test use case validates required parameters."""
        mock_service = Mock()
        use_case = GetIssueDetailsUseCase(issue_service=mock_service)

        # Test with empty issue key
        result = await use_case.execute("", "test_instance")

        assert result.success is False
        assert "required" in result.error.lower()


class TestUseCaseFactory:
    """Test UseCaseFactory dependency injection."""

    @pytest.fixture
    def mock_services(self):
        """Mock all services."""
        return {
            'issue_service': Mock(),
            'project_service': Mock(),
            'workflow_service': Mock(),
            'instance_service': Mock()
        }

    @pytest.fixture
    def use_case_factory(self, mock_services):
        """Create UseCaseFactory with mock services."""
        return UseCaseFactory(**mock_services)

    def test_factory_creates_use_cases(self, use_case_factory):
        """Test factory creates use cases with dependencies."""
        # Test creating different use case types
        list_projects = use_case_factory.create_use_case(ListProjectsUseCase)
        get_issue = use_case_factory.create_use_case(GetIssueDetailsUseCase)
        create_issue = use_case_factory.create_use_case(CreateIssueUseCase)

        # Verify instances are created
        assert isinstance(list_projects, ListProjectsUseCase)
        assert isinstance(get_issue, GetIssueDetailsUseCase)
        assert isinstance(create_issue, CreateIssueUseCase)

        # Verify dependencies are injected
        assert hasattr(list_projects, '_project_service')
        assert hasattr(get_issue, '_issue_service')
        assert hasattr(create_issue, '_issue_service')

    def test_factory_supports_additional_dependencies(self, use_case_factory):
        """Test factory supports additional dependencies."""
        custom_service = Mock()
        use_case_factory.add_dependency('custom_service', custom_service)

        # Create use case with additional dependency
        use_case = use_case_factory.create_use_case(
            BaseUseCase,
            custom_service=custom_service
        )

        assert hasattr(use_case, '_custom_service')
        assert use_case._custom_service == custom_service


class TestValidationService:
    """Test ValidationService."""

    def test_validate_issue_key_success(self):
        """Test successful issue key validation."""
        # Should not raise exception
        ValidationService.validate_issue_key("TEST-123")
        ValidationService.validate_issue_key("PROJECT-456")

    def test_validate_issue_key_failures(self):
        """Test issue key validation failures."""
        with pytest.raises(JiraValidationError):
            ValidationService.validate_issue_key("")

        with pytest.raises(JiraValidationError):
            ValidationService.validate_issue_key("INVALID")

        with pytest.raises(JiraValidationError):
            ValidationService.validate_issue_key("TEST-")

        with pytest.raises(JiraValidationError):
            ValidationService.validate_issue_key("123-TEST")

    def test_validate_project_key_success(self):
        """Test successful project key validation."""
        ValidationService.validate_project_key("TEST")
        ValidationService.validate_project_key("PROJECT")

    def test_validate_project_key_failures(self):
        """Test project key validation failures."""
        with pytest.raises(JiraValidationError):
            ValidationService.validate_project_key("")

        with pytest.raises(JiraValidationError):
            ValidationService.validate_project_key("T")  # Too short

        with pytest.raises(JiraValidationError):
            ValidationService.validate_project_key("TOOLONGPROJECT")  # Too long

        with pytest.raises(JiraValidationError):
            ValidationService.validate_project_key("TEST123")  # Contains numbers

    def test_validate_summary_success(self):
        """Test successful summary validation."""
        ValidationService.validate_summary("This is a valid summary")
        ValidationService.validate_summary("Short but valid")

    def test_validate_summary_failures(self):
        """Test summary validation failures."""
        with pytest.raises(JiraValidationError):
            ValidationService.validate_summary("")

        with pytest.raises(JiraValidationError):
            ValidationService.validate_summary("Too")  # Too short

        with pytest.raises(JiraValidationError):
            ValidationService.validate_summary("x" * 300)  # Too long


class TestJiraApplicationService:
    """Test JiraApplicationService orchestration."""

    @pytest.fixture
    def mock_use_case_factory(self):
        """Mock UseCaseFactory."""
        factory = Mock()
        factory.create_use_case = Mock()
        return factory

    @pytest.fixture
    def app_service(self, mock_use_case_factory):
        """Create JiraApplicationService."""
        return JiraApplicationService(mock_use_case_factory)

    @pytest.mark.asyncio
    async def test_create_issue_with_workflow_success(self, app_service, mock_use_case_factory):
        """Test successful issue creation workflow."""
        # Setup mocks
        mock_create_use_case = Mock()
        mock_create_result = UseCaseResult(
            success=True,
            data={"key": "TEST-123", "url": "https://test.atlassian.net/browse/TEST-123"},
            details={}
        )
        mock_create_use_case.execute = AsyncMock(return_value=mock_create_result)

        mock_comment_use_case = Mock()
        mock_comment_result = UseCaseResult(success=True, data={}, details={})
        mock_comment_use_case.execute = AsyncMock(return_value=mock_comment_result)

        # Configure factory to return mocks
        def create_use_case_side_effect(use_case_class):
            if use_case_class == CreateIssueUseCase:
                return mock_create_use_case
            elif use_case_class == AddCommentUseCase:
                return mock_comment_use_case
            return Mock()

        mock_use_case_factory.create_use_case.side_effect = create_use_case_side_effect

        # Execute workflow
        result = await app_service.create_issue_with_workflow(
            project_key="TEST",
            summary="Test issue",
            description="Test description",
            initial_comment="Initial comment",
            instance_name="test_instance"
        )

        # Verify
        assert result.success is True
        assert "Issue created: TEST-123" in result.steps_completed
        assert "Initial comment added" in result.steps_completed
        assert len(result.errors) == 0
        assert result.final_result == mock_create_result

    @pytest.mark.asyncio
    async def test_create_issue_with_workflow_failure(self, app_service, mock_use_case_factory):
        """Test issue creation workflow with failure."""
        # Setup failing mock
        mock_create_use_case = Mock()
        mock_create_result = UseCaseResult(
            success=False,
            error="Creation failed",
            details={}
        )
        mock_create_use_case.execute = AsyncMock(return_value=mock_create_result)

        mock_use_case_factory.create_use_case.return_value = mock_create_use_case

        # Execute workflow
        result = await app_service.create_issue_with_workflow(
            project_key="TEST",
            summary="Test issue",
            description="Test description"
        )

        # Verify
        assert result.success is False
        assert "Issue creation failed: Creation failed" in result.errors
        assert "Input validation" in result.steps_completed
        assert result.final_result == mock_create_result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
