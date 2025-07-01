"""
MCP adapter for document processing.

This adapter connects the application use cases to the MCP framework,
keeping the core business logic independent of MCP specifics.
"""

from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

from domain.models import DocumentFormat, PDFEngine
from application.use_cases import (
    ConvertDocumentUseCase, ListOutputFilesUseCase, 
    ListTemplatesUseCase, GetServerInfoUseCase
)


class MCPDocumentProcessorAdapter:
    """Adapter that connects use cases to MCP tools."""
    
    def __init__(
        self,
        convert_use_case: ConvertDocumentUseCase,
        list_files_use_case: ListOutputFilesUseCase,
        list_templates_use_case: ListTemplatesUseCase,
        get_info_use_case: GetServerInfoUseCase
    ):
        self._convert_use_case = convert_use_case
        self._list_files_use_case = list_files_use_case
        self._list_templates_use_case = list_templates_use_case
        self._get_info_use_case = get_info_use_case
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register MCP tools with the server."""
        
        @mcp_server.tool()
        def convert_markdown_to_pdf(
            markdown_text: str,
            filename: Optional[str] = None,
            engine: Optional[str] = None,
            template: Optional[str] = None
        ) -> Dict[str, Any]:
            """Convert markdown text to PDF format."""
            try:
                pdf_engine = PDFEngine(engine) if engine else None
                result = self._convert_use_case.execute(
                    markdown_text=markdown_text,
                    target_format=DocumentFormat.PDF,
                    filename=filename,
                    template_name=template,
                    pdf_engine=pdf_engine
                )
                
                if result.success:
                    return {
                        "success": True,
                        "output_file": str(result.file_path),
                        "filename": result.file_path.name,
                        "engine_used": result.engine_used,
                        "file_size_bytes": result.file_size_bytes
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @mcp_server.tool()
        def convert_markdown_to_html(
            markdown_text: str,
            filename: Optional[str] = None,
            template: Optional[str] = None
        ) -> Dict[str, Any]:
            """Convert markdown text to HTML format."""
            try:
                result = self._convert_use_case.execute(
                    markdown_text=markdown_text,
                    target_format=DocumentFormat.HTML,
                    filename=filename,
                    template_name=template
                )
                
                if result.success:
                    return {
                        "success": True,
                        "output_file": str(result.file_path),
                        "filename": result.file_path.name,
                        "file_size_bytes": result.file_size_bytes,
                        "template_used": template or "default"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @mcp_server.tool()
        def convert_markdown_to_docx(
            markdown_text: str,
            filename: Optional[str] = None
        ) -> Dict[str, Any]:
            """Convert markdown text to Microsoft Word document."""
            try:
                result = self._convert_use_case.execute(
                    markdown_text=markdown_text,
                    target_format=DocumentFormat.DOCX,
                    filename=filename
                )
                
                if result.success:
                    return {
                        "success": True,
                        "output_file": str(result.file_path),
                        "filename": result.file_path.name,
                        "file_size_bytes": result.file_size_bytes
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @mcp_server.tool()
        def convert_markdown_to_text(
            markdown_text: str,
            filename: Optional[str] = None
        ) -> Dict[str, Any]:
            """Convert markdown text to plain text."""
            try:
                result = self._convert_use_case.execute(
                    markdown_text=markdown_text,
                    target_format=DocumentFormat.TEXT,
                    filename=filename
                )
                
                if result.success:
                    return {
                        "success": True,
                        "output_file": str(result.file_path),
                        "filename": result.file_path.name,
                        "file_size_bytes": result.file_size_bytes,
                        "preview": result.document.content[:200] + "..." if len(result.document.content) > 200 else result.document.content
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @mcp_server.tool()
        def list_output_files() -> Dict[str, Any]:
            """List all files in the output directory."""
            try:
                files = self._list_files_use_case.execute()
                
                file_list = []
                for file_info in files:
                    file_list.append({
                        "filename": file_info.name,
                        "full_path": str(file_info.path),
                        "size_bytes": file_info.size_bytes,
                        "modified_time": file_info.modified_time,
                        "extension": file_info.extension
                    })
                
                return {
                    "success": True,
                    "file_count": len(file_list),
                    "files": sorted(file_list, key=lambda x: x["modified_time"], reverse=True)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @mcp_server.tool()
        def get_server_info() -> Dict[str, Any]:
            """Get server configuration and capabilities."""
            try:
                return self._get_info_use_case.execute()
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def register_resources(self, mcp_server: FastMCP) -> None:
        """Register MCP resources with the server."""
        
        @mcp_server.resource("config://server")
        def server_config() -> Dict[str, Any]:
            """Server configuration resource."""
            try:
                info = self._get_info_use_case.execute()
                return {
                    "name": "Document Processor Configuration",
                    "settings": info
                }
            except Exception as e:
                return {
                    "name": "Configuration Error",
                    "error": str(e)
                }
        
        @mcp_server.resource("templates://list")
        def list_templates() -> Dict[str, Any]:
            """List available HTML templates."""
            try:
                templates = self._list_templates_use_case.execute()
                return {
                    "name": "Available HTML Templates",
                    "templates": [{"name": name} for name in templates]
                }
            except Exception as e:
                return {
                    "name": "Template List Error",
                    "error": str(e),
                    "templates": []
                }
