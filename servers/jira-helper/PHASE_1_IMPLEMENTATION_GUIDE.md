# Phase 1 Implementation Guide

## Overview
This guide provides step-by-step implementation details for Phase 1 critical fixes. Each task includes specific code examples and file changes.

## Task 1.1: Create BaseJiraService Class

### Step 1: Create the Base Service Class

**File**: `src/domain/base_service.py`

```python
"""
Base service class for all Jira domain services.
Eliminates code duplication and provides common functionality.
"""

import logging
from typing import Any

from .exceptions import JiraInstanceNotFound, JiraValidationError
from .ports import ConfigurationProvider, Logger


class BaseJiraService:
    """Base class for all Jira services with common functionality."""

    def __init__(
        self,
        config_provider: ConfigurationProvider,
        logger: Logger,
        **kwargs
    ):
        """Initialize base service with common dependencies."""
        self._config_provider = config_provider
        self._logger = logger
        
        # Store additional dependencies passed by subclasses
        for key, value in kwargs.items():
            setattr(self, f"_{key}", value)

    def _resolve_instance_name(self, instance_name: str | None) -> str:
        """
        Resolve instance name to use.
        
        This method eliminates duplication across 8+ service classes.
        """
        if instance_name:
            return instance_name

        default_instance = self._config_provider.get_default_instance_name()
        if not default_instance:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound("default", available_instances)

        return default_instance

    def _validate_issue_key(self, issue_key: str) -> None:
        """
        Validate issue key format.
        
        This method eliminates duplication across multiple service classes.
        """
        if not issue_key or not issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])

        if "-" not in issue_key:
            raise JiraValidationError([
                "Issue key must contain project key and number (e.g., PROJ-123)"
            ])

    def _validate_non_empty_string(self, value: str, field_name: str) -> None:
        """Validate that a string field is not empty."""
        if not value or not value.strip():
            raise JiraValidationError([f"{field_name} cannot be empty"])

    def _validate_positive_integer(self, value: int, field_name: str) -> None:
        """Validate that an integer field is positive."""
        if value <= 0:
            raise JiraValidationError([f"{field_name} must be greater than 0"])

    def _validate_max_results(self, max_results: int) -> None:
        """Validate max results parameter."""
        if max_results <= 0:
            raise JiraValidationError(["Max results must be greater than 0"])

        if max_results > 1000:
            raise JiraValidationError(["Max results cannot exceed 1000"])

    def _log_operation_start(self, operation: str, **context) -> None:
        """Log the start of an operation with context."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self._logger.info(f"Starting {operation}: {context_str}")

    def _log_operation_success(self, operation: str, **context) -> None:
        """Log successful completion of an operation."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self._logger.info(f"Completed {operation}: {context_str}")

    def _log_operation_error(self, operation: str, error: Exception, **context) -> None:
        """Log operation failure with context."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self._logger.error(f"Failed {operation}: {context_str} - {str(error)}")
```

### Step 2: Update IssueService to Use BaseJiraService

**File**: `src/domain/services.py` (modify existing IssueService)

**BEFORE** (remove these methods):
```python
def _resolve_instance_name(self, instance_name: str | None) -> str:
    # Remove this entire method - 15 lines

def _validate_issue_key(self, issue_key: str) -> None:
    # Remove this entire method - 8 lines
```

**AFTER** (update class definition):
```python
class IssueService(BaseJiraService):
    """Domain service for issue-related operations."""

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        super().__init__(
            config_provider,
            logger,
            repository=repository,
            event_publisher=event_publisher
        )

    # Remove _resolve_instance_name method (inherited from base)
    # Remove _validate_issue_key method (inherited from base)
    # Keep all other methods as-is
```

### Step 3: Update All Other Services

Apply the same pattern to all services in `src/domain/services.py`:

1. **TimeTrackingService**: Remove `_resolve_instance_name()` and `_validate_issue_key()`
2. **WorkflowService**: Remove `_resolve_instance_name()` and `_validate_issue_key()`
3. **ProjectService**: Remove `_resolve_instance_name()`
4. **VisualizationService**: Remove `_resolve_instance_name()`
5. **IssueLinkService**: Remove `_resolve_instance_name()` and `_validate_issue_key()`
6. **IssueUpdateService**: Remove `_resolve_instance_name()` and `_validate_issue_key()`
7. **SearchService**: Remove `_resolve_instance_name()`

