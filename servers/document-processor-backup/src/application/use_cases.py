"""
Use cases for document processing.

Pure business logic that orchestrates domain objects and ports.
"""

import uuid
from typing import Dict, Any, List
from pathlib import Path

from domain.models import ConversionRequest, ConversionResult, DocumentFormat, PDFEngine, FileInfo
from domain.ports import DocumentConverter, FileStorage, TemplateRenderer, ConfigurationProvider


class ConvertDocumentUseCase:
    """Use case for converting documents between formats."""
    
    def __init__(
        self,
        converter: DocumentConverter,
        file_storage: FileStorage,
        template_renderer: TemplateRenderer,
        config: ConfigurationProvider
    ):
        self._converter = converter
        self._file_storage = file_storage
        self._template_renderer = template_renderer
        self._config = config
    
    async def execute(
        self,
        markdown_text: str,
        target_format: DocumentFormat,
        filename: str = None,
        template_name: str = None,
        pdf_engine: PDFEngine = None
    ) -> ConversionResult:
        """Execute document conversion."""
        
        # Generate filename if not provided
        if not filename:
            filename = f"document_{uuid.uuid4().hex[:8]}"
        
        # Use default PDF engine if not specified
        if target_format == DocumentFormat.PDF and not pdf_engine:
            pdf_engine = self._config.get_default_pdf_engine()
        
        # Create conversion request
        request = ConversionRequest(
            source_content=markdown_text,
            target_format=target_format,
            filename=filename,
            template_name=template_name,
            pdf_engine=pdf_engine
        )
        
        # Perform conversion
        result = await self._converter.convert(request)
        
        # Save to file if conversion was successful
        if result.success and result.document:
            output_dir = self._config.get_output_directory()
            file_path = output_dir / f"{filename}.{target_format.value}"
            
            saved = await self._file_storage.save_file(result.document.content, file_path)
            if saved:
                file_info = await self._file_storage.get_file_info(file_path)
                return ConversionResult(
                    success=True,
                    document=result.document,
                    file_path=file_path,
                    file_size_bytes=file_info.size_bytes if file_info else 0,
                    engine_used=result.engine_used
                )
            else:
                return ConversionResult(
                    success=False,
                    error_message="Failed to save converted document"
                )
        
        return result


class ListOutputFilesUseCase:
    """Use case for listing output files."""
    
    def __init__(self, file_storage: FileStorage, config: ConfigurationProvider):
        self._file_storage = file_storage
        self._config = config
    
    async def execute(self) -> List[FileInfo]:
        """Execute file listing."""
        output_dir = self._config.get_output_directory()
        return await self._file_storage.list_files(output_dir)


class ListTemplatesUseCase:
    """Use case for listing available templates."""
    
    def __init__(self, template_renderer: TemplateRenderer):
        self._template_renderer = template_renderer
    
    async def execute(self) -> List[str]:
        """Execute template listing."""
        return await self._template_renderer.list_templates()


class GetServerInfoUseCase:
    """Use case for getting server configuration information."""
    
    def __init__(self, config: ConfigurationProvider):
        self._config = config
    
    async def execute(self) -> Dict[str, Any]:
        """Execute server info retrieval."""
        return {
            "output_directory": str(self._config.get_output_directory()),
            "input_directory": str(self._config.get_input_directory()),
            "template_directory": str(self._config.get_template_directory()),
            "default_pdf_engine": self._config.get_default_pdf_engine().value,
            "max_file_size_mb": self._config.get_max_file_size_mb(),
            "supported_formats": [fmt.value for fmt in DocumentFormat],
            "available_pdf_engines": [engine.value for engine in PDFEngine]
        }
