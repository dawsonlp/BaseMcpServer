"""
MCP server implementation for the Jira helper server.

This module defines Jira-specific tools and resources for the MCP server.
Supports multiple Jira instances, workflow transitions, and assignee management.
"""

from typing import List, Dict, Any, Optional
import base64
import io
import tempfile
import os
from jira import JIRA
from mcp.server.fastmcp import FastMCP
from config import settings, JiraInstance

try:
    import graphviz
    import networkx as nx
    GRAPH_SUPPORT = True
except ImportError:
    GRAPH_SUPPORT = False


def create_jira_client(instance_name: Optional[str] = None) -> JIRA:
    """
    Create a JIRA client instance for the specified instance.
    
    Args:
        instance_name: Name of the Jira instance to connect to. If None, uses default instance.
    
    Returns:
        JIRA: A configured JIRA client instance
        
    Raises:
        Exception: If the instance is not found or client creation fails
    """
    instances = settings.get_jira_instances()
    
    if not instances:
        raise Exception("No Jira instances configured")
    
    # Use default instance if none specified
    if instance_name is None:
        instance_name = settings.get_default_instance_name()
        if instance_name is None:
            raise Exception("No default Jira instance available")
    
    # Get the specified instance
    if instance_name not in instances:
        available = ", ".join(instances.keys())
        raise Exception(f"Jira instance '{instance_name}' not found. Available instances: {available}")
    
    instance = instances[instance_name]
    
    try:
        jira = JIRA(
            server=instance.url,
            basic_auth=(instance.user, instance.token)
        )
        return jira
    except Exception as e:
        raise Exception(f"Failed to create JIRA client for instance '{instance_name}': {e}")


def get_available_instances() -> Dict[str, JiraInstance]:
    """
    Get all available Jira instances.
    
    Returns:
        Dict[str, JiraInstance]: Dictionary of available instances
    """
    return settings.get_jira_instances()