**Template for each service**:
```python
class ServiceName(BaseJiraService):
    def __init__(self, dependencies...):
        super().__init__(config_provider, logger, **other_deps)
    
    # Remove duplicated methods
    # Keep service-specific methods
```

## Task 1.2: Consolidate Service Layer

### Step 1: Create Consolidated JiraService

**File**: `src/domain/jira_service.py`

```python
"""
Consolidated Jira service combining core CRUD operations.
Replaces IssueService, ProjectService, and WorkflowService.
"""

from typing import Any

from .base_service import BaseJiraService
from .exceptions import (
    JiraTransitionNotAvailable,
    JiraValidationError,
    JiraWorkflowError,
)
from .models import (
    AssigneeChangeRequest,
    CommentAddRequest,
    CustomFieldMapping,
    IssueCreateRequest,
    IssueTransitionRequest,
    JiraComment,
    JiraIssue,
    JiraProject,
    WorkflowTransition,
)
from .ports import ConfigurationProvider, EventPublisher, JiraRepository, Logger


class JiraService(BaseJiraService):
    """Consolidated service for core Jira operations."""

    def __init__(
        self,
        repository: JiraRepository,
        config_provider: ConfigurationProvider,
        logger: Logger,
        event_publisher: EventPublisher | None = None
    ):
        super().__init__(
            config_provider,
            logger,
            repository=repository,
            event_publisher=event_publisher
        )

    # === ISSUE OPERATIONS ===

    async def get_issue(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
        """Get a single issue by key."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)
        
        self._log_operation_start("get_issue", issue_key=issue_key, instance=instance_name)
        
        try:
            issue = await self._repository.get_issue(issue_key, instance_name)
            self._log_operation_success("get_issue", issue_key=issue_key)
            return issue
        except Exception as e:
            self._log_operation_error("get_issue", e, issue_key=issue_key)
            raise

    async def get_issue_with_comments(self, issue_key: str, instance_name: str | None = None) -> JiraIssue:
        """Get a single issue with all its comments."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)
        
        return await self._repository.get_issue_with_comments(issue_key, instance_name)

    async def create_issue(self, request: IssueCreateRequest, instance_name: str | None = None) -> JiraIssue:
        """Create a new issue."""
        self._validate_create_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            issue = await self._repository.create_issue(request, instance_name)
            self._log_operation_success("create_issue", issue_key=issue.key, project=request.project_key)

            if self._event_publisher:
                await self._event_publisher.publish_issue_created(issue, instance_name)

            return issue
        except Exception as e:
            self._log_operation_error("create_issue", e, project=request.project_key)
            raise

    async def add_comment(self, request: CommentAddRequest, instance_name: str | None = None) -> JiraComment:
        """Add a comment to an issue."""
        self._validate_comment_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            comment = await self._repository.add_comment(request, instance_name)
            self._log_operation_success("add_comment", issue_key=request.issue_key)

            if self._event_publisher:
                await self._event_publisher.publish_comment_added(request.issue_key, comment, instance_name)

            return comment
        except Exception as e:
            self._log_operation_error("add_comment", e, issue_key=request.issue_key)
            raise

    # === PROJECT OPERATIONS ===

    async def get_projects(self, instance_name: str | None = None) -> list[JiraProject]:
        """Get all projects from a Jira instance."""
        instance_name = self._resolve_instance_name(instance_name)

        try:
            projects = await self._repository.get_projects(instance_name)
            self._log_operation_success("get_projects", count=len(projects), instance=instance_name)
            return projects
        except Exception as e:
            self._log_operation_error("get_projects", e, instance=instance_name)
            raise

    async def get_custom_field_mappings(self, reverse: bool = False, instance_name: str | None = None) -> list[CustomFieldMapping]:
        """Get custom field mappings."""
        instance_name = self._resolve_instance_name(instance_name)

        try:
            mappings = await self._repository.get_custom_field_mappings(reverse, instance_name)
            self._log_operation_success("get_custom_field_mappings", count=len(mappings), instance=instance_name)
            return mappings
        except Exception as e:
            self._log_operation_error("get_custom_field_mappings", e, instance=instance_name)
            raise

    # === WORKFLOW OPERATIONS ===

    async def get_available_transitions(self, issue_key: str, instance_name: str | None = None) -> list[WorkflowTransition]:
        """Get available transitions for an issue."""
        self._validate_issue_key(issue_key)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            transitions = await self._repository.get_available_transitions(issue_key, instance_name)
            self._log_operation_success("get_transitions", issue_key=issue_key, count=len(transitions))
            return transitions
        except Exception as e:
            self._log_operation_error("get_transitions", e, issue_key=issue_key)
            raise

    async def transition_issue(self, request: IssueTransitionRequest, instance_name: str | None = None) -> JiraIssue:
        """Transition an issue through workflow."""
        self._validate_transition_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        # Get current issue state
        current_issue = await self._repository.get_issue(request.issue_key, instance_name)
        old_status = current_issue.status

        # Get available transitions
        available_transitions = await self._repository.get_available_transitions(request.issue_key, instance_name)

        # Validate transition is available
        transition_names = [t.name for t in available_transitions]
        if request.transition_name not in transition_names:
            raise JiraTransitionNotAvailable(request.issue_key, request.transition_name, transition_names)

        try:
            updated_issue = await self._repository.transition_issue(request, instance_name)
            self._log_operation_success("transition_issue", 
                issue_key=request.issue_key, 
                from_status=old_status, 
                to_status=updated_issue.status
            )

            if self._event_publisher:
                await self._event_publisher.publish_issue_transitioned(
                    updated_issue, old_status, updated_issue.status, instance_name
                )

            return updated_issue
        except Exception as e:
            self._log_operation_error("transition_issue", e, issue_key=request.issue_key)
            raise JiraWorkflowError(str(e), request.issue_key)

    async def change_assignee(self, request: AssigneeChangeRequest, instance_name: str | None = None) -> JiraIssue:
        """Change the assignee of an issue."""
        self._validate_assignee_request(request)
        instance_name = self._resolve_instance_name(instance_name)

        # Get current issue state
        current_issue = await self._repository.get_issue(request.issue_key, instance_name)
        old_assignee = current_issue.assignee

        try:
            updated_issue = await self._repository.change_assignee(request, instance_name)
            self._log_operation_success("change_assignee", 
                issue_key=request.issue_key, 
                from_assignee=old_assignee, 
                to_assignee=updated_issue.assignee
            )

            if self._event_publisher:
                await self._event_publisher.publish_assignee_changed(
                    updated_issue, old_assignee, updated_issue.assignee, instance_name
                )

            return updated_issue
        except Exception as e:
            self._log_operation_error("change_assignee", e, issue_key=request.issue_key)
            raise

    # === VALIDATION METHODS ===

    def _validate_create_request(self, request: IssueCreateRequest) -> None:
        """Validate issue creation request."""
        errors = []

        if not request.project_key or not request.project_key.strip():
            errors.append("Project key cannot be empty")

        if not request.summary or not request.summary.strip():
            errors.append("Summary cannot be empty")

        if not request.description or not request.description.strip():
            errors.append("Description cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    def _validate_comment_request(self, request: CommentAddRequest) -> None:
        """Validate comment addition request."""
        errors = []

        if not request.issue_key or not request.issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not request.comment or not request.comment.strip():
            errors.append("Comment cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    def _validate_transition_request(self, request: IssueTransitionRequest) -> None:
        """Validate transition request."""
        errors = []

        if not request.issue_key or not request.issue_key.strip():
            errors.append("Issue key cannot be empty")

        if not request.transition_name or not request.transition_name.strip():
            errors.append("Transition name cannot be empty")

        if errors:
            raise JiraValidationError(errors)

    def _validate_assignee_request(self, request: AssigneeChangeRequest) -> None:
        """Validate assignee change request."""
        if not request.issue_key or not request.issue_key.strip():
            raise JiraValidationError(["Issue key cannot be empty"])
```

