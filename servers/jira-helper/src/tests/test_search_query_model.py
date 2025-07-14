"""
Tests for SearchQuery domain model.
"""

import pytest
from domain.models import SearchQuery, SearchResult
from domain.exceptions import InvalidJQLError, SearchLimitExceededError, JQLSecurityError


class TestSearchQuery:
    """Test cases for SearchQuery model."""

    def test_create_valid_search_query(self):
        """Test creating a valid search query."""
        query = SearchQuery(
            jql="project = PROJ AND status = 'In Progress'",
            max_results=50,
            start_at=0
        )
        
        assert query.jql == "project = PROJ AND status = 'In Progress'"
        assert query.max_results == 50
        assert query.start_at == 0

    def test_create_query_with_defaults(self):
        """Test creating query with default values."""
        query = SearchQuery(jql="project = PROJ")
        
        assert query.jql == "project = PROJ"
        assert query.max_results == 50  # Default value
        assert query.start_at == 0  # Default value
        assert query.fields is None  # Default value

    def test_create_query_with_custom_fields(self):
        """Test creating query with custom fields."""
        fields = ["key", "summary", "status", "assignee"]
        query = SearchQuery(
            jql="project = PROJ",
            fields=fields
        )
        
        assert query.fields == fields

    def test_invalid_max_results(self):
        """Test validation of max_results parameter."""
        # Too high
        with pytest.raises(SearchLimitExceededError):
            SearchQuery(
                jql="project = PROJ",
                max_results=2000  # Over limit
            )

        # Negative
        with pytest.raises(ValueError):
            SearchQuery(
                jql="project = PROJ",
                max_results=-1
            )

        # Zero
        with pytest.raises(ValueError):
            SearchQuery(
                jql="project = PROJ",
                max_results=0
            )

    def test_invalid_start_at(self):
        """Test validation of start_at parameter."""
        # Negative
        with pytest.raises(ValueError):
            SearchQuery(
                jql="project = PROJ",
                start_at=-1
            )

    def test_empty_jql_validation(self):
        """Test that empty JQL is rejected."""
        with pytest.raises(InvalidJQLError):
            SearchQuery(jql="")

        with pytest.raises(InvalidJQLError):
            SearchQuery(jql="   ")  # Whitespace only

    def test_jql_security_validation(self):
        """Test JQL security validation."""
        # Potentially dangerous JQL
        dangerous_queries = [
            "project = PROJ; DROP TABLE issues;",
            "project = PROJ UNION SELECT * FROM users",
            "project = PROJ' OR '1'='1",
        ]
        
        for dangerous_jql in dangerous_queries:
            with pytest.raises(JQLSecurityError):
                SearchQuery(jql=dangerous_jql)

    def test_jql_syntax_validation(self):
        """Test JQL syntax validation."""
        # Valid JQL
        valid_queries = [
            "project = PROJ",
            "project = PROJ AND status = 'In Progress'",
            "assignee = currentUser() AND created >= -7d",
            "project in (PROJ1, PROJ2) ORDER BY created DESC"
        ]
        
        for valid_jql in valid_queries:
            query = SearchQuery(jql=valid_jql)
            assert query.validate_jql()

        # Invalid JQL syntax
        invalid_queries = [
            "project ==== PROJ",  # Invalid operator
            "project = PROJ AND AND status = Open",  # Double AND
            "project = PROJ ORDER ORDER BY created",  # Double ORDER
        ]
        
        for invalid_jql in invalid_queries:
            with pytest.raises(InvalidJQLError):
                SearchQuery(jql=invalid_jql)

    def test_fields_validation(self):
        """Test validation of fields parameter."""
        # Valid fields
        valid_fields = ["key", "summary", "status", "assignee", "created"]
        query = SearchQuery(
            jql="project = PROJ",
            fields=valid_fields
        )
        assert query.validate_fields()

        # Invalid fields (empty list)
        with pytest.raises(ValueError):
            SearchQuery(
                jql="project = PROJ",
                fields=[]
            )

        # Invalid field names
        with pytest.raises(ValueError):
            SearchQuery(
                jql="project = PROJ",
                fields=["invalid_field_name"]
            )

    def test_to_dict(self):
        """Test converting query to dictionary."""
        query = SearchQuery(
            jql="project = PROJ AND status = Open",
            max_results=25,
            start_at=10,
            fields=["key", "summary"]
        )
        
        query_dict = query.to_dict()
        
        expected = {
            "jql": "project = PROJ AND status = Open",
            "max_results": 25,
            "start_at": 10,
            "fields": ["key", "summary"]
        }
        
        assert query_dict == expected

    def test_from_dict(self):
        """Test creating query from dictionary."""
        query_dict = {
            "jql": "project = PROJ",
            "max_results": 25,
            "start_at": 10,
            "fields": ["key", "summary"]
        }
        
        query = SearchQuery.from_dict(query_dict)
        
        assert query.jql == "project = PROJ"
        assert query.max_results == 25
        assert query.start_at == 10
        assert query.fields == ["key", "summary"]

    def test_get_pagination_info(self):
        """Test getting pagination information."""
        query = SearchQuery(
            jql="project = PROJ",
            max_results=25,
            start_at=50
        )
        
        pagination = query.get_pagination_info()
        
        assert pagination["max_results"] == 25
        assert pagination["start_at"] == 50
        assert pagination["page"] == 3  # (50 / 25) + 1

    def test_get_next_page_query(self):
        """Test getting next page query."""
        query = SearchQuery(
            jql="project = PROJ",
            max_results=25,
            start_at=0
        )
        
        next_query = query.get_next_page_query()
        
        assert next_query.jql == query.jql
        assert next_query.max_results == query.max_results
        assert next_query.start_at == 25
        assert next_query.fields == query.fields

    def test_get_previous_page_query(self):
        """Test getting previous page query."""
        query = SearchQuery(
            jql="project = PROJ",
            max_results=25,
            start_at=50
        )
        
        prev_query = query.get_previous_page_query()
        
        assert prev_query.jql == query.jql
        assert prev_query.max_results == query.max_results
        assert prev_query.start_at == 25
        assert prev_query.fields == query.fields

    def test_get_previous_page_query_first_page(self):
        """Test getting previous page query when on first page."""
        query = SearchQuery(
            jql="project = PROJ",
            max_results=25,
            start_at=0
        )
        
        prev_query = query.get_previous_page_query()
        
        assert prev_query.start_at == 0  # Should stay at 0

    def test_sanitize_jql(self):
        """Test JQL sanitization."""
        query = SearchQuery(jql="project = PROJ AND summary ~ 'test'")
        
        sanitized = query.sanitize_jql()
        
        # Should remove potentially dangerous characters/patterns
        assert "'" in sanitized  # Normal quotes should be preserved
        assert sanitized == "project = PROJ AND summary ~ 'test'"

    def test_estimate_complexity(self):
        """Test JQL complexity estimation."""
        # Simple query
        simple_query = SearchQuery(jql="project = PROJ")
        assert simple_query.estimate_complexity() == "low"

        # Medium complexity query
        medium_query = SearchQuery(jql="project = PROJ AND status = Open AND assignee = currentUser()")
        assert medium_query.estimate_complexity() == "medium"

        # Complex query
        complex_query = SearchQuery(
            jql="project in (PROJ1, PROJ2, PROJ3) AND created >= -30d AND "
                "assignee in membersOf('developers') ORDER BY priority DESC, created ASC"
        )
        assert complex_query.estimate_complexity() == "high"


