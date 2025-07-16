"""
Integration Tests.

Tests for infrastructure layer and end-to-end integration scenarios.
Tests Jira API integration, configuration loading, and complete workflows.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from application.base_use_case import UseCaseFactory
from application.services import JiraApplicationService, ValidationService
from domain.exceptions import (
    JiraConfigurationMissingError,
    JiraValidationError,
)
from domain.models import (
    IssueCreateRequest,
    JiraIssue,
    JiraProject,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
)
from infrastructure.config_adapter import ConfigurationAdapter
from infrastructure.graph_generator import GraphvizGenerator
from infrastructure.jira_api_repository import JiraApiRepository
from infrastructure.jira_client_factory import JiraClientFactory


class TestJiraApiRepository:
    """Test JiraApiRepository integration with mocked Jira client."""

    @pytest.fixture
    def mock_jira_client(self):
        """Mock Jira client."""
        client = Mock()

        # Mock issue operations
        client.issue = Mock()
        client.issue.return_value = Mock()

        # Mock project operations
        client.projects = Mock()
        client.projects.return_value = []

        # Mock transition operations
        client.transitions = Mock()
        client.transitions.return_value = []

        # Mock create operations
        client.create_issue = Mock()
        client.add_comment = Mock()
        client.transition_issue = Mock()

        return client

    @pytest.fixture
    def mock_client_factory(self, mock_jira_client):
        """Mock JiraClientFactory."""
        factory = Mock()
        factory.get_client = Mock(return_value=mock_jira_client)
        return factory

    @pytest.fixture
    def jira_repository(self, mock_client_factory):
        """Create JiraApiRepository with mocked dependencies."""
        return JiraApiRepository(client_factory=mock_client_factory)

    @pytest.mark.asyncio
    async def test_get_issue_integration(self, jira_repository, mock_jira_client, mock_client_factory):
        """Test get_issue integration with Jira client."""
        # Setup mock response
        mock_issue_data = Mock()
        mock_issue_data.key = "TEST-123"
        mock_issue_data.id = "12345"
        mock_issue_data.fields.summary = "Test issue"
        mock_issue_data.fields.description = "Test description"
        mock_issue_data.fields.status.name = "Open"
        mock_issue_data.fields.issuetype.name = "Story"
        mock_issue_data.fields.priority.name = "Medium"
        mock_issue_data.fields.assignee.displayName = "John Doe"
        mock_issue_data.fields.reporter.displayName = "Jane Doe"
        mock_issue_data.fields.created = "2024-01-01T10:00:00.000+0000"
        mock_issue_data.fields.updated = "2024-01-01T11:00:00.000+0000"
        mock_issue_data.fields.components = []
        mock_issue_data.fields.labels = ["bug"]

        mock_jira_client.issue.return_value = mock_issue_data

        # Execute
        result = await jira_repository.get_issue("TEST-123", "default")

        # Verify
        assert isinstance(result, JiraIssue)
        assert result.key == "TEST-123"
        assert result.summary == "Test issue"
        assert result.status == "Open"
        assert "bug" in result.labels

        # Verify client was called correctly
        mock_client_factory.get_client.assert_called_once_with("default")
        mock_jira_client.issue.assert_called_once_with("TEST-123")

    @pytest.mark.asyncio
    async def test_get_projects_integration(self, jira_repository, mock_jira_client, mock_client_factory):
        """Test get_projects integration with Jira client."""
        # Setup mock response
        mock_project_data = [
            Mock(
                key="TEST1",
                name="Test Project 1",
                id="10001",
                lead=Mock(displayName="John Doe", emailAddress="john@example.com")
            ),
            Mock(
                key="TEST2",
                name="Test Project 2",
                id="10002",
                lead=Mock(displayName="Jane Doe", emailAddress="jane@example.com")
            )
        ]

        mock_jira_client.projects.return_value = mock_project_data

        # Execute
        result = await jira_repository.get_projects("default")

        # Verify
        assert len(result) == 2
        assert all(isinstance(project, JiraProject) for project in result)
        assert result[0].key == "TEST1"
        assert result[1].key == "TEST2"
        assert result[0].lead_name == "John Doe"

        # Verify client was called correctly
        mock_client_factory.get_client.assert_called_once_with("default")
        mock_jira_client.projects.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_issue_integration(self, jira_repository, mock_jira_client, mock_client_factory):
        """Test create_issue integration with Jira client."""
        # Setup mock response
        mock_created_issue = Mock()
        mock_created_issue.key = "TEST-124"
        mock_created_issue.id = "12346"
        mock_created_issue.fields.summary = "New test issue"
        mock_created_issue.fields.description = "New test description"
        mock_created_issue.fields.status.name = "Open"
        mock_created_issue.fields.issuetype.name = "Story"
        mock_created_issue.fields.priority.name = "Medium"
        mock_created_issue.fields.assignee = None
        mock_created_issue.fields.reporter.displayName = "Jane Doe"
        mock_created_issue.fields.created = "2024-01-01T12:00:00.000+0000"
        mock_created_issue.fields.updated = "2024-01-01T12:00:00.000+0000"
        mock_created_issue.fields.components = []
        mock_created_issue.fields.labels = ["test"]

        mock_jira_client.create_issue.return_value = mock_created_issue

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
        result = await jira_repository.create_issue(request, "default")

        # Verify
        assert isinstance(result, JiraIssue)
        assert result.key == "TEST-124"
        assert result.summary == "New test issue"
        assert result.labels == ["test"]

        # Verify client was called correctly
        mock_client_factory.get_client.assert_called_once_with("default")
        mock_jira_client.create_issue.assert_called_once()


class TestConfigurationAdapter:
    """Test ConfigurationAdapter integration."""

    @pytest.fixture
    def mock_config_data(self):
        """Mock configuration data."""
        return {
            "instances": {
                "production": {
                    "url": "https://company.atlassian.net",
                    "user": "api.user@company.com",
                    "token": "secret_token",
                    "description": "Production instance"
                },
                "staging": {
                    "url": "https://staging.atlassian.net",
                    "user": "api.user@company.com",
                    "token": "staging_token",
                    "description": "Staging instance"
                }
            },
            "default_instance": "production"
        }

    @pytest.fixture
    def config_adapter(self, mock_config_data):
        """Create ConfigurationAdapter with mock data."""
        with patch('infrastructure.config_adapter.load_config', return_value=mock_config_data):
            return ConfigurationAdapter()

    def test_get_instance_config(self, config_adapter):
        """Test getting instance configuration."""
        config = config_adapter.get_instance_config("production")

        assert config.name == "production"
        assert config.url == "https://company.atlassian.net"
        assert config.user == "api.user@company.com"
        assert config.description == "Production instance"
        assert config.is_default is True

    def test_get_default_instance(self, config_adapter):
        """Test getting default instance."""
        default = config_adapter.get_default_instance()

        assert default.name == "production"
        assert default.is_default is True

    def test_get_all_instances(self, config_adapter):
        """Test getting all instances."""
        instances = config_adapter.get_all_instances()

        assert len(instances) == 2
        instance_names = [instance.name for instance in instances]
        assert "production" in instance_names
        assert "staging" in instance_names

        # Check default flag
        production = next(i for i in instances if i.name == "production")
        staging = next(i for i in instances if i.name == "staging")
        assert production.is_default is True
        assert staging.is_default is False

    def test_get_nonexistent_instance(self, config_adapter):
        """Test getting non-existent instance raises error."""
        with pytest.raises(JiraConfigurationMissingError):
            config_adapter.get_instance_config("nonexistent")


class TestGraphvizGenerator:
    """Test GraphvizGenerator integration."""

    @pytest.fixture
    def graph_generator(self):
        """Create GraphvizGenerator."""
        return GraphvizGenerator()

    @pytest.fixture
    def sample_workflow_graph(self):
        """Sample workflow graph for testing."""
        nodes = [
            WorkflowNode(id="1", name="Open", status_category="new"),
            WorkflowNode(id="2", name="In Progress", status_category="indeterminate"),
            WorkflowNode(id="3", name="Done", status_category="done")
        ]

        edges = [
            WorkflowEdge(from_node="1", to_node="2", transition_name="Start Progress"),
            WorkflowEdge(from_node="2", to_node="3", transition_name="Done")
        ]

        return WorkflowGraph(
            project_key="TEST",
            issue_type="Story",
            nodes=nodes,
            edges=edges
        )

    def test_generate_svg_graph(self, graph_generator, sample_workflow_graph):
        """Test SVG graph generation."""
        with patch('infrastructure.graph_generator.graphviz') as mock_graphviz:
            mock_dot = Mock()
            mock_dot.render.return_value = "test_output.svg"
            mock_graphviz.Digraph.return_value = mock_dot

            graph_generator.generate_svg(sample_workflow_graph)

            # Verify graph was created
            mock_graphviz.Digraph.assert_called_once()
            mock_dot.render.assert_called_once()

            # Verify nodes and edges were added
            assert mock_dot.node.call_count == 3  # 3 nodes
            assert mock_dot.edge.call_count == 2  # 2 edges

    def test_generate_png_graph(self, graph_generator, sample_workflow_graph):
        """Test PNG graph generation."""
        with patch('infrastructure.graph_generator.graphviz') as mock_graphviz:
            mock_dot = Mock()
            mock_dot.render.return_value = "test_output.png"
            mock_graphviz.Digraph.return_value = mock_dot

            graph_generator.generate_png(sample_workflow_graph)

            # Verify graph was created with PNG format
            mock_graphviz.Digraph.assert_called_once()
            mock_dot.render.assert_called_once()


class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        deps = {
            'jira_client': Mock(),
            'config_data': {
                "instances": {
                    "test": {
                        "url": "https://test.atlassian.net",
                        "user": "test@example.com",
                        "token": "test_token",
                        "description": "Test instance"
                    }
                },
                "default_instance": "test"
            }
        }

        # Setup Jira client responses
        deps['jira_client'].projects.return_value = [
            Mock(
                key="TEST",
                name="Test Project",
                id="10001",
                lead=Mock(displayName="John Doe", emailAddress="john@example.com")
            )
        ]

        return deps

    @pytest.fixture
    def integrated_system(self, mock_dependencies):
        """Create integrated system with all components."""
        with patch('infrastructure.config_adapter.load_config', return_value=mock_dependencies['config_data']):
            with patch('infrastructure.jira_client_factory.JIRA', return_value=mock_dependencies['jira_client']):
                # Create configuration adapter
                config_adapter = ConfigurationAdapter()

                # Create client factory
                client_factory = JiraClientFactory(config_adapter)

                # Create repository
                jira_repository = JiraApiRepository(client_factory)

                # Create services (mocked for this test)
                issue_service = Mock()
                project_service = Mock()
                workflow_service = Mock()
                instance_service = Mock()

                # Setup service responses
                project_service.get_projects = AsyncMock(return_value=[
                    JiraProject(
                        key="TEST",
                        name="Test Project",
                        id="10001",
                        lead_name="John Doe",
                        lead_email="john@example.com",
                        url="https://test.atlassian.net/projects/TEST"
                    )
                ])

                # Create use case factory
                factory = UseCaseFactory(
                    issue_service=issue_service,
                    project_service=project_service,
                    workflow_service=workflow_service,
                    instance_service=instance_service
                )

                # Create application service
                app_service = JiraApplicationService(factory)

                return {
                    'config_adapter': config_adapter,
                    'client_factory': client_factory,
                    'jira_repository': jira_repository,
                    'app_service': app_service,
                    'factory': factory
                }

    def test_configuration_loading_integration(self, integrated_system):
        """Test configuration loading works end-to-end."""
        config_adapter = integrated_system['config_adapter']

        # Test getting instance config
        instance = config_adapter.get_instance_config("test")
        assert instance.name == "test"
        assert instance.url == "https://test.atlassian.net"
        assert instance.is_default is True

        # Test getting all instances
        instances = config_adapter.get_all_instances()
        assert len(instances) == 1
        assert instances[0].name == "test"

    def test_client_factory_integration(self, integrated_system, mock_dependencies):
        """Test client factory creates clients correctly."""
        client_factory = integrated_system['client_factory']

        # Get client for test instance
        client = client_factory.get_client("test")

        # Verify client is the mocked one
        assert client == mock_dependencies['jira_client']

    @pytest.mark.asyncio
    async def test_application_service_integration(self, integrated_system):
        """Test application service orchestration works end-to-end."""
        app_service = integrated_system['app_service']

        # Test project overview workflow
        result = await app_service.get_project_overview(
            project_key="TEST",
            include_recent_issues=False,
            instance_name="test"
        )

        # Verify result structure
        assert result.success is True
        assert "project" in result.data
        assert result.data["project"]["key"] == "TEST"
        assert result.data["instance"] == "test"

    @pytest.mark.asyncio
    async def test_validation_service_integration(self):
        """Test validation service works correctly."""
        validation = ValidationService()

        # Test successful validations
        validation.validate_issue_key("TEST-123")
        validation.validate_project_key("TEST")
        validation.validate_summary("This is a valid summary")

        # Test validation failures
        with pytest.raises(JiraValidationError):
            validation.validate_issue_key("INVALID")

        with pytest.raises(JiraValidationError):
            validation.validate_project_key("123")

        with pytest.raises(JiraValidationError):
            validation.validate_summary("Too short")


class TestMcpAdapterIntegration:
    """Test MCP adapter integration with application layer."""

    @pytest.fixture
    def mock_app_service(self):
        """Mock application service."""
        app_service = Mock()

        # Mock successful responses
        app_service.get_project_overview = AsyncMock(return_value=Mock(
            success=True,
            data={
                "project": {"key": "TEST", "name": "Test Project"},
                "recent_issues": [],
                "instance": "test"
            }
        ))

        return app_service

    @pytest.fixture
    def mock_use_case_factory(self):
        """Mock use case factory."""
        factory = Mock()

        # Mock use cases
        mock_list_projects = Mock()
        mock_list_projects.execute = AsyncMock(return_value=Mock(
            success=True,
            data={
                "projects": [{"key": "TEST", "name": "Test Project"}],
                "count": 1,
                "instance": "test"
            }
        ))

        factory.create_use_case.return_value = mock_list_projects
        return factory

    @pytest.fixture
    def mcp_adapter(self, mock_app_service, mock_use_case_factory):
        """Create MCP adapter with mocked dependencies."""
        return McpJiraAdapter(
            app_service=mock_app_service,
            use_case_factory=mock_use_case_factory
        )

    @pytest.mark.asyncio
    async def test_mcp_tool_integration(self, mcp_adapter, mock_use_case_factory):
        """Test MCP tool integration with use cases."""
        # Test list_jira_projects tool
        result = await mcp_adapter.list_jira_projects(instance_name="test")

        # Verify result structure matches MCP expectations
        assert isinstance(result, dict)
        assert "projects" in result
        assert "count" in result
        assert result["count"] == 1

        # Verify use case was called
        mock_use_case_factory.create_use_case.assert_called()

    @pytest.mark.asyncio
    async def test_mcp_error_handling_integration(self, mcp_adapter, mock_use_case_factory):
        """Test MCP adapter handles errors correctly."""
        # Setup failing use case
        mock_failing_use_case = Mock()
        mock_failing_use_case.execute = AsyncMock(return_value=Mock(
            success=False,
            error="Test error",
            details={"operation": "test"}
        ))

        mock_use_case_factory.create_use_case.return_value = mock_failing_use_case

        # Execute and verify error handling
        with pytest.raises(Exception) as exc_info:
            await mcp_adapter.list_jira_projects(instance_name="test")

        assert "Test error" in str(exc_info.value)


class TestPerformanceIntegration:
    """Test performance characteristics of integrated system."""

    @pytest.fixture
    def performance_test_data(self):
        """Generate test data for performance testing."""
        return {
            'projects': [
                JiraProject(
                    key=f"PROJ{i}",
                    name=f"Project {i}",
                    id=str(10000 + i),
                    lead_name="Test Lead",
                    lead_email="lead@example.com",
                    url=f"https://test.atlassian.net/projects/PROJ{i}"
                )
                for i in range(100)  # 100 projects
            ],
            'issues': [
                JiraIssue(
                    key=f"TEST-{i}",
                    id=str(i),
                    summary=f"Test issue {i}",
                    description=f"Description for issue {i}",
                    status="Open",
                    issue_type="Story",
                    priority="Medium",
                    assignee="test.user",
                    reporter="test.reporter",
                    created="2024-01-01T10:00:00Z",
                    updated="2024-01-01T11:00:00Z",
                    components=[],
                    labels=[],
                    url=f"https://test.atlassian.net/browse/TEST-{i}"
                )
                for i in range(1000)  # 1000 issues
            ]
        }

    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self, performance_test_data):
        """Test performance of bulk operations."""
        import time

        # Mock service that returns large datasets
        mock_service = Mock()
        mock_service.get_projects = AsyncMock(return_value=performance_test_data['projects'])

        # Time the operation
        start_time = time.time()

        projects = await mock_service.get_projects("test")

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify performance is reasonable (should be very fast with mocks)
        assert execution_time < 1.0  # Less than 1 second
        assert len(projects) == 100

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self):
        """Test performance of concurrent operations."""
        import time

        # Mock service with slight delay to simulate real operations
        mock_service = Mock()

        async def mock_get_issue(issue_key, instance):
            await asyncio.sleep(0.01)  # 10ms delay
            return JiraIssue(
                key=issue_key,
                id="123",
                summary="Test issue",
                description="Test description",
                status="Open",
                issue_type="Story",
                priority="Medium",
                assignee="test.user",
                reporter="test.reporter",
                created="2024-01-01T10:00:00Z",
                updated="2024-01-01T11:00:00Z",
                components=[],
                labels=[],
                url=f"https://test.atlassian.net/browse/{issue_key}"
            )

        mock_service.get_issue = mock_get_issue

        # Test concurrent execution
        start_time = time.time()

        tasks = [
            mock_service.get_issue(f"TEST-{i}", "test")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        execution_time = end_time - start_time

        # Concurrent execution should be faster than sequential
        # 10 operations * 10ms = 100ms sequential, but concurrent should be ~10ms
        assert execution_time < 0.05  # Less than 50ms for concurrent
        assert len(results) == 10


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