### Step 2: Extract SearchService

**File**: `src/domain/search_service.py`

```python
"""
Dedicated service for JQL search operations.
Extracted from the consolidated services for focused responsibility.
"""

# Move SearchService class from services.py to this file
# Update to inherit from BaseJiraService
# Remove duplicated methods
```

### Step 3: Create ConfigurationService

**File**: `src/domain/configuration_service.py`

```python
"""
Service for instance and configuration management.
Consolidates InstanceService and configuration logic.
"""

from .base_service import BaseJiraService
from .models import JiraInstance
from .ports import ConfigurationProvider, Logger


class ConfigurationService(BaseJiraService):
    """Service for managing Jira instances and configuration."""

    def __init__(self, config_provider: ConfigurationProvider, logger: Logger):
        super().__init__(config_provider, logger)

    def get_instances(self) -> list[JiraInstance]:
        """Get all configured Jira instances."""
        try:
            instances_dict = self._config_provider.get_instances()
            instances = list(instances_dict.values())
            self._log_operation_success("get_instances", count=len(instances))
            return instances
        except Exception as e:
            self._log_operation_error("get_instances", e)
            raise

    def get_default_instance(self) -> JiraInstance | None:
        """Get the default Jira instance."""
        try:
            default_instance = self._config_provider.get_instance()
            if default_instance:
                self._log_operation_success("get_default_instance", name=default_instance.name)
            else:
                self._logger.warning("No default instance configured")
            return default_instance
        except Exception as e:
            self._log_operation_error("get_default_instance", e)
            raise

    def validate_instance(self, instance_name: str) -> bool:
        """Validate that an instance exists and is accessible."""
        try:
            instance = self._config_provider.get_instance(instance_name)
            return instance is not None
        except Exception as e:
            self._log_operation_error("validate_instance", e, instance=instance_name)
            return False
```

