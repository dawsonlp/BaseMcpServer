"""
Confluence API Repository implementation.

This module contains the repository implementation for Confluence operations
using the atlassian-python-api library.
"""

import asyncio
import logging
from typing import Any

from atlassian import Confluence

from domain.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraInstanceNotFound,
    JiraTimeoutError,
)
from domain.models import (
    ConfluencePage,
    ConfluencePageCreateRequest,
    ConfluencePageUpdateRequest,
    ConfluenceSearchResult,
    ConfluenceSpace,
)
from domain.ports import ConfigurationProvider
from infrastructure.base_adapter import BaseJiraAdapter

logger = logging.getLogger(__name__)


class ConfluenceClientFactory:
    """Factory for creating Confluence clients using atlassian-python-api."""

    def __init__(self, config_provider: ConfigurationProvider):
        self._config_provider = config_provider
        self._clients: dict[str, Confluence] = {}

    def create_client(self, instance_name: str | None = None) -> Confluence:
        """Create a Confluence client for the specified instance."""
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
            # Use the same credentials as Jira since they often share authentication
            is_cloud = ".atlassian.net" in instance.url
            
            # Confluence URL might need to be adjusted if only Jira URL is provided
            confluence_url = instance.url
            if "/jira" in confluence_url.lower():
                confluence_url = confluence_url.replace("/jira", "/wiki")
            elif not ("/wiki" in confluence_url.lower() or "confluence" in confluence_url.lower()):
                # If it's a generic Atlassian URL, add /wiki path
                if confluence_url.endswith("/"):
                    confluence_url += "wiki"
                else:
                    confluence_url += "/wiki"
            
            client = Confluence(
                url=confluence_url,
                username=instance.user,
                password=instance.token,
                cloud=is_cloud,
                timeout=30,
            )
            self._clients[instance_name] = client
            logger.info(f"Created Confluence client for instance: {instance_name}")
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
            # Try to get current user info to validate connection
            client.get_current_user()
            return True
        except Exception:
            return False


