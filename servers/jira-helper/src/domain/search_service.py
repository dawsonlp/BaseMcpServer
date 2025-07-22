"""
Search service for JQL operations.

This service is already well-focused on search operations and remains
separate from the consolidated JiraService.
"""

from typing import Any

from .base_service import BaseJiraService
from .exceptions import (
    InvalidJQLError,
    JiraValidationError,
    JQLSecurityError,
)
from .jql_builder import JQLBuilderFactory, validate_jql_safety
from .models import (
    SearchFilters,
    SearchQuery,
    SearchResult,
)
from .ports import (
    ConfigurationProvider,
    IssueSearchPort,
    JQLValidator,
    Logger,
)


class SearchService(BaseJiraService):
    """Domain service for JQL search operations."""

    def __init__(
        self,
        search_port: IssueSearchPort,
        config_provider: ConfigurationProvider,
        jql_validator: JQLValidator,
        logger: Logger,
        trilliant_sync_adapter=None
    ):
        super().__init__(
            config_provider,
            logger,
            search_port=search_port,
            jql_validator=jql_validator,
            trilliant_sync_adapter=trilliant_sync_adapter
        )

    async def search_issues(self, query: SearchQuery, instance_name: str | None = None) -> SearchResult:
        """Execute a JQL search with validation."""
        import time
        start_time = time.time()
        
        self._logger.info(f"🔍 SearchService.search_issues() ENTRY - JQL: {query.jql[:50]}... | Instance: {instance_name} | Max Results: {query.max_results}")
        
        self._validate_search_query(query)
        validation_time = time.time()
        self._logger.info(f"✅ Query validation took {validation_time - start_time:.3f}s")
        
        instance_name = self._resolve_instance_name(instance_name)
        resolve_time = time.time()
        self._logger.info(f"🏷️ Instance resolution took {resolve_time - validation_time:.3f}s | Resolved to: {instance_name}")

        # Use Trilliant-specific adapter if available and instance is Trilliant
        if self._trilliant_sync_adapter and instance_name.lower() == "trilliant":
            self._logger.info(f"🔧 Using Trilliant synchronous adapter for instance: {instance_name}")
            
            # Validate JQL syntax and security with sync adapter
            self._logger.info(f"🔒 Starting SYNC JQL validation for Trilliant instance")
            await self._validate_jql_query_sync(query.jql, instance_name)
            jql_validation_time = time.time()
            self._logger.info(f"🔒 SYNC JQL validation took {jql_validation_time - resolve_time:.3f}s")

            try:
                self._logger.info(f"📡 Calling trilliant_sync_adapter.search_issues() for instance: {instance_name}")
                result = self._trilliant_sync_adapter.search_issues(query)
                search_time = time.time()
                self._logger.info(f"📡 trilliant_sync_adapter.search_issues() completed in {search_time - jql_validation_time:.3f}s")
                
                self._logger.info(f"JQL search returned {len(result.issues)} issues (total: {result.total_results})")
                
                total_time = time.time() - start_time
                self._logger.info(f"🏁 SearchService.search_issues() COMPLETE (SYNC) - Total time: {total_time:.3f}s")
                return result
            except Exception as e:
                error_time = time.time()
                self._logger.error(f"❌ SearchService (SYNC) failed after {error_time - start_time:.3f}s: {str(e)}")
                raise InvalidJQLError(query.jql, str(e))
        else:
            # Use regular async adapter
            self._logger.info(f"🔒 Starting JQL validation for instance: {instance_name}")
            await self._validate_jql_query(query.jql, instance_name)
            jql_validation_time = time.time()
            self._logger.info(f"🔒 JQL validation took {jql_validation_time - resolve_time:.3f}s")

            try:
                self._logger.info(f"📡 Calling search_port.search_issues() for instance: {instance_name}")
                result = await self._search_port.search_issues(query, instance_name)
                search_time = time.time()
                self._logger.info(f"📡 search_port.search_issues() completed in {search_time - jql_validation_time:.3f}s")
                
                self._logger.info(f"JQL search returned {len(result.issues)} issues (total: {result.total_results})")
                
                total_time = time.time() - start_time
                self._logger.info(f"🏁 SearchService.search_issues() COMPLETE - Total time: {total_time:.3f}s")
                return result
            except Exception as e:
                error_time = time.time()
                self._logger.error(f"❌ SearchService failed after {error_time - start_time:.3f}s: {str(e)}")
                raise InvalidJQLError(query.jql, str(e))

    async def search_with_filters(self, filters: SearchFilters, instance_name: str | None = None) -> SearchResult:
        """
        Execute a search using simple filters by converting them to JQL.

        This method provides a clean interface for simple project-based searches
        while internally using the robust JQL search infrastructure.
        """
        self._validate_search_filters(filters)
        instance_name = self._resolve_instance_name(instance_name)

        try:
            # Convert filters to JQL using the builder
            jql_builder = JQLBuilderFactory.from_search_filters(filters)
            jql = jql_builder.build()

            # Additional security validation on generated JQL
            security_errors = validate_jql_safety(jql)
            if security_errors:
                raise JQLSecurityError(jql, "; ".join(security_errors))

            # Create SearchQuery from filters and generated JQL
            search_query = SearchQuery(
                jql=jql,
                max_results=filters.max_results,
                start_at=filters.start_at,
                fields=None  # Use default fields for filter-based searches
            )

            # Delegate to the main search method
            result = await self.search_issues(search_query, instance_name)

            self._logger.info(
                f"Filter search for project {filters.project_key} returned {len(result.issues)} issues "
                f"(JQL: {jql})"
            )

            return result

        except Exception as e:
            self._logger.error(
                f"Failed to execute filter search for project {filters.project_key}: {str(e)}"
            )
            # Re-raise with context about the filter conversion
            if isinstance(e, InvalidJQLError | JQLSecurityError):
                raise
            else:
                raise InvalidJQLError(
                    f"Generated from filters: {filters.get_active_filters()}",
                    str(e)
                )

    async def validate_jql_syntax(self, jql: str, instance_name: str | None = None) -> list[str]:
        """Validate JQL syntax without executing the query."""
        instance_name = self._resolve_instance_name(instance_name)

        # First check with local validator
        syntax_errors = self._jql_validator.validate_syntax(jql)
        if syntax_errors:
            return syntax_errors

        # Then check with Jira instance
        try:
            validation_errors = await self._search_port.validate_jql(jql, instance_name)
            return validation_errors
        except Exception as e:
            self._logger.error(f"Failed to validate JQL syntax: {str(e)}")
            return [f"Could not validate JQL: {str(e)}"]

    async def validate_jql(self, jql: str, instance_name: str | None = None) -> dict[str, Any]:
        """Validate JQL and return structured result with Trilliant-specific routing."""
        import time
        start_time = time.time()
        
        self._logger.info(f"🔒 SearchService.validate_jql() ENTRY - JQL: {jql[:50]}... | Instance: {instance_name}")
        
        instance_name = self._resolve_instance_name(instance_name)
        resolve_time = time.time()
        self._logger.info(f"🏷️ Instance resolution took {resolve_time - start_time:.3f}s | Resolved to: {instance_name}")

        # Use Trilliant-specific adapter if available and instance is Trilliant
        if self._trilliant_sync_adapter and instance_name.lower() == "trilliant":
            self._logger.info(f"🔧 Using Trilliant synchronous adapter for JQL validation: {instance_name}")
            
            try:
                self._logger.info(f"🔒 Starting SYNC JQL validation for Trilliant instance")
                await self._validate_jql_query_sync(jql, instance_name)
                
                validation_time = time.time()
                total_time = validation_time - start_time
                self._logger.info(f"✅ SYNC JQL validation completed in {total_time:.3f}s")
                self._logger.info(f"🏁 SearchService.validate_jql() COMPLETE (SYNC) - Total time: {total_time:.3f}s")
                
                return {
                    "valid": True,
                    "errors": [],
                    "warnings": []
                }
            except Exception as e:
                error_time = time.time()
                total_time = error_time - start_time
                self._logger.error(f"❌ SYNC JQL validation failed after {total_time:.3f}s: {str(e)}")
                
                return {
                    "valid": False,
                    "errors": [str(e)],
                    "warnings": []
                }
        else:
            # Use regular async adapter
            self._logger.info(f"🔒 Starting async JQL validation for instance: {instance_name}")
            
            try:
                await self._validate_jql_query(jql, instance_name)
                
                validation_time = time.time()
                total_time = validation_time - start_time
                self._logger.info(f"✅ Async JQL validation completed in {total_time:.3f}s")
                self._logger.info(f"🏁 SearchService.validate_jql() COMPLETE - Total time: {total_time:.3f}s")
                
                return {
                    "valid": True,
                    "errors": [],
                    "warnings": []
                }
            except Exception as e:
                error_time = time.time()
                total_time = error_time - start_time
                self._logger.error(f"❌ Async JQL validation failed after {total_time:.3f}s: {str(e)}")
                
                return {
                    "valid": False,
                    "errors": [str(e)],
                    "warnings": []
                }

    async def get_search_suggestions(self, partial_jql: str, instance_name: str | None = None) -> list[str]:
        """Get JQL completion suggestions."""
        instance_name = self._resolve_instance_name(instance_name)

        try:
            suggestions = await self._search_port.get_search_suggestions(partial_jql, instance_name)
            self._logger.debug(f"Retrieved {len(suggestions)} JQL suggestions")
            return suggestions
        except Exception as e:
            self._logger.error(f"Failed to get JQL suggestions: {str(e)}")
            return []

    def _validate_search_query(self, query: SearchQuery) -> None:
        """Validate search query parameters."""
        errors = []

        if not query.jql or not query.jql.strip():
            errors.append("JQL query cannot be empty")

        # Validate limits
        limit_errors = self._jql_validator.validate_limits(query.max_results, query.start_at)
        errors.extend(limit_errors)

        if errors:
            raise JiraValidationError(errors)

    def _validate_search_filters(self, filters: SearchFilters) -> None:
        """Validate search filters parameters."""
        errors = []

        if not filters.project_key or not filters.project_key.strip():
            errors.append("Project key cannot be empty")

        # Validate limits (reuse existing validator logic)
        limit_errors = self._jql_validator.validate_limits(filters.max_results, filters.start_at)
        errors.extend(limit_errors)

        if errors:
            raise JiraValidationError(errors)

    async def _validate_jql_query(self, jql: str, instance_name: str) -> None:
        """Validate JQL query for syntax and security."""
        # Check syntax
        is_valid, syntax_errors = self._jql_validator.validate_syntax(jql)
        if not is_valid or syntax_errors:
            raise InvalidJQLError(jql, "; ".join(syntax_errors))

        # Check security
        security_errors = self._jql_validator.check_security(jql)
        if security_errors:
            raise JQLSecurityError(jql, "; ".join(security_errors))

        # Validate with Jira instance
        validation_errors = await self._search_port.validate_jql(jql, instance_name)
        if validation_errors:
            raise InvalidJQLError(jql, "; ".join(validation_errors))

    async def _validate_jql_query_sync(self, jql: str, instance_name: str) -> None:
        """Validate JQL query for syntax and security using synchronous adapter."""
        # Check syntax
        syntax_errors = self._jql_validator.validate_syntax(jql)
        if syntax_errors:
            raise InvalidJQLError(jql, "; ".join(syntax_errors))

        # Check security
        security_errors = self._jql_validator.check_security(jql)
        if security_errors:
            raise JQLSecurityError(jql, "; ".join(security_errors))

        # Validate with Jira instance using sync adapter
        if self._trilliant_sync_adapter:
            try:
                is_valid = self._trilliant_sync_adapter.validate_jql_sync(jql, instance_name)
                if not is_valid:
                    raise InvalidJQLError(jql, "JQL validation failed")
            except Exception as e:
                if "validation" in str(e).lower():
                    raise InvalidJQLError(jql, str(e))
                else:
                    raise
