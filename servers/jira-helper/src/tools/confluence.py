"""Confluence operations: spaces, pages, search, create, update."""

import logging

from jira_client import get_confluence_client, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError
from output_sanitizer import sanitize_string

logger = logging.getLogger(__name__)


def list_confluence_spaces(instance_name: str = None, **kwargs) -> dict:
    """List all Confluence spaces available in the instance."""
    name = resolve_instance_name(instance_name)
    client = get_confluence_client(name)
    try:
        result = client.get_all_spaces(expand="description.plain")
        spaces_raw = result.get("results", []) if isinstance(result, dict) else result
        spaces = []
        for s in spaces_raw:
            spaces.append({
                "key": s.get("key", ""),
                "name": s.get("name", ""),
                "type": s.get("type", ""),
                "status": s.get("status", ""),
            })
        return {"instance": name, "spaces": spaces, "count": len(spaces)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to list Confluence spaces: {e}", instance_name=name)


def list_confluence_pages(
    space_key: str, instance_name: str = None, limit: int = 20, **kwargs
) -> dict:
    """List pages in a specific Confluence space."""
    if not space_key:
        raise JiraValidationError("space_key is required.")
    name = resolve_instance_name(instance_name)
    client = get_confluence_client(name)
    try:
        pages_raw = client.get_all_pages_from_space(space_key, limit=limit, expand="version")
        pages = []
        for p in pages_raw:
            pages.append({
                "id": p.get("id", ""),
                "title": sanitize_string(p.get("title", "")),
                "status": p.get("status", ""),
                "version": p.get("version", {}).get("number", 0) if p.get("version") else 0,
            })
        return {"instance": name, "space_key": space_key, "pages": pages, "count": len(pages)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to list pages in space {space_key}: {e}", instance_name=name)


def get_confluence_page(
    page_id: str = None, title: str = None, space_key: str = None,
    instance_name: str = None, **kwargs
) -> dict:
    """Get detailed information about a specific Confluence page."""
    if not page_id and not (title and space_key):
        raise JiraValidationError("Either page_id or both title and space_key are required.")
    name = resolve_instance_name(instance_name)
    client = get_confluence_client(name)
    try:
        if page_id:
            page = client.get_page_by_id(page_id, expand="body.storage,version,space")
        else:
            page = client.get_page_by_title(space_key, title, expand="body.storage,version,space")

        if not page:
            return {"instance": name, "found": False, "message": "Page not found."}

        return {
            "instance": name, "found": True,
            "id": page.get("id", ""),
            "title": sanitize_string(page.get("title", "")),
            "space_key": page.get("space", {}).get("key", "") if page.get("space") else space_key or "",
            "version": page.get("version", {}).get("number", 0) if page.get("version") else 0,
            "body": sanitize_string(page.get("body", {}).get("storage", {}).get("value", "") if page.get("body") else ""),
            "status": page.get("status", ""),
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to get Confluence page: {e}", instance_name=name)


def search_confluence_pages(
    query: str, instance_name: str = None, limit: int = 20, **kwargs
) -> dict:
    """Search for Confluence pages using text query."""
    if not query or not query.strip():
        raise JiraValidationError("query is required.")
    name = resolve_instance_name(instance_name)
    client = get_confluence_client(name)
    try:
        cql = f'text ~ "{query.strip()}"'
        result = client.cql(cql, limit=limit)
        results_raw = result.get("results", []) if isinstance(result, dict) else []
        pages = []
        for r in results_raw:
            content = r.get("content", r) if isinstance(r, dict) else r
            pages.append({
                "id": content.get("id", ""),
                "title": sanitize_string(content.get("title", "")),
                "type": content.get("type", ""),
                "space_key": content.get("space", {}).get("key", "") if content.get("space") else "",
            })
        return {"instance": name, "query": query, "pages": pages, "count": len(pages)}
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Confluence search failed: {e}", instance_name=name)


def create_confluence_page(
    space_key: str, title: str, body: str, parent_id: str = None,
    instance_name: str = None, **kwargs
) -> dict:
    """Create a new Confluence page."""
    if not space_key or not title or not body:
        raise JiraValidationError("space_key, title, and body are required.")
    name = resolve_instance_name(instance_name)
    client = get_confluence_client(name)
    try:
        result = client.create_page(
            space=space_key, title=title, body=body,
            parent_id=parent_id, type="page",
        )
        return {
            "instance": name,
            "id": result.get("id", ""),
            "title": result.get("title", title),
            "space_key": space_key,
            "message": f"Successfully created page '{title}' in space {space_key}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to create Confluence page: {e}", instance_name=name)


def update_confluence_page(
    page_id: str, title: str = None, body: str = None,
    instance_name: str = None, **kwargs
) -> dict:
    """Update an existing Confluence page."""
    if not page_id:
        raise JiraValidationError("page_id is required.")
    if not title and not body:
        raise JiraValidationError("At least one of title or body is required.")
    name = resolve_instance_name(instance_name)
    client = get_confluence_client(name)
    try:
        # Get current page to preserve unmodified fields
        current = client.get_page_by_id(page_id, expand="body.storage,version")
        current_title = current.get("title", "")
        current_body = current.get("body", {}).get("storage", {}).get("value", "") if current.get("body") else ""
        current_version = current.get("version", {}).get("number", 0) if current.get("version") else 0

        result = client.update_page(
            page_id=page_id,
            title=title or current_title,
            body=body or current_body,
        )
        return {
            "instance": name,
            "id": page_id,
            "title": title or current_title,
            "version": current_version + 1,
            "message": f"Successfully updated page {page_id}",
        }
    except JiraError:
        raise
    except Exception as e:
        raise JiraApiError(f"Failed to update Confluence page: {e}", instance_name=name)