"""Issue operations: get, create, update, transition, assign."""

import logging
from typing import Any, Literal, TypedDict

from jira_client import get_jira_client, validate_issue_key, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError
from output_sanitizer import sanitize_string

logger = logging.getLogger(__name__)


class ListResult(TypedDict):
    instance: str
    count: int


class ProjectsResult(ListResult):
    projects: list[dict[str, Any]]


class IssueDetailsResult(TypedDict):
    key: str
    summary: str
    status: str
    assignee: str
    reporter: str
    priority: str
    issue_type: str
    project: str
    description: str
    created: str
    updated: str
    labels: list[str]
    components: list[str]
    instance: str


class CreatedIssueResult(TypedDict):
    key: str
    id: str
    self: str
    instance: str
    message: str


class UpdatedIssueResult(TypedDict):
    key: str
    instance: str
    updated_fields: list[str]
    message: str


class TransitionResult(TypedDict):
    key: str
    instance: str
    transition: str
    transition_id: str
    message: str


class AssigneeResult(TypedDict):
    key: str
    instance: str
    assignee: str
    message: str


class InstancesResult(TypedDict):
    instances: list[dict[str, Any]]
    count: int


class CustomFieldsResult(ListResult):
    custom_fields: list[dict[str, Any]]


def list_jira_projects(instance_name: str | None = None) -> ProjectsResult:
    """List all projects available in the Jira instance."""
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        projects = client.projects()
        result = []
        for p in projects:
            result.append({
                "key": p.get("key", ""),
                "name": p.get("name", ""),
                "id": p.get("id", ""),
                "project_type": p.get("projectTypeKey", ""),
            })
        return {"instance": name, "projects": result, "count": len(result)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to list projects: {e}", instance_name=name)


def get_issue_details(issue_key: str, instance_name: str | None = None) -> IssueDetailsResult:
    """Get detailed information about a specific Jira issue."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        issue = client.issue(key)
        fields = issue.get("fields", {})
        return {
            "key": issue.get("key", key),
            "summary": sanitize_string(fields.get("summary", "")),
            "status": fields.get("status", {}).get("name", "") if fields.get("status") else "",
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
            "reporter": fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else "",
            "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
            "issue_type": fields.get("issuetype", {}).get("name", "") if fields.get("issuetype") else "",
            "project": fields.get("project", {}).get("key", "") if fields.get("project") else "",
            "description": sanitize_string(fields.get("description", "")),
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "labels": fields.get("labels", []),
            "components": [c.get("name", "") for c in fields.get("components", [])],
            "instance": name,
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get issue {key}: {e}", instance_name=name)


def get_full_issue_details(
    issue_key: str, instance_name: str | None = None, include_comments: bool = True,
    raw_data: bool = False, format: Literal["structured"] = "structured",
) -> dict[str, Any]:
    """Get comprehensive information about a Jira issue with formatting options."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        issue = client.issue(key)
        if raw_data:
            return {"key": key, "raw_data": issue, "instance": name}

        fields = issue.get("fields", {})
        result = {
            "key": issue.get("key", key),
            "summary": sanitize_string(fields.get("summary", "")),
            "status": fields.get("status", {}).get("name", "") if fields.get("status") else "",
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
            "reporter": fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else "",
            "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
            "issue_type": fields.get("issuetype", {}).get("name", "") if fields.get("issuetype") else "",
            "project": fields.get("project", {}).get("key", "") if fields.get("project") else "",
            "description": sanitize_string(fields.get("description", "")),
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "labels": fields.get("labels", []),
            "components": [c.get("name", "") for c in fields.get("components", [])],
            "instance": name,
        }

        if include_comments:
            comments_data = client.issue_get_comments(key)
            comments = []
            raw_comments = comments_data.get("comments", []) if isinstance(comments_data, dict) else comments_data
            for c in raw_comments:
                comments.append({
                    "id": c.get("id", ""),
                    "author": c.get("author", {}).get("displayName", "") if c.get("author") else "",
                    "body": sanitize_string(c.get("body", "")),
                    "created": c.get("created", ""),
                    "updated": c.get("updated", ""),
                })
            result["comments"] = comments
            result["comment_count"] = len(comments)

        # Add links
        issue_links = fields.get("issuelinks", [])
        links = []
        for link in issue_links:
            link_info = {"type": link.get("type", {}).get("name", "")}
            if "outwardIssue" in link:
                link_info["direction"] = "outward"
                link_info["issue_key"] = link["outwardIssue"].get("key", "")
                link_info["summary"] = sanitize_string(link["outwardIssue"].get("fields", {}).get("summary", ""))
            elif "inwardIssue" in link:
                link_info["direction"] = "inward"
                link_info["issue_key"] = link["inwardIssue"].get("key", "")
                link_info["summary"] = sanitize_string(link["inwardIssue"].get("fields", {}).get("summary", ""))
            links.append(link_info)
        result["links"] = links

        # Add attachments
        attachments = fields.get("attachment", [])
        result["attachments"] = [
            {
                "id": a.get("id", ""),
                "filename": a.get("filename", ""),
                "size": a.get("size", 0),
                "created": a.get("created", ""),
                "author": a.get("author", {}).get("displayName", "") if a.get("author") else "",
            }
            for a in attachments
        ]

        return result
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get full issue details for {key}: {e}", instance_name=name)


def create_jira_ticket(
    project_key: str, summary: str, issue_type: str = "Task",
    description: str = "", priority: str | None = None, assignee: str | None = None,
    labels: list[str] | None = None, components: list[str] | None = None,
    instance_name: str | None = None, custom_fields: dict[str, Any] | None = None,
) -> CreatedIssueResult:
    """Create a new Jira ticket."""
    if not project_key or not summary:
        raise JiraValidationError("project_key and summary are required.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        fields = {
            "project": {"key": project_key.strip().upper()},
            "summary": summary.strip(),
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = description
        if priority:
            fields["priority"] = {"name": priority}
        if assignee:
            fields["assignee"] = {"name": assignee}
        if labels:
            fields["labels"] = labels
        if components:
            fields["components"] = [{"name": c} for c in components]

        for field_name, value in (custom_fields or {}).items():
            if not field_name.startswith("customfield_"):
                raise JiraValidationError(
                    f"Invalid custom field {field_name!r}; keys must start with 'customfield_'."
                )
            fields[field_name] = value

        result = client.issue_create(fields=fields)
        return {
            "key": result.get("key", ""),
            "id": result.get("id", ""),
            "self": result.get("self", ""),
            "instance": name,
            "message": f"Successfully created issue {result.get('key', '')}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to create issue: {e}", instance_name=name)


def update_jira_issue(
    issue_key: str, summary: str | None = None, description: str | None = None,
    priority: str | None = None, assignee: str | None = None,
    labels: list[str] | None = None, components: list[str] | None = None,
    instance_name: str | None = None, custom_fields: dict[str, Any] | None = None,
) -> UpdatedIssueResult:
    """Update an existing Jira issue with new field values."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        fields = {}
        if summary is not None:
            fields["summary"] = summary
        if description is not None:
            fields["description"] = description
        if priority is not None:
            fields["priority"] = {"name": priority}
        if assignee is not None:
            fields["assignee"] = {"name": assignee}
        if labels is not None:
            fields["labels"] = labels
        if components is not None:
            fields["components"] = [{"name": c} for c in components]

        for field_name, value in (custom_fields or {}).items():
            if not field_name.startswith("customfield_"):
                raise JiraValidationError(
                    f"Invalid custom field {field_name!r}; keys must start with 'customfield_'."
                )
            fields[field_name] = value

        if not fields:
            raise JiraValidationError("No fields to update. Provide at least one field.")

        client.issue_update(key, fields=fields)
        return {
            "key": key,
            "instance": name,
            "updated_fields": list(fields.keys()),
            "message": f"Successfully updated issue {key}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to update issue {key}: {e}", instance_name=name)


def transition_jira_issue(
    issue_key: str, transition_name: str | None = None, transition_id: str | None = None,
    instance_name: str | None = None,
) -> TransitionResult:
    """Transition a Jira issue through its workflow."""
    key = validate_issue_key(issue_key)
    if not transition_name and not transition_id:
        raise JiraValidationError("Either transition_name or transition_id is required.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        transitions = client.get_issue_transitions(key)
        target = None

        if transition_id:
            for t in transitions:
                if str(t.get("id")) == str(transition_id):
                    target = t
                    break
        elif transition_name:
            transition_lower = transition_name.lower()
            for t in transitions:
                if t.get("name", "").lower() == transition_lower:
                    target = t
                    break

        if not target:
            available = [t.get("name", "") for t in transitions]
            raise JiraValidationError(
                f"Transition not found. Available transitions: {available}"
            )

        client.set_issue_status_by_transition_id(key, target["id"])
        return {
            "key": key,
            "instance": name,
            "transition": target.get("name", ""),
            "transition_id": target.get("id", ""),
            "message": f"Successfully transitioned {key} via '{target.get('name', '')}'",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to transition issue {key}: {e}", instance_name=name)


def change_issue_assignee(
    issue_key: str, assignee: str, instance_name: str | None = None,
) -> AssigneeResult:
    """Change the assignee of a Jira issue."""
    key = validate_issue_key(issue_key)
    if not assignee:
        raise JiraValidationError("assignee is required.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        client.issue_update(key, fields={"assignee": {"name": assignee}})
        return {
            "key": key,
            "instance": name,
            "assignee": assignee,
            "message": f"Successfully changed assignee of {key} to {assignee}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to change assignee for {key}: {e}", instance_name=name)


def list_jira_instances() -> InstancesResult:
    """List all configured Jira instances."""
    from jira_client import get_instances_info
    instances = get_instances_info()
    return {"instances": instances, "count": len(instances)}


def get_custom_field_mappings(instance_name: str | None = None) -> CustomFieldsResult:
    """Get mappings between Jira custom field IDs and their names."""
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        all_fields = client.get_all_fields()
        mappings = []
        for field in all_fields:
            if field.get("custom", False):
                mappings.append({
                    "id": field.get("id", ""),
                    "name": field.get("name", ""),
                    "type": field.get("schema", {}).get("type", "") if field.get("schema") else "",
                    "custom_type": field.get("schema", {}).get("custom", "") if field.get("schema") else "",
                })
        return {"instance": name, "custom_fields": mappings, "count": len(mappings)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get custom field mappings: {e}", instance_name=name)