def register_tools_and_resources(srv: FastMCP):
    """
    Register Jira tools and resources with the provided MCP server instance.
    
    Args:
        srv: A FastMCP server instance to register tools and resources with
    """
    # Jira tool to list all projects
    @srv.tool()
    def list_jira_projects(instance_name: Optional[str] = None) -> Dict[str, Any]:
        """
        List all projects available in the Jira instance.
        
        Args:
            instance_name: Name of the Jira instance to use. If None, uses default instance.
        
        Returns:
            A dictionary containing a list of Jira projects
        """
        try:
            jira = create_jira_client(instance_name)
            projects = jira.projects()
            
            # Extract relevant information from each project
            project_list = []
            for project in projects:
                project_list.append({
                    "key": project.key,
                    "name": project.name,
                    "id": project.id
                })
            
            used_instance = instance_name or settings.get_default_instance_name()
            return {
                "projects": project_list,
                "instance": used_instance,
                "count": len(project_list)
            }
        except Exception as e:
            return {"error": str(e)}
    
    # Add a Jira tool to get issue details
    @srv.tool()
    def get_issue_details(issue_key: str, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific Jira issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            instance_name: Name of the Jira instance to use. If None, uses default instance.
            
        Returns:
            A dictionary containing issue details
        """
        try:
            jira = create_jira_client(instance_name)
            issue = jira.issue(issue_key)
            used_instance = instance_name or settings.get_default_instance_name()
            
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
            
            return {
                "issue": issue_details,
                "instance": used_instance
            }
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
    
    # Jira tool to create a new ticket
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
    
    # Jira tool to add a comment to an existing ticket
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
    
    # Jira tool to list tickets in a project
    @srv.tool()
    def list_project_tickets(
        project_key: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List tickets (issues) in a Jira project with optional filtering.
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            status: Optional filter by status (e.g., "In Progress", "Done")
            issue_type: Optional filter by issue type (e.g., "Story", "Bug")
            max_results: Maximum number of results to return (default 50)
            instance_name: Name of the Jira instance to use. If None, uses default instance.
            
        Returns:
            A dictionary containing a list of matching tickets
        """
        try:
            jira = create_jira_client(instance_name)
            instances = settings.get_jira_instances()
            used_instance = instance_name or settings.get_default_instance_name()
            instance_url = instances[used_instance].url if used_instance in instances else settings.JIRA_URL
            
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
                    "url": f"{instance_url}/browse/{issue.key}"
                }
                issue_list.append(issue_data)
            
            return {
                "project": project_key,
                "issues_count": len(issue_list),
                "issues": issue_list,
                "instance": used_instance
            }
        except Exception as e:
            return {"error": str(e)}
    
    # NEW: Jira tool to transition an issue through workflow
    @srv.tool()
    def transition_jira_issue(
        issue_key: str,
        transition_name: str,
        comment: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transition a Jira issue through its workflow (e.g., move from "To Do" to "In Progress").
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            transition_name: Name of the transition to execute (e.g., "Start Progress", "Done")
            comment: Optional comment to add when transitioning
            instance_name: Name of the Jira instance to use. If None, uses default instance.
            
        Returns:
            A dictionary containing the transition result and new status
        """
        try:
            jira = create_jira_client(instance_name)
            instances = settings.get_jira_instances()
            used_instance = instance_name or settings.get_default_instance_name()
            instance_url = instances[used_instance].url if used_instance in instances else settings.JIRA_URL
            
            # Get the issue to check current status
            issue = jira.issue(issue_key)
            old_status = issue.fields.status.name
            
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
                    "success": False,
                    "error": f"Transition '{transition_name}' not available for issue {issue_key}",
                    "available_transitions": available_transitions,
                    "current_status": old_status
                }
            
            # Prepare transition data
            transition_data = {}
            if comment:
                transition_data['comment'] = [{'add': {'body': comment}}]
            
            # Execute the transition
            jira.transition_issue(issue, target_transition['id'], **transition_data)
            
            # Get the updated issue to confirm new status
            updated_issue = jira.issue(issue_key)
            new_status = updated_issue.fields.status.name
            
            return {
                "success": True,
                "issue_key": issue_key,
                "transition_executed": target_transition['name'],
                "old_status": old_status,
                "new_status": new_status,
                "comment_added": bool(comment),
                "url": f"{instance_url}/browse/{issue_key}",
                "instance": used_instance
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # NEW: Jira tool to get available transitions for an issue
    @srv.tool()
    def get_issue_transitions(
        issue_key: str,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get available workflow transitions for a Jira issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            instance_name: Name of the Jira instance to use. If None, uses default instance.
            
        Returns:
            A dictionary containing available transitions and current status
        """
        try:
            jira = create_jira_client(instance_name)
            used_instance = instance_name or settings.get_default_instance_name()
            
            # Get the issue and its current status
            issue = jira.issue(issue_key)
            current_status = issue.fields.status.name
            
            # Get available transitions
            transitions = jira.transitions(issue)
            
            # Format transition information
            transition_list = []
            for transition in transitions:
                transition_info = {
                    "id": transition['id'],
                    "name": transition['name'],
                    "to_status": transition['to']['name'] if 'to' in transition else "Unknown"
                }
                transition_list.append(transition_info)
            
            return {
                "issue_key": issue_key,
                "current_status": current_status,
                "available_transitions": transition_list,
                "transition_count": len(transition_list),
                "instance": used_instance
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # NEW: Jira tool to change issue assignee
    @srv.tool()
    def change_issue_assignee(
        issue_key: str,
        assignee: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Change the assignee of a Jira issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJECT-123')
            assignee: Username or email of the new assignee. Use None or empty string to unassign.
            instance_name: Name of the Jira instance to use. If None, uses default instance.
            
        Returns:
            A dictionary containing the assignment result
        """
        try:
            jira = create_jira_client(instance_name)
            instances = settings.get_jira_instances()
            used_instance = instance_name or settings.get_default_instance_name()
            instance_url = instances[used_instance].url if used_instance in instances else settings.JIRA_URL
            
            # Get the issue to check current assignee
            issue = jira.issue(issue_key)
            old_assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
            
            # Prepare assignee data
            if assignee and assignee.strip():
                # Assign to specific user
                assignee_data = {'name': assignee.strip()}
                new_assignee_name = assignee.strip()
            else:
                # Unassign (set to None)
                assignee_data = {'name': None}
                new_assignee_name = "Unassigned"
            
            # Update the assignee
            jira.assign_issue(issue, assignee_data['name'])
            
            # Verify the change by getting the updated issue
            updated_issue = jira.issue(issue_key)
            actual_assignee = updated_issue.fields.assignee.displayName if updated_issue.fields.assignee else "Unassigned"
            
            return {
                "success": True,
                "issue_key": issue_key,
                "old_assignee": old_assignee,
                "new_assignee": actual_assignee,
                "requested_assignee": new_assignee_name,
                "url": f"{instance_url}/browse/{issue_key}",
                "instance": used_instance
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # NEW: Jira tool to list all available instances
    @srv.tool()
    def list_jira_instances() -> Dict[str, Any]:
        """
        List all configured Jira instances.
        
        Returns:
            A dictionary containing information about all configured Jira instances
        """
        try:
            instances = settings.get_jira_instances()
            default_instance = settings.get_default_instance_name()
            
            instance_list = []
            for name, instance in instances.items():
                instance_info = {
                    "name": name,
                    "url": instance.url,
                    "user": instance.user,
                    "description": instance.description,
                    "is_default": name == default_instance
                }
                instance_list.append(instance_info)
            
            return {
                "instances": instance_list,
                "count": len(instance_list),
                "default_instance": default_instance
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # NEW: Jira tool to generate workflow graph for a project
    @srv.tool()
    def generate_project_workflow_graph(
        project_key: str,
        issue_type: str = "Story",
        format: str = "svg",
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a visual workflow graph for a specific project and issue type.
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            issue_type: The issue type to analyze workflow for (default: "Story")
            format: Output format - "svg", "png", "dot", or "json" (default: "svg")
            instance_name: Name of the Jira instance to use. If None, uses default instance.
            
        Returns:
            A dictionary containing the workflow graph data
        """
        if not GRAPH_SUPPORT:
            return {
                "error": "Graph visualization libraries not available. Install graphviz and networkx packages.",
                "missing_packages": ["graphviz", "networkx"]
            }
        
        try:
            jira = create_jira_client(instance_name)
            instances = settings.get_jira_instances()
            used_instance = instance_name or settings.get_default_instance_name()
            instance_url = instances[used_instance].url if used_instance in instances else settings.JIRA_URL
            
            # Get project information
            project = jira.project(project_key)
            
            # Get a sample issue of the specified type to analyze workflow
            jql = f"project = {project_key} AND issuetype = '{issue_type}'"
            issues = jira.search_issues(jql, maxResults=1)
            
            if not issues:
                return {
                    "error": f"No issues of type '{issue_type}' found in project {project_key}",
                    "project": project_key,
                    "issue_type": issue_type
                }
            
            sample_issue = issues[0]
            
            # Get all possible transitions by analyzing the workflow
            # We'll use the Jira API to get workflow information
            try:
                # Get workflow scheme for the project
                workflow_data = jira._get_json(f"project/{project.id}/statuses")
                
                # Find the workflow for our issue type
                issue_type_workflows = None
                for item in workflow_data:
                    if item['name'].lower() == issue_type.lower():
                        issue_type_workflows = item['statuses']
                        break
                
                if not issue_type_workflows:
                    # Fallback: use transitions from sample issue
                    transitions = jira.transitions(sample_issue)
                    statuses = set([sample_issue.fields.status.name])
                    for trans in transitions:
                        if 'to' in trans:
                            statuses.add(trans['to']['name'])
                    
                    # Create a simple workflow from available transitions
                    workflow_graph = _create_simple_workflow_graph(jira, sample_issue, list(statuses))
                else:
                    # Create workflow graph from project workflow data
                    workflow_graph = _create_workflow_graph_from_statuses(issue_type_workflows)
                
            except Exception as workflow_error:
                # Fallback to analyzing transitions from sample issue
                workflow_graph = _create_fallback_workflow_graph(jira, sample_issue)
            
            # Generate the requested format
            if format.lower() == "json":
                return {
                    "success": True,
                    "project": project_key,
                    "issue_type": issue_type,
                    "workflow": workflow_graph,
                    "instance": used_instance,
                    "format": "json"
                }
            elif format.lower() == "dot":
                dot_content = _generate_dot_graph(workflow_graph, project_key, issue_type)
                return {
                    "success": True,
                    "project": project_key,
                    "issue_type": issue_type,
                    "dot_content": dot_content,
                    "instance": used_instance,
                    "format": "dot"
                }
            else:
                # Generate visual graph (SVG or PNG)
                graph_data = _generate_visual_graph(workflow_graph, project_key, issue_type, format)
                return {
                    "success": True,
                    "project": project_key,
                    "issue_type": issue_type,
                    "graph_data": graph_data,
                    "instance": used_instance,
                    "format": format,
                    "encoding": "base64"
                }
                
        except Exception as e:
            return {"error": str(e), "success": False}


def _create_workflow_graph_from_statuses(statuses_data):
    """Create workflow graph from Jira project status data."""
    workflow = {
        "nodes": [],
        "edges": [],
        "metadata": {}
    }
    
    # Extract statuses and their categories
    for status_info in statuses_data:
        status_name = status_info['name']
        category = status_info.get('statusCategory', {}).get('name', 'Unknown')
        
        workflow["nodes"].append({
            "id": status_name,
            "name": status_name,
            "category": category,
            "color": _get_status_color(category)
        })
    
    # For project-level workflow, we can't easily get transitions
    # So we'll create a logical flow based on categories
    todo_statuses = [n for n in workflow["nodes"] if n["category"] == "To Do"]
    progress_statuses = [n for n in workflow["nodes"] if n["category"] == "In Progress"]
    done_statuses = [n for n in workflow["nodes"] if n["category"] == "Done"]
    
    # Create logical transitions
    for todo in todo_statuses:
        for progress in progress_statuses:
            workflow["edges"].append({
                "from": todo["id"],
                "to": progress["id"],
                "label": "Start Progress"
            })
    
    for progress in progress_statuses:
        for done in done_statuses:
            workflow["edges"].append({
                "from": progress["id"],
                "to": done["id"],
                "label": "Complete"
            })
    
    return workflow


def _create_simple_workflow_graph(jira, sample_issue, all_statuses):
    """Create a simple workflow graph from available statuses."""
    workflow = {
        "nodes": [],
        "edges": [],
        "metadata": {"source": "status_analysis"}
    }
    
    # Add all statuses as nodes
    for status in all_statuses:
        # Try to get category information
        category = "Unknown"
        try:
            # This is a simplified categorization
            if any(word in status.lower() for word in ["todo", "open", "new", "backlog"]):
                category = "To Do"
            elif any(word in status.lower() for word in ["progress", "development", "review", "testing"]):
                category = "In Progress"
            elif any(word in status.lower() for word in ["done", "closed", "resolved", "complete"]):
                category = "Done"
        except:
            pass
        
        workflow["nodes"].append({
            "id": status,
            "name": status,
            "category": category,
            "color": _get_status_color(category)
        })
    
    # Get actual transitions from the sample issue
    try:
        transitions = jira.transitions(sample_issue)
        current_status = sample_issue.fields.status.name
        
        for transition in transitions:
            if 'to' in transition:
                workflow["edges"].append({
                    "from": current_status,
                    "to": transition['to']['name'],
                    "label": transition['name']
                })
    except:
        pass
    
    return workflow


def _create_fallback_workflow_graph(jira, sample_issue):
    """Create a fallback workflow graph when other methods fail."""
    workflow = {
        "nodes": [],
        "edges": [],
        "metadata": {"source": "fallback"}
    }
    
    current_status = sample_issue.fields.status.name
    
    # Add current status as a node
    workflow["nodes"].append({
        "id": current_status,
        "name": current_status,
        "category": "Current",
        "color": "#4CAF50"
    })
    
    # Get available transitions
    try:
        transitions = jira.transitions(sample_issue)
        
        for transition in transitions:
            if 'to' in transition:
                target_status = transition['to']['name']
                
                # Add target status as node if not already present
                if not any(node['id'] == target_status for node in workflow["nodes"]):
                    workflow["nodes"].append({
                        "id": target_status,
                        "name": target_status,
                        "category": "Available",
                        "color": "#2196F3"
                    })
                
                # Add transition edge
                workflow["edges"].append({
                    "from": current_status,
                    "to": target_status,
                    "label": transition['name']
                })
    except:
        pass
    
    return workflow


def _get_status_color(category):
    """Get color for status category."""
    color_map = {
        "To Do": "#FF9800",      # Orange
        "In Progress": "#2196F3", # Blue
        "Done": "#4CAF50",       # Green
        "Current": "#9C27B0",    # Purple
        "Available": "#607D8B",  # Blue Grey
        "Unknown": "#9E9E9E"     # Grey
    }
    return color_map.get(category, "#9E9E9E")


def _generate_dot_graph(workflow, project_key, issue_type):
    """Generate DOT format graph."""
    dot_lines = [
        f'digraph "{project_key}_{issue_type}_workflow" {{',
        '    rankdir=LR;',
        '    node [shape=box, style=rounded];',
        ''
    ]
    
    # Add nodes
    for node in workflow["nodes"]:
        color = node.get("color", "#9E9E9E")
        dot_lines.append(f'    "{node["id"]}" [label="{node["name"]}", fillcolor="{color}", style="filled,rounded"];')
    
    dot_lines.append('')
    
    # Add edges
    for edge in workflow["edges"]:
        label = edge.get("label", "")
        dot_lines.append(f'    "{edge["from"]}" -> "{edge["to"]}" [label="{label}"];')
    
    dot_lines.append('}')
    
    return '\n'.join(dot_lines)


def _generate_visual_graph(workflow, project_key, issue_type, format):
    """Generate visual graph in SVG or PNG format."""
    try:
        # Create Graphviz graph
        dot = graphviz.Digraph(comment=f'{project_key} {issue_type} Workflow')
        dot.attr(rankdir='LR')
        dot.attr('node', shape='box', style='rounded,filled')
        
        # Add nodes
        for node in workflow["nodes"]:
            color = node.get("color", "#9E9E9E")
            dot.node(node["id"], node["name"], fillcolor=color)
        
        # Add edges
        for edge in workflow["edges"]:
            label = edge.get("label", "")
            dot.edge(edge["from"], edge["to"], label=label)
        
        # Render to the specified format
        if format.lower() == "png":
            output_format = "png"
        else:
            output_format = "svg"
        
        # Use a temporary file to render
        with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as tmp_file:
            try:
                # Render the graph
                dot.render(tmp_file.name.replace(f'.{output_format}', ''), format=output_format, cleanup=True)
                
                # Read the generated file
                output_file = tmp_file.name
                with open(output_file, 'rb') as f:
                    graph_bytes = f.read()
                
                # Clean up
                os.unlink(output_file)
                
                # Return base64 encoded data
                return base64.b64encode(graph_bytes).decode('utf-8')
                
            except Exception as render_error:
                # Clean up temp file if it exists
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
                raise render_error
                
    except Exception as e:
        # Fallback to text representation
        return f"Error generating visual graph: {str(e)}\n\nWorkflow structure:\n{_format_workflow_as_text(workflow)}"


def _format_workflow_as_text(workflow):
    """Format workflow as text when visual generation fails."""
    lines = ["Nodes:"]
    for node in workflow["nodes"]:
        lines.append(f"  - {node['name']} ({node.get('category', 'Unknown')})")
    
    lines.append("\nTransitions:")
    for edge in workflow["edges"]:
        label = edge.get("label", "transition")
        lines.append(f"  - {edge['from']} --[{label}]--> {edge['to']}")
    
    return "\n".join(lines)


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
        
        Returns information about all configured Jira instances, including both
        instances configured via JIRA_INSTANCES JSON and legacy single instance configuration.
        
        Returns:
            A dictionary containing a list of Jira instances
        """
        try:
            instances = settings.get_jira_instances()
            default_instance = settings.get_default_instance_name()
            
            instance_list = []
            for name, instance in instances.items():
                instance_info = {
                    "name": name,
                    "url": instance.url,
                    "user": instance.user,
                    "has_token": bool(instance.token),
                    "description": instance.description,
                    "is_default": name == default_instance
                }
                instance_list.append(instance_info)
            
            return {
                "instances": instance_list,
                "count": len(instance_list),
                "default_instance": default_instance
            }
        except Exception as e:
            return {
                "instances": [],
                "count": 0,
                "error": str(e)
            }
