"""
File Storage Manager
===================

Handles file storage operations with support for Render's filesystem constraints.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union, BinaryIO
import logging

logger = logging.getLogger(__name__)

class FileStorageManager:
    """Manages file storage with Render compatibility"""
    
    def __init__(self):
        """Initialize file storage manager"""
        self.is_render = os.environ.get('RENDER') == 'true'
        self.temp_dir = None
        self._setup_storage()
    
    def _setup_storage(self):
        """Setup storage directories based on environment"""
        if self.is_render:
            # Use /tmp on Render (ephemeral but writable)
            self.base_path = Path("/tmp/app_storage")
            self.upload_path = self.base_path / "uploads"
            self.export_path = self.base_path / "exports"
            self.cache_path = self.base_path / "cache"
            
            logger.info("Using /tmp for file storage on Render (ephemeral)")
        else:
            # Use local directories for development
            self.base_path = Path("./data/storage")
            self.upload_path = self.base_path / "uploads"
            self.export_path = self.base_path / "exports"
            self.cache_path = self.base_path / "cache"
        
        # Create directories
        for path in [self.upload_path, self.export_path, self.cache_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_upload_path(self, filename: str) -> Path:
        """Get path for uploaded file"""
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        return self.upload_path / safe_filename
    
    def get_export_path(self, filename: str) -> Path:
        """Get path for exported file"""
        safe_filename = self._sanitize_filename(filename)
        return self.export_path / safe_filename
    
    def get_temp_file(self, suffix: str = None, prefix: str = "tmp_") -> Path:
        """Get a temporary file path"""
        if self.is_render:
            # Use /tmp on Render
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix=prefix,
                dir="/tmp"
            )
        else:
            # Use system temp directory
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix=prefix
            )
        
        temp_file.close()
        return Path(temp_file.name)
    
    def save_upload(self, file_data: Union[bytes, BinaryIO], filename: str) -> Path:
        """Save uploaded file"""
        file_path = self.get_upload_path(filename)
        
        try:
            if isinstance(file_data, bytes):
                file_path.write_bytes(file_data)
            else:
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(file_data, f)
            
            logger.info(f"Saved upload: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving upload: {e}")
            raise
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old temporary files"""
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for directory in [self.upload_path, self.export_path, self.cache_path]:
            if not directory.exists():
                continue
                
            for file_path in directory.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            logger.info(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error cleaning up file {file_path}: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security"""
        import re
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace dangerous characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Ensure reasonable length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename
    
    def get_storage_info(self) -> dict:
        """Get storage usage information"""
        info = {
            'base_path': str(self.base_path),
            'is_render': self.is_render,
            'directories': {}
        }
        
        for name, path in [
            ('uploads', self.upload_path),
            ('exports', self.export_path),
            ('cache', self.cache_path)
        ]:
            if path.exists():
                files = list(path.iterdir())
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                info['directories'][name] = {
                    'path': str(path),
                    'file_count': len(files),
                    'total_size_mb': round(total_size / (1024 * 1024), 2)
                }
        
        return info

# Global instance - lazy initialization
_file_storage = None

def get_file_storage():
    """Get or create file storage instance"""
    global _file_storage
    if _file_storage is None:
        _file_storage = FileStorageManager()
    return _file_storage

# For backward compatibility
file_storage = get_file_storage()