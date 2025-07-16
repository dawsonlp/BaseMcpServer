"""
JQL Builder utility for constructing Jira Query Language queries.

This module provides a clean, fluent interface for building JQL queries
from simple search filters, with proper validation and sanitization.
"""

import re

from .models import SearchFilters


class JQLBuilder:
    """
    Fluent interface for building JQL queries with validation and sanitization.

    This class follows the builder pattern to construct JQL queries step by step,
    ensuring proper escaping and validation of input values.
    """

    def __init__(self):
        """Initialize an empty JQL builder."""
        self._conditions: list[str] = []
        self._order_by: str | None = None

    def project(self, project_key: str) -> 'JQLBuilder':
        """
        Add a project filter to the JQL query.

        Args:
            project_key: The project key to filter by

        Returns:
            Self for method chaining

        Raises:
            ValueError: If project_key is empty or invalid
        """
        if not project_key or not project_key.strip():
            raise ValueError("Project key cannot be empty")

        # Validate project key format (alphanumeric, hyphens, underscores)
        if not re.match(r'^[A-Z0-9_-]+$', project_key.upper()):
            raise ValueError(f"Invalid project key format: {project_key}")

        escaped_key = self._escape_value(project_key)
        self._conditions.append(f"project = {escaped_key}")
        return self

    def status(self, status_name: str) -> 'JQLBuilder':
        """
        Add a status filter to the JQL query.

        Args:
            status_name: The status name to filter by

        Returns:
            Self for method chaining

        Raises:
            ValueError: If status_name is empty
        """
        if not status_name or not status_name.strip():
            raise ValueError("Status name cannot be empty")

        escaped_status = self._escape_value(status_name)
        self._conditions.append(f"status = {escaped_status}")
        return self

    def issue_type(self, type_name: str) -> 'JQLBuilder':
        """
        Add an issue type filter to the JQL query.

        Args:
            type_name: The issue type name to filter by

        Returns:
            Self for method chaining

        Raises:
            ValueError: If type_name is empty
        """
        if not type_name or not type_name.strip():
            raise ValueError("Issue type name cannot be empty")

        escaped_type = self._escape_value(type_name)
        self._conditions.append(f"issuetype = {escaped_type}")
        return self

    def assignee(self, assignee_name: str) -> 'JQLBuilder':
        """
        Add an assignee filter to the JQL query.

        Args:
            assignee_name: The assignee name to filter by, or "unassigned"

        Returns:
            Self for method chaining
        """
        if assignee_name.lower() == "unassigned":
            self._conditions.append("assignee is EMPTY")
        else:
            escaped_assignee = self._escape_value(assignee_name)
            self._conditions.append(f"assignee = {escaped_assignee}")
        return self

    def reporter(self, reporter_name: str) -> 'JQLBuilder':
        """
        Add a reporter filter to the JQL query.

        Args:
            reporter_name: The reporter name to filter by

        Returns:
            Self for method chaining
        """
        escaped_reporter = self._escape_value(reporter_name)
        self._conditions.append(f"reporter = {escaped_reporter}")
        return self

    def priority(self, priority_name: str) -> 'JQLBuilder':
        """
        Add a priority filter to the JQL query.

        Args:
            priority_name: The priority name to filter by

        Returns:
            Self for method chaining
        """
        escaped_priority = self._escape_value(priority_name)
        self._conditions.append(f"priority = {escaped_priority}")
        return self

    def labels(self, label_names: list[str]) -> 'JQLBuilder':
        """
        Add a labels filter to the JQL query.

        Args:
            label_names: List of label names to filter by

        Returns:
            Self for method chaining
        """
        if not label_names:
            return self

        label_conditions = []
        for label in label_names:
            if label and label.strip():
                escaped_label = self._escape_value(label)
                label_conditions.append(f"labels = {escaped_label}")

        if label_conditions:
            # Use AND for multiple labels (issue must have all labels)
            labels_clause = " AND ".join(label_conditions)
            self._conditions.append(f"({labels_clause})")

        return self

    def created_after(self, date_str: str) -> 'JQLBuilder':
        """
        Add a created after date filter to the JQL query.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Self for method chaining
        """
        # Basic date format validation
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

        self._conditions.append(f"created >= '{date_str}'")
        return self

    def created_before(self, date_str: str) -> 'JQLBuilder':
        """
        Add a created before date filter to the JQL query.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Self for method chaining
        """
        # Basic date format validation
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

        self._conditions.append(f"created <= '{date_str}'")
        return self

    def order_by_created(self, ascending: bool = False) -> 'JQLBuilder':
        """
        Add an order by created date clause.

        Args:
            ascending: If True, order ascending; if False, order descending

        Returns:
            Self for method chaining
        """
        direction = "ASC" if ascending else "DESC"
        self._order_by = f"created {direction}"
        return self

    def order_by_updated(self, ascending: bool = False) -> 'JQLBuilder':
        """
        Add an order by updated date clause.

        Args:
            ascending: If True, order ascending; if False, order descending

        Returns:
            Self for method chaining
        """
        direction = "ASC" if ascending else "DESC"
        self._order_by = f"updated {direction}"
        return self

    def order_by_priority(self, ascending: bool = False) -> 'JQLBuilder':
        """
        Add an order by priority clause.

        Args:
            ascending: If True, order ascending; if False, order descending

        Returns:
            Self for method chaining
        """
        direction = "ASC" if ascending else "DESC"
        self._order_by = f"priority {direction}"
        return self

    def build(self) -> str:
        """
        Build and return the final JQL query string.

        Returns:
            The constructed JQL query string

        Raises:
            ValueError: If no conditions have been added
        """
        if not self._conditions:
            raise ValueError("Cannot build JQL query with no conditions")

        # Join conditions with AND
        jql = " AND ".join(self._conditions)

        # Add ORDER BY clause if specified
        if self._order_by:
            jql += f" ORDER BY {self._order_by}"

        return jql

    def reset(self) -> 'JQLBuilder':
        """
        Reset the builder to start building a new query.

        Returns:
            Self for method chaining
        """
        self._conditions.clear()
        self._order_by = None
        return self

    def _escape_value(self, value: str) -> str:
        """
        Escape a value for safe use in JQL queries.

        Args:
            value: The value to escape

        Returns:
            The escaped value wrapped in quotes if necessary
        """
        # Remove any existing quotes and escape internal quotes
        cleaned_value = value.strip().replace('"', '\\"')

        # Always quote values to prevent injection and handle spaces
        return f'"{cleaned_value}"'

    def get_conditions_count(self) -> int:
        """
        Get the number of conditions currently in the builder.

        Returns:
            Number of conditions
        """
        return len(self._conditions)

    def has_conditions(self) -> bool:
        """
        Check if the builder has any conditions.

        Returns:
            True if there are conditions, False otherwise
        """
        return len(self._conditions) > 0


