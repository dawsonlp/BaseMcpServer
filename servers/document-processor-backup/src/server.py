"""
Document Processor MCP server implementation using hexagonal architecture.

This module wires together all the components following dependency injection
and inversion of control principles.
"""

from mcp.server.fastmcp import FastMCP

# Domain
from domain.models import PDFEngine

# Application
from application.use_cases import (
    ConvertDocumentUseCase, ListOutputFilesUseCase,
    ListTemplatesUseCase, GetServerInfoUseCase
)

# Infrastructure
from infrastructure.converters import MarkdownConverter
from infrastructure.storage import LocalFileStorage
from infrastructure.templates import Jinja2TemplateRenderer
from infrastructure.config import SettingsConfigurationProvider

# Adapters
from adapters.mcp_adapter import MCPDocumentProcessorAdapter

from config import settings


def create_document_processor_server() -> FastMCP:
    """
    Create and configure the document processor MCP server.
    
    This function follows the dependency injection pattern to wire together
    all components of the hexagonal architecture.
    """
    # Create infrastructure components (outer layer)
    config_provider = SettingsConfigurationProvider()
    file_storage = LocalFileStorage()
    template_renderer = Jinja2TemplateRenderer(config_provider.get_template_directory())
    document_converter = MarkdownConverter(template_renderer)
    
    # Create application use cases (application layer)
    convert_use_case = ConvertDocumentUseCase(
        converter=document_converter,
        file_storage=file_storage,
        template_renderer=template_renderer,
        config=config_provider
    )
    
    list_files_use_case = ListOutputFilesUseCase(
        file_storage=file_storage,
        config=config_provider
    )
    
    list_templates_use_case = ListTemplatesUseCase(
        template_renderer=template_renderer
    )
    
    get_info_use_case = GetServerInfoUseCase(
        config=config_provider
    )
    
    # Create MCP adapter (adapter layer)
    mcp_adapter = MCPDocumentProcessorAdapter(
        convert_use_case=convert_use_case,
        list_files_use_case=list_files_use_case,
        list_templates_use_case=list_templates_use_case,
        get_info_use_case=get_info_use_case
    )
    
    # Create and configure MCP server
    mcp_server = FastMCP(settings.server_name)
    
    # Register tools and resources through the adapter
    mcp_adapter.register_tools(mcp_server)
    mcp_adapter.register_resources(mcp_server)
    
    return mcp_server


def register_tools_and_resources(srv: FastMCP):
    """
    Legacy function for backward compatibility.
    
    This function is kept for compatibility with the existing main.py,
    but now delegates to the new hexagonal architecture.
    """
    # Get the configured server components
    server = create_document_processor_server()
    
    # Copy tools and resources from the configured server
    # Note: This is a workaround for the existing main.py structure
    # In a pure hexagonal architecture, we would create the server directly
    for tool_name, tool_func in server._tools.items():
        srv._tools[tool_name] = tool_func
    
    for resource_uri, resource_func in server._resources.items():
        srv._resources[resource_uri] = resource_func
