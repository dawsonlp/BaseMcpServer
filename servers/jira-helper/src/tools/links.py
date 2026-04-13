"""Issue link operations: create, query, and bulk-link on creation."""

import logging

from jira_client import get_jira_client, validate_issue_key, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError

logger = logging.getLogger(__name__)


def create_issue_link(
    from_issue_key: str, to_issue_key: str, link_type: str = "Relates",
    instance_name: str = None, **kwargs
) -> dict:
    """Create a link between two Jira issues."""
    from_key = validate_issue_key(from_issue_key)
    to_key = validate_issue_key(to_issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        link_data = {
            "type": {"name": link_type},
            "inwardIssue": {"key": from_key},
            "outwardIssue": {"key": to_key},
        }
        client.create_issue_link(link_data)
        return {
            "from_issue": from_key, "to_issue": to_key, "link_type": link_type,
            "instance": name, "message": f"Successfully linked {from_key} -> {to_key} ({link_type})",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to create link: {e}", instance_name=name)


def create_epic_story_link(epic_key: str, story_key: str, instance_name: str = None, **kwargs) -> dict:
    """Create an Epic-Story link between issues."""
    e_key = validate_issue_key(epic_key)
    s_key = validate_issue_key(story_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        link_data = {
            "type": {"name": "Epic-Story Link"},
            "inwardIssue": {"key": e_key},
            "outwardIssue": {"key": s_key},
        }
        try:
            client.create_issue_link(link_data)
        except Exception:
            # Fall back to generic "Relates" if Epic-Story Link type not available
            link_data["type"]["name"] = "Relates"
            client.create_issue_link(link_data)
        return {
            "epic_key": e_key, "story_key": s_key,
            "instance": name, "message": f"Successfully linked epic {e_key} to story {s_key}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to create epic-story link: {e}", instance_name=name)


def get_issue_links(issue_key: str, instance_name: str = None, **kwargs) -> dict:
    """Get all links for a specific Jira issue."""
    key = validate_issue_key(issue_key)
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)
    try:
        issue = client.issue(key)
        issue_links = issue.get("fields", {}).get("issuelinks", [])
        links = []
        for link in issue_links:
            link_info = {"type": link.get("type", {}).get("name", "")}
            if "outwardIssue" in link:
                linked = link["outwardIssue"]
                link_info["direction"] = "outward"
                link_info["issue_key"] = linked.get("key", "")
                link_info["summary"] = linked.get("fields", {}).get("summary", "")
                link_info["status"] = linked.get("fields", {}).get("status", {}).get("name", "") if linked.get("fields", {}).get("status") else ""
            elif "inwardIssue" in link:
                linked = link["inwardIssue"]
                link_info["direction"] = "inward"
                link_info["issue_key"] = linked.get("key", "")
                link_info["summary"] = linked.get("fields", {}).get("summary", "")
                link_info["status"] = linked.get("fields", {}).get("status", {}).get("name", "") if linked.get("fields", {}).get("status") else ""
            links.append(link_info)
        return {"key": key, "instance": name, "links": links, "count": len(links)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get links for {key}: {e}", instance_name=name)


def create_issue_with_links(
    project_key: str, summary: str, issue_type: str = "Task",
    description: str = "", links: list = None,
    instance_name: str = None, **kwargs
) -> dict:
    """Create a new Jira issue with links to other issues."""
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

        result = client.issue_create(fields=fields)
        new_key = result.get("key", "")

        links_created = 0
        link_errors = []
        if links:
            for link_spec in links:
                target_key = link_spec.get("issue_key", "")
                link_type = link_spec.get("link_type", "Relates")
                if target_key:
                    try:
                        link_data = {
                            "type": {"name": link_type},
                            "inwardIssue": {"key": new_key},
                            "outwardIssue": {"key": target_key.strip().upper()},
                        }
                        client.create_issue_link(link_data)
                        links_created += 1
                    except Exception as le:
                        link_errors.append(f"Failed to link to {target_key}: {le}")

        response = {
            "key": new_key, "instance": name,
            "links_created": links_created,
            "message": f"Created {new_key} with {links_created} links",
        }
        if link_errors:
            response["link_errors"] = link_errors
        return response
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to create issue with links: {e}", instance_name=name)