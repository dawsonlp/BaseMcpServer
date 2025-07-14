"""
Domain-specific exceptions for document processing.
"""


class DocumentProcessingError(Exception):
    """Base exception for all document processing errors."""
    
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConversionError(DocumentProcessingError):
    """Exception raised when document conversion fails."""
    
    def __init__(self, source_format: str, target_format: str, message: str, details: str = None):
        self.source_format = source_format
        self.target_format = target_format
        super().__init__(
            f"Failed to convert from {source_format} to {target_format}: {message}",
            details
        )


class UnsupportedFormatError(DocumentProcessingError):
    """Exception raised when an unsupported format is encountered."""
    
    def __init__(self, format_name: str, supported_formats: list = None):
        self.format_name = format_name
        self.supported_formats = supported_formats or []
        
        message = f"Unsupported format: {format_name}"
        if self.supported_formats:
            message += f". Supported formats: {', '.join(self.supported_formats)}"
        
        super().__init__(message)


class TemplateError(DocumentProcessingError):
    """Exception raised when template processing fails."""
    
    def __init__(self, template_name: str, message: str, details: str = None):
        self.template_name = template_name
        super().__init__(
            f"Template error in '{template_name}': {message}",
            details
        )


class FileOperationError(DocumentProcessingError):
    """Exception raised when file operations fail."""
    
    def __init__(self, operation: str, file_path: str, message: str, details: str = None):
        self.operation = operation
        self.file_path = file_path
        super().__init__(
            f"File {operation} failed for '{file_path}': {message}",
            details
        )