class TestSearchResult:
    """Test cases for SearchResult model."""

    def test_create_successful_result(self):
        """Test creating successful search result."""
        issues = [
            {"key": "PROJ-1", "summary": "Test issue 1"},
            {"key": "PROJ-2", "summary": "Test issue 2"}
        ]
        
        result = SearchResult(
            success=True,
            issues=issues,
            total=100,
            start_at=0,
            max_results=50
        )
        
        assert result.success is True
        assert len(result.issues) == 2
        assert result.total == 100
        assert result.start_at == 0
        assert result.max_results == 50

    def test_create_failed_result(self):
        """Test creating failed search result."""
        result = SearchResult(
            success=False,
            error="Invalid JQL syntax",
            jql="project ==== PROJ"
        )
        
        assert result.success is False
        assert result.error == "Invalid JQL syntax"
        assert result.jql == "project ==== PROJ"
        assert result.issues == []

    def test_pagination_info(self):
        """Test pagination information."""
        result = SearchResult(
            success=True,
            issues=[],
            total=100,
            start_at=25,
            max_results=25
        )
        
        pagination = result.get_pagination_info()
        
        assert pagination["total"] == 100
        assert pagination["start_at"] == 25
        assert pagination["max_results"] == 25
        assert pagination["current_page"] == 2
        assert pagination["total_pages"] == 4
        assert pagination["has_next_page"] is True
        assert pagination["has_previous_page"] is True

    def test_pagination_first_page(self):
        """Test pagination on first page."""
        result = SearchResult(
            success=True,
            issues=[],
            total=100,
            start_at=0,
            max_results=25
        )
        
        pagination = result.get_pagination_info()
        
        assert pagination["current_page"] == 1
        assert pagination["has_previous_page"] is False
        assert pagination["has_next_page"] is True

    def test_pagination_last_page(self):
        """Test pagination on last page."""
        result = SearchResult(
            success=True,
            issues=[],
            total=100,
            start_at=75,
            max_results=25
        )
        
        pagination = result.get_pagination_info()
        
        assert pagination["current_page"] == 4
        assert pagination["has_previous_page"] is True
        assert pagination["has_next_page"] is False

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        issues = [{"key": "PROJ-1", "summary": "Test"}]
        
        result = SearchResult(
            success=True,
            issues=issues,
            total=1,
            start_at=0,
            max_results=50,
            jql="project = PROJ"
        )
        
        result_dict = result.to_dict()
        
        expected = {
            "success": True,
            "issues": issues,
            "total": 1,
            "start_at": 0,
            "max_results": 50,
            "jql": "project = PROJ",
            "error": None,
            "execution_time_ms": None
        }
        
        assert result_dict == expected

    def test_result_from_dict(self):
        """Test creating result from dictionary."""
        result_dict = {
            "success": True,
            "issues": [{"key": "PROJ-1"}],
            "total": 1,
            "start_at": 0,
            "max_results": 50
        }
        
        result = SearchResult.from_dict(result_dict)
        
        assert result.success is True
        assert len(result.issues) == 1
        assert result.total == 1

    def test_get_issue_keys(self):
        """Test getting list of issue keys."""
        issues = [
            {"key": "PROJ-1", "summary": "Test 1"},
            {"key": "PROJ-2", "summary": "Test 2"}
        ]
        
        result = SearchResult(
            success=True,
            issues=issues,
            total=2,
            start_at=0,
            max_results=50
        )
        
        keys = result.get_issue_keys()
        assert keys == ["PROJ-1", "PROJ-2"]

    def test_filter_issues_by_field(self):
        """Test filtering issues by field value."""
        issues = [
            {"key": "PROJ-1", "status": "Open", "priority": "High"},
            {"key": "PROJ-2", "status": "Closed", "priority": "Low"},
            {"key": "PROJ-3", "status": "Open", "priority": "Medium"}
        ]
        
        result = SearchResult(
            success=True,
            issues=issues,
            total=3,
            start_at=0,
            max_results=50
        )
        
        open_issues = result.filter_issues_by_field("status", "Open")
        assert len(open_issues) == 2
        assert open_issues[0]["key"] == "PROJ-1"
        assert open_issues[1]["key"] == "PROJ-3"

    def test_get_execution_stats(self):
        """Test getting execution statistics."""
        result = SearchResult(
            success=True,
            issues=[],
            total=100,
            start_at=0,
            max_results=50,
            execution_time_ms=250
        )
        
        stats = result.get_execution_stats()
        
        assert stats["total_results"] == 100
        assert stats["returned_results"] == 0
        assert stats["execution_time_ms"] == 250
        assert stats["results_per_second"] > 0
