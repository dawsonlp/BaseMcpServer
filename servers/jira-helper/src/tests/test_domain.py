"""
Domain Layer Tests.

Tests for domain models, exceptions, and services using live Jira connections.
These tests run against the "personal" Jira instance and use the "ATP" test project.
"""

import logging
import pytest

from domain.exceptions import (
    JiraDomainException,
    JiraInstanceNotFound,
    JiraValidationError,
)
from domain.models import (
    CommentAddRequest,
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
from infrastructure.atlassian_repository import (
    AtlassianApiJiraClientFactory,
    AtlassianApiRepository,
)
from infrastructure.config_adapter import ConfigurationAdapter


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
        assert issue.is_assigned() is True
        assert issue.has_labels() is True
        assert issue.has_components() is True

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

    def test_workflow_graph_creation(self):
        """Test WorkflowGraph domain model."""
        nodes = [
            WorkflowNode(id="1", name="Open", category="new", color="blue"),
            WorkflowNode(id="2", name="In Progress", category="indeterminate", color="yellow"),
            WorkflowNode(id="3", name="Done", category="done", color="green")
        ]

        edges = [
            WorkflowEdge(from_node="1", to_node="2", label="Start Progress"),
            WorkflowEdge(from_node="2", to_node="3", label="Done")
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
        assert graph.edges[0].label == "Start Progress"

    def test_custom_field_mapping(self):
        """Test CustomFieldMapping domain model."""
        mapping = CustomFieldMapping(
            field_id="customfield_10001",
            name="Story Points",
            description="Estimation in story points"
        )

        assert mapping.field_id == "customfield_10001"
        assert mapping.name == "Story Points"

    def test_jira_instance_configuration(self):
        """Test JiraInstance domain model."""
        instance = JiraInstance(
            name="production",
            url="https://company.atlassian.net",
            user="api.user@company.com",
            token="fake-token",
            description="Production Jira instance",
            is_default=True
        )

        assert instance.name == "production"
        assert instance.url == "https://company.atlassian.net"
        assert instance.is_default is True


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


class TestDomainServicesIntegration:
    """Test domain services with live Jira integration."""

    @pytest.fixture(scope="module")
    def config_provider(self):
        """Fixture for the configuration provider."""
        return ConfigurationAdapter()

    @pytest.fixture(scope="module")
    def jira_repository(self, config_provider):
        """Fixture for live JiraRepository."""
        client_factory = AtlassianApiJiraClientFactory(config_provider)
        return AtlassianApiRepository(client_factory, config_provider)

    @pytest.fixture(scope="module")
    def logger(self):
        """Fixture for logger."""
        return logging.getLogger(__name__)

    @pytest.fixture
    def issue_service(self, jira_repository, config_provider, logger):
        """Create IssueService with live dependencies."""
        return IssueService(
            repository=jira_repository,
            config_provider=config_provider,
            logger=logger
        )

    @pytest.fixture
    def project_service(self, jira_repository, config_provider, logger):
        """Create ProjectService with live dependencies."""
        return ProjectService(
            repository=jira_repository,
            config_provider=config_provider,
            logger=logger
        )

    @pytest.fixture
    def workflow_service(self, jira_repository, config_provider, logger):
        """Create WorkflowService with live dependencies."""
        return WorkflowService(
            repository=jira_repository,
            config_provider=config_provider,
            logger=logger
        )

    @pytest.mark.asyncio
    async def test_project_service_get_projects(self, project_service):
        """Test ProjectService.get_projects method with live Jira."""
        # Execute
        result = await project_service.get_projects("personal")

        # Verify
        assert len(result) > 0
        # Check if the ATP project is in the list
        assert any(p.key == "ATP" for p in result)
        
        # Verify project structure
        atp_project = next(p for p in result if p.key == "ATP")
        assert atp_project.name is not None
        assert atp_project.id is not None

    @pytest.mark.asyncio
    async def test_issue_service_create_and_get_issue(self, issue_service, jira_repository):
        """Test IssueService create and get issue methods with live Jira."""
        # Create request
        request = IssueCreateRequest(
            project_key="ATP",
            summary="Domain Service Test Issue",
            description="This is a test issue created by domain service integration tests.",
            issue_type="Task",
            priority="Medium",
            assignee=None,
            labels=["domain-test"]
        )

        created_issue = None
        try:
            # Execute create
            created_issue = await issue_service.create_issue(request, "personal")

            # Verify creation
            assert created_issue is not None
            assert created_issue.summary == "Domain Service Test Issue"
            assert created_issue.issue_type == "Task"
            assert "domain-test" in created_issue.labels

            # Execute get
            retrieved_issue = await issue_service.get_issue(created_issue.key, "personal")

            # Verify retrieval
            assert retrieved_issue is not None
            assert retrieved_issue.key == created_issue.key
            assert retrieved_issue.summary == "Domain Service Test Issue"

        finally:
            if created_issue:
                # Clean up the created issue
                client = jira_repository._client_factory.create_client("personal")
                client.delete_issue(created_issue.key)

    @pytest.mark.asyncio
    async def test_issue_service_add_comment(self, issue_service, jira_repository):
        """Test IssueService add comment method with live Jira."""
        # First create an issue
        create_request = IssueCreateRequest(
            project_key="ATP",
            summary="Comment Test Issue",
            description="This is an issue for testing comments via domain service.",
            issue_type="Task",
            priority="Medium",
            assignee=None,
            labels=["comment-test"]
        )

        created_issue = None
        try:
            created_issue = await issue_service.create_issue(create_request, "personal")
            assert created_issue is not None

            # Add a comment
            comment_request = CommentAddRequest(
                issue_key=created_issue.key,
                comment="This is a test comment added via domain service."
            )
            added_comment = await issue_service.add_comment(comment_request, "personal")

            # Verify comment
            assert added_comment is not None
            assert added_comment.body == "This is a test comment added via domain service."

            # Get issue with comments to verify
            issue_with_comments = await issue_service.get_issue_with_comments(created_issue.key, "personal")
            assert issue_with_comments is not None
            assert len(issue_with_comments.comments) > 0
            assert any(c.body == "This is a test comment added via domain service." for c in issue_with_comments.comments)

        finally:
            if created_issue:
                # Clean up the created issue
                client = jira_repository._client_factory.create_client("personal")
                client.delete_issue(created_issue.key)

    @pytest.mark.asyncio
    async def test_workflow_service_get_transitions(self, workflow_service, issue_service, jira_repository):
        """Test WorkflowService.get_available_transitions method with live Jira."""
        # First create an issue to test transitions on
        create_request = IssueCreateRequest(
            project_key="ATP",
            summary="Workflow Test Issue",
            description="This is an issue for testing workflow transitions.",
            issue_type="Task",
            priority="Medium",
            assignee=None,
            labels=["workflow-test"]
        )

        created_issue = None
        try:
            created_issue = await issue_service.create_issue(create_request, "personal")
            assert created_issue is not None

            # Execute get transitions
            result = await workflow_service.get_available_transitions(created_issue.key, "personal")

            # Verify
            assert len(result) > 0
            # Should have at least some basic transitions available
            transition_names = [t.name for t in result]
            assert len(transition_names) > 0
            
            # Verify transition structure
            for transition in result:
                assert transition.id is not None
                assert transition.name is not None
                assert transition.to_status is not None

        finally:
            if created_issue:
                # Clean up the created issue
                client = jira_repository._client_factory.create_client("personal")
                client.delete_issue(created_issue.key)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
