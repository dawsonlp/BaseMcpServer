"""
MCP server implementation for the Jira clone server.

This module defines Jira-specific tools and resources for the MCP server.
"""

from typing import List, Dict, Any, Optional
from jira import JIRA
from mcp.server.fastmcp import FastMCP
from config import settings


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
        raise Exception(f"Failed to create JIRA client: {e}")


def register_tools_and_resources(mcp: FastMCP):
    """
    Register Jira tools and resources with the provided MCP server instance.
    
    Args:
        mcp: A FastMCP server instance to register tools and resources with
    """
    # Jira tool to list all projects
    @mcp.tool()
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
    
    # Add a Jira tool to get issue details
    @mcp.tool()
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
    
    # Jira tool to create a new ticket
    @mcp.tool()
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
    
    # Jira tool to add a comment to an existing ticket
    @mcp.tool()
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
    
    # Jira tool to list tickets in a project
    @mcp.tool()
    def list_project_tickets(
        project_key: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
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
    @mcp.resource("resource://jira/project/{project_key}")
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
    @mcp.resource("resource://jira/instances")
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