## Task 1.3: Simplify Domain Models

### Step 1: Create Application Layer Validators

**File**: `src/application/validators.py`

```python
"""
Application layer validators.
Moved from domain models to follow proper hexagonal architecture.
"""

from typing import Any, Dict, List

from domain.exceptions import JiraValidationError


class BaseValidator:
    """Base validator with common validation methods."""

    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that required fields are present and not empty."""
        errors = []
        
        for field in required_fields:
            if field not in data:
                errors.append(f"Field '{field}' is required")
            elif data[field] is None:
                errors.append(f"Field '{field}' cannot be None")
            elif isinstance(data[field], str) and not data[field].strip():
                errors.append(f"Field '{field}' cannot be empty")
        
        return errors

    def validate_non_empty_string(self, value: str, field_name: str) -> List[str]:
        """Validate that a string field is not empty."""
        errors = []
        if not value or not value.strip():
            errors.append(f"{field_name} cannot be empty")
        return errors

    def validate_positive_integer(self, value: int, field_name: str) -> List[str]:
        """Validate that an integer field is positive."""
        errors = []
        if value <= 0:
            errors.append(f"{field_name} must be greater than 0")
        return errors


class IssueValidator(BaseValidator):
    """Validator for issue-related operations."""

    def validate_issue_key(self, issue_key: str) -> List[str]:
        """Validate issue key format."""
        errors = []
        
        if not issue_key or not issue_key.strip():
            errors.append("Issue key cannot be empty")
            return errors

        if "-" not in issue_key:
            errors.append("Issue key must contain project key and number (e.g., PROJ-123)")

        return errors

    def validate_create_request(self, data: Dict[str, Any]) -> List[str]:
        """Validate issue creation request."""
        required_fields = ['project_key', 'summary', 'description', 'issue_type']
        errors = self.validate_required_fields(data, required_fields)
        
        # Additional validation logic here
        
        return errors

    def validate_comment_request(self, data: Dict[str, Any]) -> List[str]:
        """Validate comment addition request."""
        required_fields = ['issue_key', 'comment']
        return self.validate_required_fields(data, required_fields)


class ProjectValidator(BaseValidator):
    """Validator for project-related operations."""

    def validate_project_key(self, project_key: str) -> List[str]:
        """Validate project key format."""
        return self.validate_non_empty_string(project_key, "Project key")


class SearchValidator(BaseValidator):
    """Validator for search-related operations."""

    def validate_jql_query(self, jql: str) -> List[str]:
        """Validate JQL query."""
        return self.validate_non_empty_string(jql, "JQL query")

    def validate_search_limits(self, max_results: int, start_at: int) -> List[str]:
        """Validate search pagination limits."""
        errors = []
        
        if max_results <= 0:
            errors.append("Max results must be greater than 0")
        
        if max_results > 1000:
            errors.append("Max results cannot exceed 1000")
        
        if start_at < 0:
            errors.append("Start at must be non-negative")
        
        return errors
```

### Step 2: Simplify Domain Models

**File**: `src/domain/models.py` (modify existing)

Remove validation decorators and business logic methods:

**BEFORE**:
```python
@validate_required_fields('key', 'summary', 'status')
@dataclass
class JiraIssue:
    # ... fields ...
    
    def add_comment(self, comment: JiraComment) -> None:
        """Add a comment to the issue."""
        self.comments.append(comment)

    def get_latest_comment(self) -> JiraComment | None:
        """Get the most recent comment."""
        if not self.comments:
            return None
        return max(self.comments, key=lambda c: c.created)
```

