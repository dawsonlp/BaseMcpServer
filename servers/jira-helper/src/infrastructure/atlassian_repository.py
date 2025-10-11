"""
Atlassian API Repository implementation.

This module contains the core repository implementation for Jira operations
using the atlassian-python-api library.
"""

import asyncio
import logging
from typing import Any

from atlassian import Jira

from domain.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraInstanceNotFound,
    JiraIssueNotFound,
    JiraTimeoutError,
    WorkflowDataUnavailableError,
    WorkflowSchemeNotFoundError,
    WorkflowStrategyError,
    ProjectWorkflowPermissionError,
    InvalidIssueTypeError,
    JiraProjectNotFound,
    JiraValidationError,
)
from domain.models import CommentAddRequest, IssueCreateRequest, JiraIssue, JiraProject, JiraComment
from domain.ports import ConfigurationProvider, JiraClientFactory, JiraRepository
from infrastructure.converters import JiraIssueConverter

logger = logging.getLogger(__name__)


class AtlassianApiJiraClientFactory(JiraClientFactory):
    """Factory for creating Jira clients using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._clients: dict[str, Jira] = {}

    def create_client(self, instance_name: str | None = None) -> Jira:
        """Create a Jira client for the specified instance."""
        if instance_name is None:
            instance_name = self._config_provider.get_default_instance_name()
            if instance_name is None:
                available_instances = list(self._config_provider.get_instances().keys())
                raise JiraInstanceNotFound("default", available_instances)

        if instance_name in self._clients:
            return self._clients[instance_name]

        instance = self._config_provider.get_instance(instance_name)
        if instance is None:
            available_instances = list(self._config_provider.get_instances().keys())
            raise JiraInstanceNotFound(instance_name, available_instances)

        try:
            is_cloud = ".atlassian.net" in instance.url
            client = Jira(
                url=instance.url,
                username=instance.user,
                password=instance.token,
                cloud=is_cloud,
                timeout=30,
            )
            self._clients[instance_name] = client
            logger.info(f"Created Jira client for instance: {instance_name} using atlassian-python-api")
            return client
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "unauthorized" in error_msg:
                raise JiraAuthenticationError(instance_name, str(e))
            elif "timeout" in error_msg:
                raise JiraTimeoutError("client_creation", instance_name, 30)
            else:
                raise JiraConnectionError(instance_name, str(e))

    def validate_instance(self, instance_name: str) -> bool:
        """Validate that an instance exists and is properly configured."""
        try:
            client = self.create_client(instance_name)
            client.myself()
            return True
        except Exception:
            return False


class AtlassianApiRepository(JiraRepository):
    """Repository implementation using atlassian-python-api."""

    def __init__(self, client_factory: JiraClientFactory, config_provider: ConfigurationProvider):
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

    async def get_projects(self, instance_name: str) -> list[JiraProject]:
        """Get all projects from a Jira instance."""
        try:
            client = self._client_factory.create_client(instance_name)
            projects_data = await asyncio.to_thread(client.projects)
            
            result = []
            for project_data in projects_data:
                lead_data = project_data.get("lead", {})
                instance = self._config_provider.get_instance(instance_name)
                project_url = f"{instance.url}/projects/{project_data['key']}" if instance else None

                jira_project = JiraProject(
                    key=project_data["key"],
                    name=project_data["name"],
                    id=project_data["id"],
                    lead_name=lead_data.get("displayName"),
                    lead_email=lead_data.get("emailAddress"),
                    url=project_url,
                )
                result.append(jira_project)
            return result
        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}")
            raise

    async def get_issue_with_comments(self, issue_key: str, instance_name: str) -> JiraIssue:
        """Get a specific issue with all its comments."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Get issue and comments in parallel
            issue_data, comments_data = await asyncio.gather(
                asyncio.to_thread(client.issue, issue_key),
                asyncio.to_thread(client.issue_get_comments, issue_key)
            )

            jira_issue = self._converter.convert_issue_to_domain(issue_data, instance_name)

            for comment_data in comments_data.get("comments", []):
                comment = JiraComment(
                    id=comment_data["id"],
                    author_name=comment_data.get("author", {}).get("displayName"),
                    author_key=comment_data.get("author", {}).get("key"),
                    body=comment_data.get("body"),
                    created=comment_data.get("created"),
                    updated=comment_data.get("updated"),
                )
                jira_issue.add_comment(comment)

            jira_issue.comments.sort(key=lambda c: c.created, reverse=True)
            return jira_issue

        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise JiraIssueNotFound(issue_key, instance_name or "default")
            logger.error(f"Failed to get issue with comments {issue_key}: {str(e)}")
            raise

    async def create_issue(self, request: IssueCreateRequest, instance_name: str) -> JiraIssue:
        """Create a new issue."""
        try:
            client = self._client_factory.create_client(instance_name)

            issue_dict = {
                "project": {"key": request.project_key},
                "summary": request.summary,
                "description": request.description,
                "issuetype": {"name": request.issue_type},
            }
            
            # Add standard optional fields
            if request.priority:
                issue_dict["priority"] = {"name": request.priority}
            if request.assignee:
                issue_dict["assignee"] = {"name": request.assignee}
            if request.labels:
                issue_dict["labels"] = request.labels

            # Add custom fields to the payload
            if request.has_custom_fields():
                for field_id, field_value in request.custom_fields.items():
                    issue_dict[field_id] = field_value
                    logger.debug(f"Added custom field {field_id} with value: {field_value}")

            logger.debug(f"Creating issue with payload: {issue_dict}")

            created_issue_data = await asyncio.to_thread(
                client.issue_create, fields=issue_dict
            )

            # Fetch the full issue details to get all fields
            full_issue_data = await asyncio.to_thread(
                client.issue, created_issue_data["key"]
            )

            return self._converter.convert_issue_to_domain(full_issue_data, instance_name)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to create issue: {error_msg}")
            
            # Provide more helpful error messages for custom field issues
            if "customfield_" in error_msg and "required" in error_msg.lower():
                logger.error("This appears to be a custom field validation error. Check that all required custom fields are provided.")
            elif "customfield_" in error_msg:
                logger.error("This appears to be a custom field format error. Check the custom field values match the expected format.")
            
            raise

    async def add_comment(self, request: CommentAddRequest, instance_name: str) -> JiraComment:
        """Add a comment to an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            comment_data = await asyncio.to_thread(
                client.issue_add_comment, request.issue_key, request.comment
            )

            return JiraComment(
                id=comment_data["id"],
                author_name=comment_data.get("author", {}).get("displayName"),
                author_key=comment_data.get("author", {}).get("key"),
                body=comment_data.get("body"),
                created=comment_data.get("created"),
                updated=comment_data.get("updated"),
            )
        except Exception as e:
            logger.error(f"Failed to add comment to {request.issue_key}: {str(e)}")
            raise

    async def get_available_transitions(self, issue_key: str, instance_name: str) -> list[Any]:
        """Get available transitions for an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            transitions_data = await asyncio.to_thread(client.get_issue_transitions, issue_key)
            
            from domain.models import WorkflowTransition
            result = []
            # transitions_data is a list directly, not a dict with "transitions" key
            for transition_data in transitions_data:
                # Handle "to" field which can be a string or dict
                to_field = transition_data.get("to", "Unknown")
                if isinstance(to_field, dict):
                    to_status = to_field.get("name", "Unknown")
                else:
                    to_status = str(to_field)
                
                transition = WorkflowTransition(
                    id=transition_data["id"],
                    name=transition_data["name"],
                    to_status=to_status
                )
                result.append(transition)
            return result
        except Exception as e:
            logger.error(f"Failed to get transitions for issue {issue_key}: {str(e)}")
            raise

    async def transition_issue(self, request, instance_name: str) -> JiraIssue:
        """Transition an issue through workflow."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get available transitions to find the transition ID
            transitions_data = await asyncio.to_thread(client.get_issue_transitions, request.issue_key)
            
            # Find the transition ID by name
            transition_id = None
            for transition in transitions_data:
                if transition["name"] == request.transition_name:
                    transition_id = transition["id"]
                    break
            
            if transition_id is None:
                available_transitions = [t["name"] for t in transitions_data]
                raise ValueError(f"Transition '{request.transition_name}' not available. Available: {available_transitions}")
            
            # Execute the transition
            transition_data = {"transition": {"id": transition_id}}
            
            # Add comment if provided
            if request.comment:
                transition_data["update"] = {
                    "comment": [{"add": {"body": request.comment}}]
                }
            
            await asyncio.to_thread(
                client.set_issue_status_by_transition_id,
                request.issue_key,
                transition_id
            )
            
            # Fetch the updated issue to return
            updated_issue_data = await asyncio.to_thread(client.issue, request.issue_key)
            return self._converter.convert_issue_to_domain(updated_issue_data, instance_name)
            
        except Exception as e:
            logger.error(f"Failed to transition issue {request.issue_key}: {str(e)}")
            raise

    async def change_assignee(self, request, instance_name: str) -> JiraIssue:
        """Change the assignee of an issue."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Build the assignee field update
            if request.assignee is None:
                # Unassign the issue
                assignee_field = {"assignee": None}
            else:
                # Assign to specific user
                assignee_field = {"assignee": {"name": request.assignee}}
            
            # Update the issue with new assignee
            await asyncio.to_thread(
                client.issue_update,
                request.issue_key,
                fields=assignee_field
            )
            
            # Fetch the updated issue to return
            updated_issue_data = await asyncio.to_thread(client.issue, request.issue_key)
            return self._converter.convert_issue_to_domain(updated_issue_data, instance_name)
            
        except Exception as e:
            logger.error(f"Failed to change assignee for issue {request.issue_key}: {str(e)}")
            raise

    async def search_issues(
        self,
        project_key: str,
        status: str | None,
        issue_type: str | None,
        max_results: int,
        instance_name: str
    ) -> list[JiraIssue]:
        """Search for issues in a project with filters."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Build JQL query from parameters
            jql_parts = [f"project = {project_key}"]
            
            if status:
                jql_parts.append(f"status = \"{status}\"")
            
            if issue_type:
                jql_parts.append(f"issuetype = \"{issue_type}\"")
            
            jql_parts.append("ORDER BY created DESC")
            jql = " AND ".join(jql_parts)
            
            # Execute search
            search_results = await asyncio.to_thread(
                client.jql,
                jql,
                limit=max_results
            )
            
            # Convert results to domain objects
            issues = []
            for issue_data in search_results.get("issues", []):
                issue = self._converter.convert_issue_to_domain(issue_data, instance_name)
                issues.append(issue)
            
            logger.info(f"Found {len(issues)} issues for project {project_key}")
            return issues
            
        except Exception as e:
            logger.error(f"Failed to search issues in project {project_key}: {str(e)}")
            raise

    async def get_custom_field_mappings(self, reverse: bool, instance_name: str) -> list[Any]:
        """Get custom field mappings."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get all fields from Jira
            fields_data = await asyncio.to_thread(client.get_all_fields)
            
            from domain.models import CustomFieldMapping
            mappings = []
            
            for field_data in fields_data:
                # Only include custom fields (they start with 'customfield_')
                if field_data.get("id", "").startswith("customfield_"):
                    if reverse:
                        # Map from name to ID
                        mapping = CustomFieldMapping(
                            name=field_data.get("name", ""),
                            field_id=field_data.get("id", ""),
                            description=field_data.get("description", "")
                        )
                    else:
                        # Map from ID to name (default)
                        mapping = CustomFieldMapping(
                            field_id=field_data.get("id", ""),
                            name=field_data.get("name", ""),
                            description=field_data.get("description", "")
                        )
                    mappings.append(mapping)
            
            logger.info(f"Retrieved {len(mappings)} custom field mappings")
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to get custom field mappings: {str(e)}")
            raise

    async def get_workflow_data(self, project_key: str, issue_type: str, instance_name: str) -> dict[str, Any]:
        """
        Get workflow data using a multi-strategy approach to handle different Jira permission levels.
        
        Tries three strategies in order of data quality:
        1. Direct schema access (admin permissions) - most complete data
        2. Project statuses API (standard user) - good data with logical transitions  
        3. Sample issue extraction (read-only) - limited data from existing issues
        """
        try:
            client = self._client_factory.create_client(instance_name)
            project_data = await asyncio.to_thread(client.project, project_key)
            
            base_workflow_data = self._create_base_workflow_structure(project_data, issue_type)
            
            # Track failed strategies for diagnostic information
            failed_strategies = []
            
            # Strategy 1: Direct workflow schema access (admin-level permissions required)
            # Best data quality - gets exact workflow definitions from Jira configuration
            try:
                logger.info(f"Attempting Strategy 1: Direct workflow schema access for {project_key}::{issue_type}")
                workflow_data = await self._extract_workflow_from_schema(client, project_key, issue_type, base_workflow_data)
                workflow_data["failed_strategies"] = failed_strategies
                return workflow_data
            except Exception as schema_error:
                error_msg = f"Strategy 1 failed (likely insufficient admin permissions): {str(schema_error)}"
                logger.warning(error_msg)
                failed_strategies.append({
                    "strategy": "direct_schema_access",
                    "error": str(schema_error),
                    "reason": "Insufficient admin permissions or API unavailable"
                })
            
            # Strategy 2: Project statuses API (standard user permissions)
            # Good data quality - gets real statuses, generates logical transitions
            try:
                logger.info(f"Attempting Strategy 2: Project statuses API for {project_key}::{issue_type}")
                workflow_data = await self._build_workflow_from_project_statuses(client, project_key, issue_type, base_workflow_data)
                workflow_data["failed_strategies"] = failed_strategies
                return workflow_data
            except Exception as statuses_error:
                error_msg = f"Strategy 2 failed (API may be restricted): {str(statuses_error)}"
                logger.warning(error_msg)
                failed_strategies.append({
                    "strategy": "project_statuses_api",
                    "error": str(statuses_error),
                    "reason": "Project statuses API restricted or issue type not found"
                })
            
            # Strategy 3: Sample issue extraction (read-only permissions)
            # Limited data quality - only works if issues exist, gets partial workflow view
            try:
                logger.info(f"Attempting Strategy 3: Sample issue fallback for {project_key}::{issue_type}")
                workflow_data = await self._extract_workflow_from_sample_issue(client, project_key, issue_type, base_workflow_data)
                workflow_data["failed_strategies"] = failed_strategies
                return workflow_data
            except Exception as sample_error:
                error_msg = f"Strategy 3 failed (no issues or read access denied): {str(sample_error)}"
                logger.warning(error_msg)
                failed_strategies.append({
                    "strategy": "sample_issue_extraction",
                    "error": str(sample_error),
                    "reason": "No issues available or insufficient read permissions"
                })
            
            # All strategies exhausted - provide actionable error message with failure details
            self._raise_workflow_unavailable_error(project_key, issue_type, failed_strategies)
            
        except Exception as e:
            logger.error(f"Failed to get workflow data for {project_key}::{issue_type}: {str(e)}")
            raise

    def _create_base_workflow_structure(self, project_data: dict, issue_type: str) -> dict[str, Any]:
        """Create the base workflow data structure with project information."""
        return {
            "project": {
                "key": project_data.get("key"),
                "name": project_data.get("name"), 
                "id": project_data.get("id")
            },
            "issue_type": issue_type,
            "statuses": [],
            "transitions": []
        }

    async def _extract_workflow_from_schema(self, client: Jira, project_key: str, issue_type: str, base_data: dict) -> dict[str, Any]:
        """Strategy 1: Extract workflow data from project workflow scheme."""
        # Get project workflow scheme
        scheme_url = f"rest/api/3/project/{project_key}/workflowscheme"
        workflow_scheme_data = await asyncio.to_thread(client.get, scheme_url)
        
        # Get all available workflows
        all_workflows_data = await asyncio.to_thread(client.get_all_workflows)
        
        # Find workflow ID for this issue type
        issue_type_mappings = workflow_scheme_data.get("issueTypeMappings", {})
        workflow_id = issue_type_mappings.get(issue_type) or workflow_scheme_data.get("defaultWorkflow")
        
        if not workflow_id:
            raise Exception(f"No workflow mapping found for issue type {issue_type}")
        
        # Find workflow definition
        workflow_definition = None
        for workflow in all_workflows_data:
            if workflow.get("id") == workflow_id or workflow.get("name") == workflow_id:
                workflow_definition = workflow
                break
                
        if not workflow_definition:
            raise Exception(f"Workflow definition not found for ID: {workflow_id}")
        
        # Extract statuses and transitions
        workflow_data = base_data.copy()
        workflow_data["workflow_scheme"] = {
            "id": workflow_scheme_data.get("id"),
            "name": workflow_scheme_data.get("name"),
            "workflow_id": workflow_id
        }
        
        for status_data in workflow_definition.get("statuses", []):
            workflow_data["statuses"].append({
                "name": status_data["name"],
                "statusCategory": status_data.get("statusCategory", {"name": "Unknown"})
            })
        
        for transition_data in workflow_definition.get("transitions", []):
            from_statuses = transition_data.get("from", [{}])
            to_status = transition_data.get("to", {}).get("name", "Unknown")
            
            for from_status_data in from_statuses:
                from_status = from_status_data.get("name", "Unknown")
                workflow_data["transitions"].append({
                    "name": transition_data["name"],
                    "from": from_status,
                    "to": to_status
                })
        
        logger.info(f"Strategy 1 successful: {len(workflow_data['statuses'])} statuses, {len(workflow_data['transitions'])} transitions")
        return workflow_data

    async def _build_workflow_from_project_statuses(self, client: Jira, project_key: str, issue_type: str, base_data: dict) -> dict[str, Any]:
        """Strategy 2: Build workflow from project statuses API."""
        project_statuses_url = f"rest/api/3/project/{project_key}/statuses"
        project_statuses_by_issue_type = await asyncio.to_thread(client.get, project_statuses_url)
        
        # Find statuses for the specific issue type
        issue_type_statuses = None
        for item in project_statuses_by_issue_type:
            if item.get("name") == issue_type:
                issue_type_statuses = item.get("statuses", [])
                break
                
        if not issue_type_statuses:
            raise Exception(f"No statuses found for issue type {issue_type} in project {project_key}")
        
        # Build workflow data
        workflow_data = base_data.copy()
        
        for status_info in issue_type_statuses:
            workflow_data["statuses"].append({
                "name": status_info["name"],
                "statusCategory": status_info.get("statusCategory", {"name": "Unknown"})
            })
        
        # Generate logical transitions based on status categories
        self._generate_logical_transitions_from_status_categories(workflow_data)
        
        logger.info(f"Strategy 2 successful: {len(workflow_data['statuses'])} statuses with logical transitions")
        return workflow_data

    async def _extract_workflow_from_sample_issue(self, client: Jira, project_key: str, issue_type: str, base_data: dict) -> dict[str, Any]:
        """Strategy 3: Extract workflow data from sample issues (enhanced fallback)."""
        # Try specific issue type first
        jql = f'project = "{project_key}" AND issuetype = "{issue_type}" ORDER BY created DESC'
        search_results = await asyncio.to_thread(client.jql, jql, limit=1)
        
        sample_issue_data = None
        if search_results.get("issues"):
            sample_issue_data = search_results["issues"][0] 
            logger.info(f"Found {issue_type} sample issue: {sample_issue_data['key']}")
        else:
            # Fallback to any issue in project
            logger.warning(f"No {issue_type} issues found, trying any issue type in {project_key}")
            jql = f'project = "{project_key}" ORDER BY created DESC'
            search_results = await asyncio.to_thread(client.jql, jql, limit=1)
            
            if search_results.get("issues"):
                sample_issue_data = search_results["issues"][0]
                logger.warning(f"Using sample issue of different type: {sample_issue_data['key']}")
        
        if not sample_issue_data:
            raise Exception(f"No issues found in project {project_key} for workflow extraction")
        
        # Extract workflow from sample issue
        workflow_data = base_data.copy()
        sample_issue_key = sample_issue_data["key"]
        current_status_info = sample_issue_data["fields"]["status"]
        
        # Add current status
        workflow_data["statuses"].append({
            "name": current_status_info["name"],
            "statusCategory": current_status_info.get("statusCategory", {"name": "Unknown"})
        })
        
        # Get available transitions and add target statuses
        transitions_data = await asyncio.to_thread(client.get_issue_transitions, sample_issue_key)
        
        for transition in transitions_data:
            to_status = transition.get("to", {})
            if isinstance(to_status, dict) and "name" in to_status:
                status_name = to_status["name"]
                
                # Add status if not already present  
                if not any(s["name"] == status_name for s in workflow_data["statuses"]):
                    workflow_data["statuses"].append({
                        "name": status_name,
                        "statusCategory": to_status.get("statusCategory", {"name": "Unknown"})
                    })
                
                # Add transition
                workflow_data["transitions"].append({
                    "name": transition["name"],
                    "from": current_status_info["name"],
                    "to": status_name
                })
        
        logger.warning(f"Strategy 3 used (limited data): {len(workflow_data['statuses'])} statuses from sample issue")
        return workflow_data

    def _generate_logical_transitions_from_status_categories(self, workflow_data: dict) -> None:
        """Generate logical workflow transitions based on status categories."""
        statuses = workflow_data["statuses"]
        
        # Group statuses by category
        to_do_statuses = [s for s in statuses if s["statusCategory"]["name"] == "To Do"]
        in_progress_statuses = [s for s in statuses if s["statusCategory"]["name"] == "In Progress"] 
        done_statuses = [s for s in statuses if s["statusCategory"]["name"] == "Done"]
        
        transitions = []
        
        # To Do → In Progress transitions
        for to_do in to_do_statuses:
            for in_progress in in_progress_statuses:
                transitions.append({
                    "name": f"Start {in_progress['name']}",
                    "from": to_do["name"],
                    "to": in_progress["name"]
                })
        
        # In Progress → Done transitions  
        for in_progress in in_progress_statuses:
            for done in done_statuses:
                transitions.append({
                    "name": f"Complete to {done['name']}",
                    "from": in_progress["name"],
                    "to": done["name"]
                })
        
        # In Progress ↔ In Progress transitions (for workflow steps)
        for i, from_status in enumerate(in_progress_statuses):
            for j, to_status in enumerate(in_progress_statuses):
                if i != j:
                    transitions.append({
                        "name": f"Move to {to_status['name']}", 
                        "from": from_status["name"],
                        "to": to_status["name"]
                    })
        
        # Done → Done transitions (for workflow completion paths)
        # E.g., Ready for Test → Done, Ready for Build → Done
        final_done_status = self._identify_final_done_status(done_statuses)
        for done_status in done_statuses:
            if done_status["name"] != final_done_status:
                transitions.append({
                    "name": f"Complete to {final_done_status}",
                    "from": done_status["name"], 
                    "to": final_done_status
                })
        
        # Done → In Progress transitions (for rework scenarios)
        # E.g., Ready for Test → In Progress (testing failed), Ready for Build → In Progress (build failed)
        for done_status in done_statuses:
            if done_status["name"] != final_done_status:
                # Allow rework back to primary In Progress status
                primary_in_progress = self._identify_primary_in_progress_status(in_progress_statuses)
                if primary_in_progress:
                    transitions.append({
                        "name": f"Rework from {done_status['name']}",
                        "from": done_status["name"],
                        "to": primary_in_progress
                    })
        
        workflow_data["transitions"] = transitions

    def _identify_final_done_status(self, done_statuses: list) -> str:
        """Identify the final 'Done' status from multiple Done statuses."""
        if not done_statuses:
            return "Done"
        
        # Look for status explicitly named "Done" first
        for status in done_statuses:
            if status["name"].lower() == "done":
                return status["name"]
        
        # Fallback to the first Done status
        return done_statuses[0]["name"]

    def _identify_primary_in_progress_status(self, in_progress_statuses: list) -> str:
        """Identify the primary 'In Progress' status for rework scenarios."""
        if not in_progress_statuses:
            return None
        
        # Look for status explicitly named "In Progress" first  
        for status in in_progress_statuses:
            if status["name"].lower() == "in progress":
                return status["name"]
        
        # Fallback to the first In Progress status
        return in_progress_statuses[0]["name"]

    def _raise_workflow_unavailable_error(self, project_key: str, issue_type: str, failed_strategies: list = None) -> None:
        """Raise comprehensive error when all workflow extraction strategies fail."""
        if failed_strategies:
            strategy_details = []
            for failure in failed_strategies:
                strategy_details.append(f"{failure['strategy']}: {failure['reason']}")
            strategy_info = f"Failed strategies: {'; '.join(strategy_details)}"
        else:
            strategy_info = "All workflow extraction strategies failed"
        
        error_message = (
            f"Cannot retrieve workflow data for {project_key}::{issue_type}. "
            f"{strategy_info}. "
            f"Solutions: Create a sample {issue_type} issue in {project_key}, "
            f"verify API permissions for workflow schema access, or "
            f"confirm the issue type is valid for this project."
        )
        
        logger.error(error_message)
        raise Exception(error_message)

    async def get_project_workflow_scheme(self, project_key: str, instance_name: str) -> dict[str, Any]:
        """Get comprehensive workflow scheme data for entire project."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get project metadata
            project_metadata = await self._get_project_metadata_with_validation(client, project_key)
            
            # Discover available issue types for this project
            available_issue_types = await self._extract_issue_types_from_project_statuses(client, project_key)
            
            # Build comprehensive workflow data for all issue types
            issue_type_workflows = await self._build_comprehensive_project_workflows(
                client, project_key, available_issue_types, instance_name
            )
            
            # Try to get workflow scheme metadata (best effort)
            workflow_scheme_metadata = await self._get_workflow_scheme_metadata_if_available(client, project_key)
            
            # Assemble final comprehensive response
            comprehensive_workflow_data = {
                "project": project_metadata,
                "workflow_scheme": workflow_scheme_metadata,
                "issue_type_workflows": issue_type_workflows
            }
            
            logger.info(f"Successfully retrieved comprehensive workflow data for {project_key}: "
                       f"{len(available_issue_types)} issue types, "
                       f"{len(issue_type_workflows)} workflows assembled")
            
            return comprehensive_workflow_data
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive workflow scheme for {project_key}: {str(e)}")
            raise

    async def _get_project_metadata_with_validation(self, client: Jira, project_key: str) -> dict[str, Any]:
        """Get project details with clear error handling for non-existent projects."""
        try:
            project_data = await asyncio.to_thread(client.project, project_key)
            return {
                "key": project_data.get("key"),
                "name": project_data.get("name"),
                "id": project_data.get("id"),
                "description": project_data.get("description"),
                "lead": project_data.get("lead", {}).get("displayName")
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                raise Exception(f"Project {project_key} does not exist or is not accessible")
            raise Exception(f"Failed to retrieve project metadata for {project_key}: {str(e)}")

    async def _extract_issue_types_from_project_statuses(self, client: Jira, project_key: str) -> list[str]:
        """Extract issue type names from project statuses API response."""
        try:
            project_statuses_url = f"rest/api/3/project/{project_key}/statuses"
            project_statuses_by_issue_type = await asyncio.to_thread(client.get, project_statuses_url)
            
            discovered_issue_types = []
            for issue_type_data in project_statuses_by_issue_type:
                issue_type_name = issue_type_data.get("name")
                if issue_type_name:
                    discovered_issue_types.append(issue_type_name)
            
            if not discovered_issue_types:
                raise Exception(f"No issue types found for project {project_key}")
                
            logger.info(f"Discovered {len(discovered_issue_types)} issue types in {project_key}: {discovered_issue_types}")
            return discovered_issue_types
            
        except Exception as e:
            raise Exception(f"Failed to discover issue types for {project_key}: {str(e)}")

    async def _build_comprehensive_project_workflows(
        self, client: Jira, project_key: str, issue_types: list[str], instance_name: str
    ) -> dict[str, Any]:
        """Build comprehensive workflow data for all issue types in project."""
        comprehensive_workflows = {}
        successful_workflows = 0
        failed_workflows = []
        
        for issue_type in issue_types:
            try:
                logger.info(f"Retrieving workflow data for {project_key}::{issue_type}")
                workflow_data = await self.get_workflow_data(project_key, issue_type, instance_name)
                
                # Structure the data for the comprehensive response
                comprehensive_workflows[issue_type] = {
                    "workflow": {
                        "statuses": workflow_data["statuses"],
                        "transitions": workflow_data["transitions"],
                        "metadata": {
                            "extraction_strategy_used": self._determine_extraction_strategy_used(workflow_data),
                            "status_count": len(workflow_data["statuses"]),
                            "transition_count": len(workflow_data["transitions"])
                        }
                    }
                }
                successful_workflows += 1
                logger.info(f"Successfully retrieved workflow for {issue_type}: "
                           f"{len(workflow_data['statuses'])} statuses, {len(workflow_data['transitions'])} transitions")
                
            except Exception as workflow_error:
                error_message = f"Failed to get workflow for {project_key}::{issue_type}: {str(workflow_error)}"
                logger.warning(error_message)
                failed_workflows.append({"issue_type": issue_type, "error": str(workflow_error)})
                
                # Continue with other issue types - partial success is acceptable
                continue
        
        if successful_workflows == 0:
            raise Exception(f"Failed to retrieve workflows for any issue type in {project_key}. "
                          f"Failed issue types: {[fw['issue_type'] for fw in failed_workflows]}")
        
        if failed_workflows:
            logger.warning(f"Partial success for {project_key}: {successful_workflows} successful, "
                          f"{len(failed_workflows)} failed workflow retrievals")
        
        return comprehensive_workflows

    def _determine_extraction_strategy_used(self, workflow_data: dict) -> str:
        """Determine which extraction strategy was used based on workflow data characteristics."""
        if "workflow_scheme" in workflow_data:
            return "direct_schema_access"
        elif len(workflow_data.get("transitions", [])) > 0:
            # Check if transitions look like generated logical transitions
            transitions = workflow_data["transitions"]
            generated_pattern_count = sum(1 for t in transitions if 
                                        t["name"].startswith("Start ") or 
                                        t["name"].startswith("Complete to ") or 
                                        t["name"].startswith("Move to "))
            if generated_pattern_count > len(transitions) * 0.5:
                return "project_statuses_with_logical_transitions"
            else:
                return "sample_issue_extraction"
        else:
            return "unknown_strategy"

    async def _get_workflow_scheme_metadata_if_available(self, client: Jira, project_key: str) -> dict[str, Any]:
        """Try to get workflow scheme metadata - best effort, graceful failure."""
        try:
            scheme_url = f"rest/api/3/project/{project_key}/workflowscheme"
            workflow_scheme_data = await asyncio.to_thread(client.get, scheme_url)
            
            return {
                "id": workflow_scheme_data.get("id"),
                "name": workflow_scheme_data.get("name"),
                "description": workflow_scheme_data.get("description"),
                "is_default": workflow_scheme_data.get("isDefault", False),
                "issue_type_mappings": workflow_scheme_data.get("issueTypeMappings", {}),
                "default_workflow": workflow_scheme_data.get("defaultWorkflow")
            }
            
        except Exception as scheme_error:
            logger.info(f"Could not retrieve workflow scheme metadata for {project_key}: {str(scheme_error)}")
            return {
                "id": None,
                "name": "Unknown Workflow Scheme",
                "description": "Workflow scheme metadata not accessible",
                "is_default": None,
                "issue_type_mappings": {},
                "default_workflow": None,
                "access_error": str(scheme_error)
            }
