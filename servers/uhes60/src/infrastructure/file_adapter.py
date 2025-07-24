from pathlib import Path
from typing import List
from domain.results import Result, Error, ErrorType

class FileAdapter:
    """Adapter for file system operations."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    def read_text_file(self, filename: str) -> Result[str]:
        """Read a text file and return its contents."""
        try:
            file_path = self.base_path / filename
            if not file_path.exists():
                return Result.fail(Error(
                    type=ErrorType.NOT_FOUND_ERROR,
                    message=f"File not found: {filename}"
                ))
            
            content = file_path.read_text(encoding='utf-8')
            return Result.ok(content)
            
        except Exception as e:
            return Result.fail(Error(
                type=ErrorType.UNKNOWN_ERROR,
                message=f"Failed to read file {filename}: {str(e)}"
            ))
    
    def list_files(self, pattern: str = "*") -> Result[List[str]]:
        """List files matching a pattern."""
        try:
            if not self.base_path.exists():
                return Result.ok([])
            
            files = [f.name for f in self.base_path.glob(pattern) if f.is_file()]
            return Result.ok(files)
            
        except Exception as e:
            return Result.fail(Error(
                type=ErrorType.UNKNOWN_ERROR,
                message=f"Failed to list files: {str(e)}"
            ))