**AFTER**:
```python
@dataclass
class JiraIssue:
    """Represents a Jira issue with all its properties."""
    key: str
    id: str
    summary: str
    description: str
    status: str
    issue_type: str
    priority: str
    assignee: str | None = None
    reporter: str | None = None
    created: str | None = None
    updated: str | None = None
    components: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)
    comments: list[JiraComment] = field(default_factory=list)
    url: str | None = None

    # Keep only essential domain methods, move validation elsewhere
```

## Task 1.4: Split Infrastructure Layer

### Step 1: Extract AtlassianApiRepository

**File**: `src/infrastructure/atlassian_repository.py`

```python
"""
Atlassian API repository implementation.
Extracted from atlassian_api_adapter.py for better separation of concerns.
"""

import asyncio
import logging
from typing import Any

from atlassian import Jira

from domain.exceptions import JiraIssueNotFound
from domain.models import CommentAddRequest, IssueCreateRequest, JiraIssue, JiraProject, JiraComment
from domain.ports import JiraRepository
from .converters import JiraIssueConverter

logger = logging.getLogger(__name__)


class AtlassianApiRepository(JiraRepository):
    """Repository implementation using atlassian-python-api."""

    def __init__(self, client_factory, config_provider):
        self._client_factory = client_factory
        self._config_provider = config_provider
        self._converter = JiraIssueConverter(config_provider)

    async def get_issue(self, issue_key: str, instance_name: str) -> JiraIssue:
        """Get a specific issue by key."""
        try:
            client = self._client_factory.create_client(instance_name)
            issue_data = await asyncio.to_thread(client.issue, issue_key)
            return self._converter.convert_issue_to_domain(issue_data, instance_name)
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(issue_key, instance_name or "default")
            logger.error(f"Failed to get issue {issue_key}: {str(e)}")
            raise

    # ... other repository methods
```

### Step 2: Extract Other Adapters

Create similar files for:
- `src/infrastructure/atlassian_link_adapter.py`
- `src/infrastructure/atlassian_update_adapter.py`
- `src/infrastructure/atlassian_time_adapter.py`
- `src/infrastructure/atlassian_search_adapter.py`

### Step 3: Update Main Adapter File

**File**: `src/infrastructure/atlassian_api_adapter.py` (keep only factory)

```python
"""
Atlassian API client factory.
Simplified to focus only on client creation.
"""

import logging
from typing import Any

from atlassian import Jira

from domain.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraInstanceNotFound,
    JiraTimeoutError,
)
from domain.ports import ConfigurationProvider, JiraClientFactory

logger = logging.getLogger(__name__)


class AtlassianApiJiraClientFactory(JiraClientFactory):
    """Factory for creating Jira clients using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._clients: dict[str, Jira] = {}

    def create_client(self, instance_name: str | None = None) -> Jira:
        """Create a Jira client for the specified instance."""
        # ... existing implementation
```

## Testing the Changes

### Step 1: Update Use Cases

Update use case files to use the new consolidated services:

**File**: `src/application/use_cases.py`

```python
# Update imports
from domain.jira_service import JiraService
from domain.search_service import SearchService
from domain.configuration_service import ConfigurationService

# Update use case constructors to use new services
```

### Step 2: Update Dependency Injection

**File**: `src/application/services.py` or dependency injection setup

```python
# Update service registration to use new consolidated services
def create_jira_service():
    return JiraService(repository, config_provider, logger, event_publisher)

def create_search_service():
    return SearchService(search_port, config_provider, jql_validator, logger)

def create_configuration_service():
    return ConfigurationService(config_provider, logger)
```

### Step 3: Run Tests

```bash
cd servers/jira-helper
python run_tests.py
```

## Expected Results

After completing Phase 1:

1. **Code Reduction**: ~800-1000 lines eliminated
2. **Service Count**: Reduced from 9 to 3 services
3. **Duplication**: Eliminated 8 instances of `_resolve_instance_name()`
4. **File Organization**: Infrastructure properly separated
5. **Validation**: Moved to appropriate application layer

## Next Steps

Once Phase 1 is complete and all tests pass:
1. Review the changes with the team
2. Update documentation
3. Plan Phase 2 implementation
4. Consider performance impact and optimization opportunities

---

**Implementation Priority**: Complete tasks in order 1.1 → 1.2 → 1.3 → 1.4
**Testing**: Run tests after each major change
**Rollback**: Keep original files until new implementation is proven stable
