"""
MCP server implementation for the Jira MCP server.

This module defines Jira-specific tools and resources for the MCP server.
"""

from typing import List, Dict, Any, Optional
from jira import JIRA
from mcp.server.fastmcp import FastMCP
from config import settings
import logging

logger = logging.getLogger(__name__)


def create_jira_client():
    """
    Create a JIRA client instance using configuration from settings.
    
    Returns:
        JIRA: A configured JIRA client instance
    """
    try:
        jira = JIRA(
            server=settings.JIRA_URL,
            basic_auth=(settings.JIRA_USER, settings.JIRA_TOKEN)
        )
        return jira
    except Exception as e:
        logger.error(f"Failed to create JIRA client: {e}")
        raise Exception(f"Failed to create JIRA client: {e}")


def test_jira_connection() -> Dict[str, Any]:
    """
    Test the connection to Jira and return status information.
    
    Returns:
        Dict containing connection status and server info
    """
    import datetime
    
    try:
        jira = create_jira_client()
        server_info = jira.server_info()
        
        return {
            "connected": True,
            "server_title": server_info.get("serverTitle", "Unknown"),
            "version": server_info.get("version", "Unknown"),
            "build_number": server_info.get("buildNumber", "Unknown"),
            "base_url": server_info.get("baseUrl", settings.JIRA_URL),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "configured_url": settings.JIRA_URL,
            "configured_user": settings.JIRA_USER,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }


