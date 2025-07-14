"""File storage implementations."""

import aiofiles
from pathlib import Path
from typing import List, Optional

from domain.models import FileInfo
from domain.ports import FileStorage


class LocalFileStorage(FileStorage):
    """Local filesystem storage implementation."""
    
    async def save_file(self, content: str, file_path: Path) -> bool:
        """Save content to a file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle binary content (encoded as latin-1)
            if isinstance(content, str) and len(content) > 0:
                # Check if this looks like binary content
                try:
                    content.encode('utf-8')
                    mode = 'w'
                    encoding = 'utf-8'
                except UnicodeEncodeError:
                    # This is binary content stored as latin-1
                    mode = 'wb'
                    content = content.encode('latin-1')
                    encoding = None
            else:
                mode = 'w'
                encoding = 'utf-8'
            
            if encoding:
                async with aiofiles.open(file_path, mode, encoding=encoding) as f:
                    await f.write(content)
            else:
                async with aiofiles.open(file_path, mode) as f:
                    await f.write(content)
            
            return True
        except Exception:
            return False
    
    async def list_files(self, directory: Path) -> List[FileInfo]:
        """List files in a directory."""
        files = []
        if directory.exists() and directory.is_dir():
            for file_path in directory.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append(FileInfo(
                        name=file_path.name,
                        path=file_path,
                        size_bytes=stat.st_size,
                        modified_time=stat.st_mtime,
                        extension=file_path.suffix
                    ))
        return files
    
    async def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists."""
        return file_path.exists() and file_path.is_file()
    
    async def get_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Get information about a file."""
        if await self.file_exists(file_path):
            stat = file_path.stat()
            return FileInfo(
                name=file_path.name,
                path=file_path,
                size_bytes=stat.st_size,
                modified_time=stat.st_mtime,
                extension=file_path.suffix
            )
        return None