class ConfluenceRepository:
    """Repository implementation for Confluence operations using atlassian-python-api."""

    def __init__(self, client_factory: ConfluenceClientFactory, config_provider: ConfigurationProvider):
        self._client_factory = client_factory
        self._config_provider = config_provider

    async def get_spaces(self, instance_name: str) -> list[ConfluenceSpace]:
        """Get all spaces from a Confluence instance."""
        try:
            client = self._client_factory.create_client(instance_name)
            spaces_data = await asyncio.to_thread(
                client.get_all_spaces,
                start=0,
                limit=500,  # Get a reasonable number of spaces
                expand="description,homepage"
            )

            result = []
            for space_data in spaces_data.get("results", []):
                space = ConfluenceSpace(
                    key=space_data["key"],
                    name=space_data["name"],
                    description=space_data.get("description", {}).get("plain", {}).get("value"),
                    homepage_id=space_data.get("homepage", {}).get("id"),
                    type=space_data.get("type", "global")
                )
                result.append(space)

            logger.info(f"Retrieved {len(result)} spaces from Confluence instance {instance_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to get spaces from Confluence instance {instance_name}: {str(e)}")
            raise

    async def get_space_pages(self, space_key: str, instance_name: str, limit: int = 50) -> list[ConfluencePage]:
        """Get pages in a specific Confluence space."""
        try:
            client = self._client_factory.create_client(instance_name)
            
            # Get pages from the space
            pages_data = await asyncio.to_thread(
                client.get_all_pages_from_space,
                space_key,
                start=0,
                limit=limit,
                expand="version,space,history.lastUpdated"
            )

            result = []
            instance = self._config_provider.get_instance(instance_name)
            base_url = instance.url if instance else ""

            for page_data in pages_data:
                # Build page URL
                page_url = None
                if base_url and page_data.get("id"):
                    if "/wiki" in base_url:
                        page_url = f"{base_url}/pages/viewpage.action?pageId={page_data['id']}"
                    else:
                        page_url = f"{base_url}/wiki/pages/viewpage.action?pageId={page_data['id']}"

                # Extract version information
                version = page_data.get("version", {}).get("number", 1)
                
                # Extract history information
                history = page_data.get("history", {})
                created_date = history.get("createdDate")
                last_updated = history.get("lastUpdated", {})
                modified_date = last_updated.get("when") if last_updated else None
                author = last_updated.get("by", {}).get("displayName") if last_updated else None

                page = ConfluencePage(
                    id=page_data["id"],
                    title=page_data["title"],
                    space_key=space_key,
                    version=version,
                    created_date=created_date,
                    modified_date=modified_date,
                    author=author,
                    url=page_url
                )
                result.append(page)

            logger.info(f"Retrieved {len(result)} pages from space {space_key}")
            return result

        except Exception as e:
            logger.error(f"Failed to get pages from space {space_key}: {str(e)}")
            raise

    async def get_page_by_id(self, page_id: str, instance_name: str, expand: str = "body.storage,version,space,history.lastUpdated") -> ConfluencePage:
        """Get a specific Confluence page by ID."""
        try:
            client = self._client_factory.create_client(instance_name)
            page_data = await asyncio.to_thread(client.get_page_by_id, page_id, expand=expand)

            # Extract content
            content = None
            body = page_data.get("body", {})
            if "storage" in body:
                content = body["storage"].get("value")

            # Extract space information
            space_data = page_data.get("space", {})
            space_key = space_data.get("key", "")

            # Extract version information
            version_data = page_data.get("version", {})
            version = version_data.get("number", 1)

            # Extract history information
            history = page_data.get("history", {})
            created_date = history.get("createdDate")
            last_updated = history.get("lastUpdated", {})
            modified_date = last_updated.get("when") if last_updated else None
            author = last_updated.get("by", {}).get("displayName") if last_updated else None

            # Build page URL
            instance = self._config_provider.get_instance(instance_name)
            page_url = None
            if instance:
                base_url = instance.url
                if "/wiki" in base_url:
                    page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
                else:
                    page_url = f"{base_url}/wiki/pages/viewpage.action?pageId={page_id}"

            page = ConfluencePage(
                id=page_id,
                title=page_data["title"],
                space_key=space_key,
                content=content,
                version=version,
                created_date=created_date,
                modified_date=modified_date,
                author=author,
                url=page_url
            )

            logger.debug(f"Retrieved page {page_id}: {page.title}")
            return page

        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                logger.error(f"Page {page_id} not found")
                raise
            logger.error(f"Failed to get page {page_id}: {str(e)}")
            raise

    async def search_pages(self, query: str, space_key: str | None, instance_name: str) -> ConfluenceSearchResult:
        """Search for Confluence pages using text query."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Build search query
            search_query = query
            if space_key:
                search_query = f"space={space_key} AND text ~ \"{query}\""

            # Execute search
            search_data = await asyncio.to_thread(
                client.cql,
                search_query,
                limit=50,
                expand="content.space,content.version,content.history.lastUpdated"
            )

            pages = []
            instance = self._config_provider.get_instance(instance_name)
            base_url = instance.url if instance else ""

            for result in search_data.get("results", []):
                content = result.get("content", {})
                if content.get("type") == "page":
                    # Extract space information
                    space_data = content.get("space", {})
                    page_space_key = space_data.get("key", "")

                    # Extract version information
                    version_data = content.get("version", {})
                    version = version_data.get("number", 1)

                    # Extract history information
                    history = content.get("history", {})
                    created_date = history.get("createdDate")
                    last_updated = history.get("lastUpdated", {})
                    modified_date = last_updated.get("when") if last_updated else None
                    author = last_updated.get("by", {}).get("displayName") if last_updated else None

                    # Build page URL
                    page_url = None
                    page_id = content.get("id")
                    if base_url and page_id:
                        if "/wiki" in base_url:
                            page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
                        else:
                            page_url = f"{base_url}/wiki/pages/viewpage.action?pageId={page_id}"

                    page = ConfluencePage(
                        id=page_id,
                        title=content["title"],
                        space_key=page_space_key,
                        version=version,
                        created_date=created_date,
                        modified_date=modified_date,
                        author=author,
                        url=page_url
                    )
                    pages.append(page)

            search_result = ConfluenceSearchResult(
                pages=pages,
                total_results=search_data.get("totalSize", len(pages)),
                limit=search_data.get("limit", 50),
                start=search_data.get("start", 0)
            )

            logger.info(f"Search for '{query}' returned {len(pages)} pages")
            return search_result

        except Exception as e:
            logger.error(f"Failed to search pages with query '{query}': {str(e)}")
            raise

    async def create_page(self, space_key: str, title: str, content: str, instance_name: str, parent_page_id: str | None = None) -> ConfluencePage:
        """Create a new Confluence page."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Prepare page data
            page_data = {
                "type": "page",
                "title": title,
                "space": {"key": space_key},
                "body": {
                    "storage": {
                        "value": content,
                        "representation": "storage"
                    }
                }
            }

            # Add parent page if specified
            if parent_page_id:
                page_data["ancestors"] = [{"id": parent_page_id}]

            # Create the page
            created_page_data = await asyncio.to_thread(client.create_page_from_dict, page_data)

            # Convert to domain model
            instance = self._config_provider.get_instance(instance_name)
            page_url = None
            if instance:
                base_url = instance.url
                page_id = created_page_data["id"]
                if "/wiki" in base_url:
                    page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
                else:
                    page_url = f"{base_url}/wiki/pages/viewpage.action?pageId={page_id}"

            page = ConfluencePage(
                id=created_page_data["id"],
                title=created_page_data["title"],
                space_key=space_key,
                content=content,
                version=created_page_data.get("version", {}).get("number", 1),
                url=page_url
            )

            logger.info(f"Created page '{title}' in space {space_key}")
            return page

        except Exception as e:
            logger.error(f"Failed to create page '{title}' in space {space_key}: {str(e)}")
            raise

    async def update_page(self, page_id: str, title: str, content: str, version: int, instance_name: str) -> ConfluencePage:
        """Update an existing Confluence page."""
        try:
            client = self._client_factory.create_client(instance_name)

            # Get current page to get space info
            current_page_data = await asyncio.to_thread(client.get_page_by_id, page_id, expand="space,version")

            # Prepare update data
            page_data = {
                "id": page_id,
                "type": "page",
                "title": title,
                "space": {"key": current_page_data["space"]["key"]},
                "body": {
                    "storage": {
                        "value": content,
                        "representation": "storage"
                    }
                },
                "version": {
                    "number": version + 1  # Increment version for update
                }
            }

            # Update the page
            updated_page_data = await asyncio.to_thread(client.update_page, page_data)

            # Convert to domain model
            instance = self._config_provider.get_instance(instance_name)
            page_url = None
            if instance:
                base_url = instance.url
                if "/wiki" in base_url:
                    page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
                else:
                    page_url = f"{base_url}/wiki/pages/viewpage.action?pageId={page_id}"

            page = ConfluencePage(
                id=page_id,
                title=updated_page_data["title"],
                space_key=current_page_data["space"]["key"],
                content=content,
                version=updated_page_data.get("version", {}).get("number", version + 1),
                url=page_url
            )

            logger.info(f"Updated page '{title}' (ID: {page_id}) to version {page.version}")
            return page

        except Exception as e:
            logger.error(f"Failed to update page {page_id}: {str(e)}")
            raise