def register_tools_and_resources(srv: FastMCP):
    """
    Register Jira tools and resources with the provided MCP server instance.
    
    Args:
        srv: A FastMCP server instance to register tools and resources with
    """
    
    # Health check tool
    @srv.tool()
    def health_check() -> Dict[str, Any]:
        """
        Check the health of the Jira MCP server and its connection to Jira.
        
        Returns:
            A dictionary containing health status information
        """
        try:
            # Test Jira connection
            connection_status = test_jira_connection()
            
            return {
                "server_status": "healthy",
                "server_name": settings.server_name,
                "jira_connection": connection_status,
                "configuration": {
                    "jira_url": settings.JIRA_URL,
                    "jira_user": settings.JIRA_USER,
                    "has_token": bool(settings.JIRA_TOKEN)
                }
            }
        except Exception as e:
            return {
                "server_status": "unhealthy",
                "error": str(e)
            }
    
    # Jira tool to list all projects
    @srv.tool()
    def list_jira_projects() -> Dict[str, List[Dict[str, str]]]:
        """
        List all projects available in the Jira instance.
        
        Returns:
            A dictionary containing a list of Jira projects
        """
        try:
            jira = create_jira_client()
            projects = jira.projects()
            
            # Extract relevant information from each project
            project_list = []
            for project in projects:
                project_list.append({
                    "key": project.key,
                    "name": project.name,
                    "id": project.id
                })
            
            return {"projects": project_list}
        except Exception as e:
            return {"error": str(e)}
    
    # Jira tool to get issue details (alias for consistency)
    @srv.tool()
    def jira_get_issue(issue_key: str) -> Dict[str, Any]:
        """
        Get details of a specific issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            
        Returns:
            A dictionary containing issue details
        """
        try:
            jira = create_jira_client()
            issue = jira.issue(issue_key)
            
            # Extract the most relevant information from the issue
            fields = issue.fields
            
            issue_details = {
                "key": issue.key,
                "id": issue.id,
                "summary": fields.summary,
                "description": fields.description or "",
                "status": fields.status.name,
                "priority": fields.priority.name if hasattr(fields, 'priority') and fields.priority else "None",
                "assignee": fields.assignee.displayName if fields.assignee else "Unassigned",
                "reporter": fields.reporter.displayName if fields.reporter else "Unknown",
                "created": fields.created,
                "updated": fields.updated,
                "components": [c.name for c in fields.components] if fields.components else [],
                "labels": fields.labels if fields.labels else []
            }
            
            return {"issue": issue_details}
        except Exception as e:
            return {"error": str(e)}

    # Add a Jira tool to get issue details (original name for backward compatibility)
    @srv.tool()
    def get_issue_details(issue_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Jira issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            
        Returns:
            A dictionary containing issue details
        """
        try:
            jira = create_jira_client()
            issue = jira.issue(issue_key)
            
            # Extract the most relevant information from the issue
            fields = issue.fields
            
            issue_details = {
                "key": issue.key,
                "id": issue.id,
                "summary": fields.summary,
                "description": fields.description or "",
                "status": fields.status.name,
                "priority": fields.priority.name if hasattr(fields, 'priority') and fields.priority else "None",
                "assignee": fields.assignee.displayName if fields.assignee else "Unassigned",
                "reporter": fields.reporter.displayName if fields.reporter else "Unknown",
                "created": fields.created,
                "updated": fields.updated,
                "components": [c.name for c in fields.components] if fields.components else [],
                "labels": fields.labels if fields.labels else []
            }
            
            return {"issue": issue_details}
        except Exception as e:
            return {"error": str(e)}
            
    # Add a Jira tool to get comprehensive issue details with formatting options
    @srv.tool()
    def get_full_issue_details(
        issue_key: str,
        raw_data: bool = False,
        format: str = "formatted"
    ) -> Dict[str, Any]:
        """
        Get comprehensive information about a specific Jira issue with formatting options.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            raw_data: If True, returns the minimally processed raw data from Jira API (default: False)
            format: Output format when raw_data is False - can be "formatted" (YAML-like) or "summary" (default: "formatted")
            
        Returns:
            A dictionary containing issue details in the requested format
        """
        try:
            jira = create_jira_client()
            issue = jira.issue(issue_key)
            fields = issue.fields
            
            # Get comments for the issue
            comments = jira.comments(issue_key)
            formatted_comments = []
            for comment in comments:
                comment_dict = {
                    "id": comment.id,
                    "author": {
                        "name": comment.author.displayName if hasattr(comment.author, 'displayName') else str(comment.author),
                        "key": comment.author.key if hasattr(comment.author, 'key') else None
                    },
                    "body": comment.body,
                    "created": comment.created,
                    "updated": comment.updated if hasattr(comment, 'updated') else None
                }
                formatted_comments.append(comment_dict)
            
            # Sort comments in reverse chronological order (newest first)
            formatted_comments = sorted(formatted_comments, key=lambda c: c["created"], reverse=True)
            
            # If raw data is requested, return minimally processed data
            if raw_data:
                return {
                    "issue": issue.raw,
                    "comments": formatted_comments,
                    "comment_count": len(formatted_comments)
                }
            
            # Get custom field mappings for human-readable names
            try:
                # Use the function directly since we're in the same scope
                field_mappings = get_custom_field_mappings()
                custom_field_names = {field_id: field_info[0] for field_id, field_info in field_mappings.get("mappings", {}).items()}
            except:
                # If mapping fails, use raw field IDs
                custom_field_names = {}
            
            # Extract key fields for the header section
            summary_fields = {
                "key": issue.key,
                "id": issue.id,
                "summary": fields.summary,
                "status": fields.status.name,
                "priority": fields.priority.name if hasattr(fields, 'priority') and fields.priority else "None",
                "assignee": fields.assignee.displayName if fields.assignee else "Unassigned",
                "reporter": fields.reporter.displayName if fields.reporter else "Unknown",
                "created": fields.created,
                "updated": fields.updated,
            }
            
            # Extract custom fields (anything starting with customfield_)
            custom_fields = {}
            for field_name in dir(fields):
                if field_name.startswith('customfield_'):
                    value = getattr(fields, field_name)
                    if value is not None:  # Only include non-None values
                        # Look up custom field name from mappings
                        field_label = custom_field_names.get(field_name, field_name)
                        custom_fields[field_label] = value
            
            # Format based on requested format
            if format == "summary":
                # Similar to current get_issue_details but with comments
                result = {
                    "issue": summary_fields,
                    "description": fields.description or "",
                    "components": [c.name for c in fields.components] if fields.components else [],
                    "labels": fields.labels if fields.labels else [],
                    "comments": formatted_comments,
                    "comment_count": len(formatted_comments)
                }
            else:  # "formatted" or any other value defaults to full formatted output
                result = {
                    "issue": summary_fields,
                    "description": fields.description or "",
                    "custom_fields": custom_fields,
                    "components": [c.name for c in fields.components] if fields.components else [],
                    "labels": fields.labels if fields.labels else [],
                    "comments": formatted_comments,
                    "comment_count": len(formatted_comments)
                }
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    # Jira tool to create a new issue (alias for consistency)
    @srv.tool()
    def jira_create_issue(
        project_key: str, 
        summary: str, 
        description: str, 
        issue_type: str = "Story",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue.
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            summary: The ticket summary/title
            description: The ticket description
            issue_type: The issue type (Story, Task, Epic, Bug) - defaults to "Story"
            priority: Optional priority (e.g., "High", "Medium", "Low")
            assignee: Optional username to assign the ticket to
            labels: Optional list of labels to apply to the ticket
            
        Returns:
            A dictionary containing the created issue details
        """
        try:
            jira = create_jira_client()
            
            # Validate issue type (convert to proper case if needed)
            valid_types = ["Story", "Task", "Epic", "Bug"]
            issue_type_proper = next((t for t in valid_types if t.lower() == issue_type.lower()), None)
            if not issue_type_proper:
                raise ValueError(f"Invalid issue type: {issue_type}. Valid types are: {', '.join(valid_types)}")
            
            # Prepare the issue fields
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type_proper},
            }
            
            # Add optional fields if provided
            if priority:
                issue_dict['priority'] = {'name': priority}
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            if labels:
                issue_dict['labels'] = labels
            
            # Create the issue
            new_issue = jira.create_issue(fields=issue_dict)
            
            # Return the issue details in a structured format
            return {
                "created": True,
                "key": new_issue.key,
                "id": new_issue.id,
                "self": new_issue.self,
                "url": f"{settings.JIRA_URL}/browse/{new_issue.key}"
            }
        except Exception as e:
            return {"error": str(e), "created": False}

    # Jira tool to create a new ticket (original name for backward compatibility)
    @srv.tool()
    def create_jira_ticket(
        project_key: str, 
        summary: str, 
        description: str, 
        issue_type: str = "Story",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jira ticket (issue).
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            summary: The ticket summary/title
            description: The ticket description
            issue_type: The issue type (Story, Task, Epic, Bug) - defaults to "Story"
            priority: Optional priority (e.g., "High", "Medium", "Low")
            assignee: Optional username to assign the ticket to
            labels: Optional list of labels to apply to the ticket
            
        Returns:
            A dictionary containing the created issue details
        """
        try:
            jira = create_jira_client()
            
            # Validate issue type (convert to proper case if needed)
            valid_types = ["Story", "Task", "Epic", "Bug"]
            issue_type_proper = next((t for t in valid_types if t.lower() == issue_type.lower()), None)
            if not issue_type_proper:
                raise ValueError(f"Invalid issue type: {issue_type}. Valid types are: {', '.join(valid_types)}")
            
            # Prepare the issue fields
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type_proper},
            }
            
            # Add optional fields if provided
            if priority:
                issue_dict['priority'] = {'name': priority}
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            if labels:
                issue_dict['labels'] = labels
            
            # Create the issue
            new_issue = jira.create_issue(fields=issue_dict)
            
            # Return the issue details in a structured format
            return {
                "created": True,
                "key": new_issue.key,
                "id": new_issue.id,
                "self": new_issue.self,
                "url": f"{settings.JIRA_URL}/browse/{new_issue.key}"
            }
        except Exception as e:
            return {"error": str(e), "created": False}
    
    # Jira tool to add a comment (alias for consistency)
    @srv.tool()
    def jira_add_comment(
        issue_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            comment: The comment text to add
            
        Returns:
            A dictionary containing the comment details and status
        """
        try:
            jira = create_jira_client()
            
            # Verify the issue exists
            issue = jira.issue(issue_key)
            
            # Add the comment
            comment_obj = jira.add_comment(issue_key, comment)
            
            return {
                "added": True,
                "issue_key": issue_key,
                "comment_id": comment_obj.id,
                "comment_author": comment_obj.author.displayName if hasattr(comment_obj, 'author') else settings.JIRA_USER,
                "comment_body": comment_obj.body,
                "url": f"{settings.JIRA_URL}/browse/{issue_key}?focusedCommentId={comment_obj.id}"
            }
        except Exception as e:
            return {"error": str(e), "added": False}

    # Jira tool to add a comment to an existing ticket (original name for backward compatibility)
    @srv.tool()
    def add_comment_to_jira_ticket(
        issue_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to an existing Jira ticket.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            comment: The comment text to add
            
        Returns:
            A dictionary containing the comment details and status
        """
        try:
            jira = create_jira_client()
            
            # Verify the issue exists
            issue = jira.issue(issue_key)
            
            # Add the comment
            comment_obj = jira.add_comment(issue_key, comment)
            
            return {
                "added": True,
                "issue_key": issue_key,
                "comment_id": comment_obj.id,
                "comment_author": comment_obj.author.displayName if hasattr(comment_obj, 'author') else settings.JIRA_USER,
                "comment_body": comment_obj.body,
                "url": f"{settings.JIRA_URL}/browse/{issue_key}?focusedCommentId={comment_obj.id}"
            }
        except Exception as e:
            return {"error": str(e), "added": False}
    
    # Jira tool to get custom field mappings
    @srv.tool()
    def get_custom_field_mappings(reverse: bool = False) -> Dict[str, Any]:
        """
        Get mappings between Jira custom field IDs and their names/descriptions. If you have a dataset
        with custom field IDs such as the way data gets returned from the Jira API, you can use this to translate to 
        human-readable names. Similarly if you need to map from human-readable names to IDs, you can use the reverse option.
        This is useful for understanding the custom fields in your Jira instance.
        
                
        Args:
            reverse: If False (default), map from field_id to (name, description)
                    If True, map from name to (field_id, description)
            
        Returns:
            A dictionary containing the custom field mappings
        """
        try:
            jira = create_jira_client()
            
            # Fetch all fields from Jira
            fields = jira.fields()
            
            # Filter for custom fields (those with IDs starting with "customfield_")
            custom_fields = [field for field in fields if field['id'].startswith('customfield_')]
            
            # Create mappings
            mappings = {}
            
            if not reverse:
                # Forward mapping: field_id -> [name, description]
                for field in custom_fields:
                    field_id = field['id']
                    name = field['name']
                    description = field.get('description', "")
                    mappings[field_id] = [name, description]
            else:
                # Reverse mapping: name -> [field_id, description]
                for field in custom_fields:
                    field_id = field['id']
                    name = field['name']
                    description = field.get('description', "")
                    mappings[name] = [field_id, description]
            
            return {
                "mappings": mappings,
                "count": len(mappings),
                "mapping_direction": "name_to_id" if reverse else "id_to_name"
            }
        except Exception as e:
            return {"error": str(e)}
    
    # Jira tool to search issues using JQL
    @srv.tool()
    def jira_search(
        jql: str,
        max_results: int = 50,
        start_at: int = 0
    ) -> Dict[str, Any]:
        """
        Search issues using JQL (Jira Query Language).
        
        Args:
            jql: The JQL query string (e.g., "project = PROJ AND status = 'In Progress'")
            max_results: Maximum number of results to return (default 50)
            start_at: Starting index for pagination (default 0)
            
        Returns:
            A dictionary containing search results
        """
        try:
            jira = create_jira_client()
            
            # Execute the JQL search
            issues = jira.search_issues(jql, maxResults=max_results, startAt=start_at)
            
            # Extract relevant information from each issue
            issue_list = []
            for issue in issues:
                fields = issue.fields
                issue_data = {
                    "key": issue.key,
                    "id": issue.id,
                    "summary": fields.summary,
                    "status": fields.status.name,
                    "issue_type": fields.issuetype.name,
                    "priority": fields.priority.name if hasattr(fields, 'priority') and fields.priority else "None",
                    "assignee": fields.assignee.displayName if fields.assignee else "Unassigned",
                    "reporter": fields.reporter.displayName if fields.reporter else "Unknown",
                    "created": fields.created,
                    "updated": fields.updated,
                    "url": f"{settings.JIRA_URL}/browse/{issue.key}"
                }
                issue_list.append(issue_data)
            
            return {
                "jql": jql,
                "total_results": len(issue_list),
                "start_at": start_at,
                "max_results": max_results,
                "issues": issue_list
            }
        except Exception as e:
            return {"error": str(e)}
    
    # Jira tool to update an existing issue
    @srv.tool()
    def jira_update_issue(
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            summary: Optional new summary/title
            description: Optional new description
            priority: Optional new priority (e.g., "High", "Medium", "Low")
            assignee: Optional new assignee username
            labels: Optional new list of labels (replaces existing labels)
            
        Returns:
            A dictionary containing the update status
        """
        try:
            jira = create_jira_client()
            
            # Get the issue to verify it exists
            issue = jira.issue(issue_key)
            
            # Build the update fields dictionary
            update_fields = {}
            
            if summary is not None:
                update_fields['summary'] = summary
            if description is not None:
                update_fields['description'] = description
            if priority is not None:
                update_fields['priority'] = {'name': priority}
            if assignee is not None:
                update_fields['assignee'] = {'name': assignee}
            if labels is not None:
                update_fields['labels'] = labels
            
            if not update_fields:
                return {"error": "No fields provided to update", "updated": False}
            
            # Update the issue
            issue.update(fields=update_fields)
            
            return {
                "updated": True,
                "issue_key": issue_key,
                "updated_fields": list(update_fields.keys()),
                "url": f"{settings.JIRA_URL}/browse/{issue_key}"
            }
        except Exception as e:
            return {"error": str(e), "updated": False}
    
    # Jira tool to transition an issue to a new status
    @srv.tool()
    def jira_transition_issue(
        issue_key: str,
        transition_name: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transition an issue to a new status.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            transition_name: The name of the transition (e.g., "In Progress", "Done", "Close Issue")
            comment: Optional comment to add during the transition
            
        Returns:
            A dictionary containing the transition status
        """
        try:
            jira = create_jira_client()
            
            # Get the issue to verify it exists
            issue = jira.issue(issue_key)
            
            # Get available transitions for this issue
            transitions = jira.transitions(issue)
            
            # Find the matching transition
            target_transition = None
            for transition in transitions:
                if transition['name'].lower() == transition_name.lower():
                    target_transition = transition
                    break
            
            if not target_transition:
                available_transitions = [t['name'] for t in transitions]
                return {
                    "error": f"Transition '{transition_name}' not available for issue {issue_key}",
                    "available_transitions": available_transitions,
                    "transitioned": False
                }
            
            # Prepare transition data
            transition_data = {}
            if comment:
                transition_data['comment'] = [{'add': {'body': comment}}]
            
            # Perform the transition
            jira.transition_issue(issue, target_transition['id'], **transition_data)
            
            # Get updated issue to confirm new status
            updated_issue = jira.issue(issue_key)
            
            return {
                "transitioned": True,
                "issue_key": issue_key,
                "from_status": issue.fields.status.name,
                "to_status": updated_issue.fields.status.name,
                "transition_used": target_transition['name'],
                "comment_added": bool(comment),
                "url": f"{settings.JIRA_URL}/browse/{issue_key}"
            }
        except Exception as e:
            return {"error": str(e), "transitioned": False}
    
    # Jira tool to list tickets in a project
    @srv.tool()
    def list_project_tickets(
        project_key: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        List tickets (issues) in a Jira project with optional filtering.
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            status: Optional filter by status (e.g., "In Progress", "Done")
            issue_type: Optional filter by issue type (e.g., "Story", "Bug")
            max_results: Maximum number of results to return (default 50)
            
        Returns:
            A dictionary containing a list of matching tickets
        """
        try:
            jira = create_jira_client()
            
            # Build the JQL query
            jql = f"project = {project_key}"
            
            if status:
                jql += f" AND status = '{status}'"
            
            if issue_type:
                jql += f" AND issuetype = '{issue_type}'"
            
            jql += " ORDER BY created DESC"
            
            # Execute the search
            issues = jira.search_issues(jql, maxResults=max_results)
            
            # Extract relevant information from each issue
            issue_list = []
            for issue in issues:
                fields = issue.fields
                issue_data = {
                    "key": issue.key,
                    "summary": fields.summary,
                    "status": fields.status.name,
                    "issue_type": fields.issuetype.name,
                    "priority": fields.priority.name if hasattr(fields, 'priority') and fields.priority else "None",
                    "assignee": fields.assignee.displayName if fields.assignee else "Unassigned",
                    "created": fields.created,
                    "updated": fields.updated,
                    "url": f"{settings.JIRA_URL}/browse/{issue.key}"
                }
                issue_list.append(issue_data)
            
            return {
                "project": project_key,
                "issues_count": len(issue_list),
                "issues": issue_list
            }
        except Exception as e:
            return {"error": str(e)}
    
    # Jira resource for project information
    @srv.resource("resource://jira/project/{project_key}")
    def project_resource(project_key: str) -> Dict[str, Any]:
        """
        Get information about a specific Jira project.
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            
        Returns:
            Project information
        """
        try:
            jira = create_jira_client()
            project = jira.project(project_key)
            
            # Get project lead information if available
            lead_info = {}
            if hasattr(project, 'lead'):
                lead = project.lead
                lead_info = {
                    "name": lead.displayName if hasattr(lead, 'displayName') else "Unknown",
                    "email": lead.emailAddress if hasattr(lead, 'emailAddress') else "Unknown"
                }
            
            return {
                "key": project.key,
                "name": project.name,
                "id": project.id,
                "lead": lead_info,
                "url": f"{settings.JIRA_URL}/projects/{project.key}"
            }
        except Exception as e:
            return {"error": str(e)}
    
    # Resource to list all known Jira instances
    @srv.resource("resource://jira/instances")
    def jira_instances_resource() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about all known Jira instances.
        
        This resource currently returns only the single Jira instance configured in settings,
        but could be expanded in the future to support multiple Jira instances.
        
        Returns:
            A dictionary containing a list of Jira instances
        """
        # Currently we only have one Jira instance configured
        # In the future, this could be expanded to support multiple instances
        instances = [{
            "name": "Primary Jira Instance",
            "url": settings.JIRA_URL,
            "user": settings.JIRA_USER,
            "has_token": bool(settings.JIRA_TOKEN),
            "description": "The primary Jira instance configured for this MCP server"
        }]
        
        return {
            "instances": instances,
            "count": len(instances)
        }