class JQLBuilderFactory:
    """Factory for creating JQLBuilder instances with common patterns."""

    @staticmethod
    def from_search_filters(filters: SearchFilters) -> JQLBuilder:
        """
        Create a JQLBuilder from SearchFilters.

        Args:
            filters: The SearchFilters to convert

        Returns:
            A JQLBuilder with the filters applied
        """
        builder = JQLBuilder()

        # Always add project filter (required)
        builder.project(filters.project_key)

        # Add optional filters
        if filters.has_status_filter():
            builder.status(filters.status)

        if filters.has_issue_type_filter():
            builder.issue_type(filters.issue_type)

        # Default ordering by created date (newest first)
        builder.order_by_created(ascending=False)

        return builder

    @staticmethod
    def for_project(project_key: str) -> JQLBuilder:
        """
        Create a JQLBuilder for a specific project.

        Args:
            project_key: The project key

        Returns:
            A JQLBuilder with project filter applied
        """
        return JQLBuilder().project(project_key)

    @staticmethod
    def for_assignee(assignee_name: str) -> JQLBuilder:
        """
        Create a JQLBuilder for a specific assignee.

        Args:
            assignee_name: The assignee name

        Returns:
            A JQLBuilder with assignee filter applied
        """
        return JQLBuilder().assignee(assignee_name)


def validate_jql_safety(jql: str) -> list[str]:
    """
    Validate JQL query for potential security issues.

    Args:
        jql: The JQL query to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check for potential injection patterns
    dangerous_patterns = [
        r';\s*DROP\s+TABLE',  # SQL injection attempt
        r';\s*DELETE\s+FROM',  # SQL injection attempt
        r'<script',  # XSS attempt
        r'javascript:',  # JavaScript injection
        r'eval\s*\(',  # Code execution attempt
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, jql, re.IGNORECASE):
            errors.append(f"Potentially dangerous pattern detected: {pattern}")

    # Check for excessively long queries (potential DoS)
    if len(jql) > 5000:
        errors.append("JQL query is too long (max 5000 characters)")

    # Check for too many OR conditions (potential performance issue)
    or_count = len(re.findall(r'\bOR\b', jql, re.IGNORECASE))
    if or_count > 50:
        errors.append(f"Too many OR conditions ({or_count}), max 50 allowed")

    return errors
