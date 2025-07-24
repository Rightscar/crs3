"""
File Manager
============

Manages file uploads, storage, and cleanup.
"""

import os
import time
from pathlib import Path
from typing import Optional, List
import hashlib
from datetime import datetime, timedelta

from config.settings import UPLOAD_DIR
from config.logging_config import logger


class FileManager:
    """Manages file operations and cleanup"""
    
    def __init__(self):
        """Initialize file manager"""
        self.upload_dir = UPLOAD_DIR
        self.max_file_age_hours = 24  # Clean up files older than 24 hours
        self.max_file_size_mb = int(os.getenv('UPLOAD_MAX_SIZE_MB', 100))
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Optional[Path]:
        """
        Save uploaded file with unique name
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(file_content).hexdigest()[:8]
            
            # Get file extension
            ext = Path(filename).suffix
            unique_filename = f"{timestamp}_{file_hash}{ext}"
            
            # Save file
            file_path = self.upload_dir / unique_filename
            file_path.write_bytes(file_content)
            
            logger.info(f"Saved uploaded file: {unique_filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            return None
    
    def cleanup_old_files(self) -> int:
        """
        Clean up old uploaded files
        
        Returns:
            Number of files cleaned up
        """
        try:
            count = 0
            current_time = time.time()
            max_age_seconds = self.max_file_age_hours * 3600
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    # Check file age
                    file_age = current_time - file_path.stat().st_mtime
                    
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        count += 1
                        logger.info(f"Cleaned up old file: {file_path.name}")
            
            if count > 0:
                logger.info(f"Cleaned up {count} old files")
            
            return count
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
            return 0
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get information about a file"""
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'age_hours': (time.time() - stat.st_mtime) / 3600
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}
    
    def validate_file_size(self, file_content: bytes) -> bool:
        """Validate file size is within limits"""
        size_mb = len(file_content) / (1024 * 1024)
        return size_mb <= self.max_file_size_mb
    
    def get_upload_stats(self) -> dict:
        """Get statistics about uploaded files"""
        try:
            files = list(self.upload_dir.iterdir())
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            return {
                'total_files': len(files),
                'total_size_mb': total_size / (1024 * 1024),
                'oldest_file_hours': self._get_oldest_file_age(),
                'available_space_mb': self._get_available_space()
            }
        except Exception as e:
            logger.error(f"Error getting upload stats: {e}")
            return {}
    
    def _get_oldest_file_age(self) -> float:
        """Get age of oldest file in hours"""
        try:
            files = list(self.upload_dir.iterdir())
            if not files:
                return 0
            
            oldest_time = min(f.stat().st_mtime for f in files if f.is_file())
            return (time.time() - oldest_time) / 3600
            
        except:
            return 0
    
    def _get_available_space(self) -> float:
        """Get available disk space in MB"""
        try:
            stat = os.statvfs(self.upload_dir)
            return (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        except:
            return 0
    
    def schedule_cleanup(self):
        """Schedule periodic cleanup (to be called by a scheduler)"""
        # This would be called by a background scheduler like APScheduler
        # For now, it can be called manually
        self.cleanup_old_files()


# Global file manager instance
file_manager = FileManager()