"""
File Manager - Utilities for file operations and temp folder management
Handles file I/O, cleanup, and organization
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta

import config


class FileManager:
    """Manager for file operations and temporary files"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize file manager
        
        Args:
            base_dir: Base directory for file operations (optional)
        """
        self.base_dir = base_dir or config.PROJECT_ROOT
        self.temp_dir = config.TEMP_DIR
        self.downloads_dir = config.DOWNLOADS_DIR
        self.outputs_dir = config.OUTPUTS_DIR
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Track created files for cleanup
        self.created_files: List[str] = []
        self.created_dirs: List[str] = []
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        for directory in [self.temp_dir, self.downloads_dir, self.outputs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def create_temp_file(
        self,
        prefix: str = 'temp_',
        suffix: str = '.mp4',
        dir: Optional[Path] = None
    ) -> str:
        """
        Create a temporary file
        
        Args:
            prefix: Filename prefix
            suffix: File extension
            dir: Directory to create file in (optional)
            
        Returns:
            Path to temporary file
        """
        if dir is None:
            dir = self.temp_dir
        
        # Create unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}{timestamp}{suffix}"
        filepath = dir / filename
        
        # Track for cleanup
        self.created_files.append(str(filepath))
        
        return str(filepath)
    
    def create_temp_dir(
        self,
        prefix: str = 'temp_dir_'
    ) -> str:
        """
        Create a temporary directory
        
        Args:
            prefix: Directory name prefix
            
        Returns:
            Path to temporary directory
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dirname = f"{prefix}{timestamp}"
        dirpath = self.temp_dir / dirname
        
        dirpath.mkdir(parents=True, exist_ok=True)
        
        # Track for cleanup
        self.created_dirs.append(str(dirpath))
        
        return str(dirpath)
    
    def cleanup_file(self, filepath: str) -> bool:
        """
        Delete a file
        
        Args:
            filepath: Path to file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
                
                # Remove from tracking
                if filepath in self.created_files:
                    self.created_files.remove(filepath)
                
                return True
            return False
        except Exception as e:
            if config.DEBUG:
                print(f"Error deleting file {filepath}: {str(e)}")
            return False
    
    def cleanup_directory(self, dirpath: str, recursive: bool = True) -> bool:
        """
        Delete a directory
        
        Args:
            dirpath: Path to directory
            recursive: Delete recursively
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(dirpath):
                if recursive:
                    shutil.rmtree(dirpath)
                else:
                    os.rmdir(dirpath)
                
                # Remove from tracking
                if dirpath in self.created_dirs:
                    self.created_dirs.remove(dirpath)
                
                return True
            return False
        except Exception as e:
            if config.DEBUG:
                print(f"Error deleting directory {dirpath}: {str(e)}")
            return False
    
    def cleanup_all(self) -> None:
        """Clean up all tracked files and directories"""
        # Clean up files
        for filepath in self.created_files[:]:
            self.cleanup_file(filepath)
        
        # Clean up directories
        for dirpath in self.created_dirs[:]:
            self.cleanup_directory(dirpath)
    
    def cleanup_old_files(self, days: int = None) -> int:
        """
        Clean up old temporary files
        
        Args:
            days: Delete files older than this many days (uses config default if None)
            
        Returns:
            Number of files deleted
        """
        if days is None:
            days = config.CLEANUP_AFTER_DAYS
        
        if not config.AUTO_CLEANUP:
            return 0
        
        deleted_count = 0
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        # Clean up temp directory
        if self.temp_dir.exists():
            for item in self.temp_dir.iterdir():
                try:
                    # Check modification time
                    if item.stat().st_mtime < cutoff_time:
                        if item.is_file():
                            item.unlink()
                            deleted_count += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            deleted_count += 1
                except Exception as e:
                    if config.DEBUG:
                        print(f"Error deleting old file {item}: {str(e)}")
        
        return deleted_count
    
    def get_file_size(self, filepath: str) -> int:
        """
        Get file size in bytes
        
        Args:
            filepath: Path to file
            
        Returns:
            File size in bytes, 0 if error
        """
        try:
            return os.path.getsize(filepath)
        except Exception:
            return 0
    
    def get_file_size_mb(self, filepath: str) -> float:
        """
        Get file size in megabytes
        
        Args:
            filepath: Path to file
            
        Returns:
            File size in MB
        """
        size_bytes = self.get_file_size(filepath)
        return size_bytes / (1024 * 1024)
    
    def get_directory_size(self, dirpath: str) -> int:
        """
        Get total size of directory in bytes
        
        Args:
            dirpath: Path to directory
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        try:
            for dirpath_iter, dirnames, filenames in os.walk(dirpath):
                for filename in filenames:
                    filepath = os.path.join(dirpath_iter, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting directory size: {str(e)}")
        
        return total_size
    
    def move_file(self, src: str, dst: str) -> bool:
        """
        Move file from source to destination
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(src, dst)
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error moving file: {str(e)}")
            return False
    
    def copy_file(self, src: str, dst: str) -> bool:
        """
        Copy file from source to destination
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            if config.DEBUG:
                print(f"Error copying file: {str(e)}")
            return False
    
    def list_files(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = False
    ) -> List[str]:
        """
        List files in directory
        
        Args:
            directory: Directory path
            extensions: Filter by extensions (e.g., ['.mp4', '.mov'])
            recursive: Search recursively
            
        Returns:
            List of file paths
        """
        files = []
        
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return files
            
            if recursive:
                pattern = '**/*'
            else:
                pattern = '*'
            
            for item in dir_path.glob(pattern):
                if item.is_file():
                    if extensions is None or item.suffix.lower() in extensions:
                        files.append(str(item))
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error listing files: {str(e)}")
        
        return files
    
    # ========================================================================
    # NEW: PATH RESOLUTION AND VIDEO FINDING HELPERS
    # ========================================================================
    
    def resolve_path(self, path: str) -> Optional[str]:
        """
        Resolve relative/absolute paths and expand user home directory
        
        Args:
            path: File or folder path (can be relative, absolute, or with ~)
            
        Returns:
            Absolute resolved path or None if invalid
        """
        try:
            # Strip quotes if present (from drag-and-drop)
            path = path.strip().strip('"').strip("'")
            
            # Expand user home directory (~)
            expanded = os.path.expanduser(path)
            
            # Convert to absolute path
            absolute = os.path.abspath(expanded)
            
            # Check if exists
            if os.path.exists(absolute):
                return absolute
            
            # Try relative to project root
            relative_to_root = os.path.join(str(self.base_dir), path)
            if os.path.exists(relative_to_root):
                return os.path.abspath(relative_to_root)
            
            return None
        except Exception as e:
            if config.DEBUG:
                print(f"Error resolving path: {str(e)}")
            return None
    
    def find_videos_in_folder(
        self,
        folder_path: str,
        recursive: bool = False
    ) -> List[str]:
        """
        Find all video files in a folder
        
        Args:
            folder_path: Path to folder
            recursive: Search recursively in subfolders
            
        Returns:
            List of video file paths (sorted)
        """
        videos = self.list_files(
            folder_path,
            extensions=config.VIDEO_EXTENSIONS,
            recursive=recursive
        )
        
        # Sort by name for consistent ordering
        videos.sort()
        
        return videos
    
    def find_audios_in_folder(
        self,
        folder_path: str,
        recursive: bool = False
    ) -> List[str]:
        """
        Find all audio files in a folder
        
        Args:
            folder_path: Path to folder
            recursive: Search recursively in subfolders
            
        Returns:
            List of audio file paths (sorted)
        """
        audios = self.list_files(
            folder_path,
            extensions=config.AUDIO_EXTENSIONS,
            recursive=recursive
        )
        
        # Sort by name
        audios.sort()
        
        return audios
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize path (resolve .., ., etc.)
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        return os.path.normpath(path)
    
    def is_relative_path(self, path: str) -> bool:
        """
        Check if path is relative
        
        Args:
            path: Path to check
            
        Returns:
            True if relative, False if absolute
        """
        return not os.path.isabs(path)
    
    def make_relative_path(self, path: str, base: Optional[str] = None) -> str:
        """
        Make path relative to base directory
        
        Args:
            path: Absolute path
            base: Base directory (defaults to project root)
            
        Returns:
            Relative path
        """
        if base is None:
            base = str(self.base_dir)
        
        try:
            return os.path.relpath(path, base)
        except ValueError:
            # Can't make relative (different drives on Windows)
            return path
    
    def get_file_extension(self, filepath: str) -> str:
        """
        Get file extension (lowercase, with dot)
        
        Args:
            filepath: Path to file
            
        Returns:
            Extension (e.g., '.mp4')
        """
        return Path(filepath).suffix.lower()
    
    def get_filename(self, filepath: str, with_extension: bool = True) -> str:
        """
        Get filename from path
        
        Args:
            filepath: Path to file
            with_extension: Include extension
            
        Returns:
            Filename
        """
        path_obj = Path(filepath)
        if with_extension:
            return path_obj.name
        else:
            return path_obj.stem
    
    def change_extension(self, filepath: str, new_extension: str) -> str:
        """
        Change file extension
        
        Args:
            filepath: Original file path
            new_extension: New extension (with or without dot)
            
        Returns:
            New file path with changed extension
        """
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension
        
        path_obj = Path(filepath)
        return str(path_obj.with_suffix(new_extension))
    
    def ensure_unique_path(self, filepath: str) -> str:
        """
        Ensure path is unique by adding numbers if file exists
        
        Args:
            filepath: Desired file path
            
        Returns:
            Unique file path
        """
        if not os.path.exists(filepath):
            return filepath
        
        path_obj = Path(filepath)
        base = path_obj.stem
        ext = path_obj.suffix
        parent = path_obj.parent
        
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return str(new_path)
            
            counter += 1
    
    def get_disk_space(self) -> Dict[str, float]:
        """
        Get disk space information
        
        Returns:
            Dict with total, used, and free space in GB
        """
        try:
            stat = shutil.disk_usage(self.base_dir)
            
            return {
                'total_gb': stat.total / (1024 ** 3),
                'used_gb': stat.used / (1024 ** 3),
                'free_gb': stat.free / (1024 ** 3),
                'percent_used': (stat.used / stat.total) * 100 if stat.total > 0 else 0,
            }
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting disk space: {str(e)}")
            return {}


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================

_global_manager = None


def get_manager() -> FileManager:
    """Get global file manager instance"""
    global _global_manager
    if _global_manager is None:
        _global_manager = FileManager()
    return _global_manager


def create_temp_dir(prefix: str = 'temp_dir_') -> str:
    """Create temporary directory"""
    manager = get_manager()
    return manager.create_temp_dir(prefix)


def cleanup_temp_files() -> None:
    """Clean up all temporary files"""
    manager = get_manager()
    manager.cleanup_all()


def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    manager = get_manager()
    return manager.get_file_size(filepath)


def get_file_extension(filepath: str) -> str:
    """Get file extension"""
    return Path(filepath).suffix.lower()


def is_video_file(filepath: str) -> bool:
    """Check if file is a video"""
    ext = get_file_extension(filepath)
    return ext in config.VIDEO_EXTENSIONS


def is_audio_file(filepath: str) -> bool:
    """Check if file is an audio file"""
    ext = get_file_extension(filepath)
    return ext in config.AUDIO_EXTENSIONS


def ensure_dir_exists(dirpath: str) -> None:
    """Ensure directory exists"""
    Path(dirpath).mkdir(parents=True, exist_ok=True)


def cleanup_old_temp_files(days: int = None) -> int:
    """Clean up old temporary files"""
    manager = get_manager()
    return manager.cleanup_old_files(days)


def get_temp_dir() -> Path:
    """Get temporary directory path"""
    return config.TEMP_DIR


def get_downloads_dir() -> Path:
    """Get downloads directory path"""
    return config.DOWNLOADS_DIR


def get_outputs_dir() -> Path:
    """Get outputs directory path"""
    return config.OUTPUTS_DIR


# ============================================================================
# NEW: PATH RESOLUTION FUNCTIONS
# ============================================================================

def resolve_path(path: str) -> Optional[str]:
    """Resolve file path (handles ~, relative paths, etc.)"""
    manager = get_manager()
    return manager.resolve_path(path)


def find_videos_in_folder(folder_path: str, recursive: bool = False) -> List[str]:
    """Find all videos in folder"""
    manager = get_manager()
    return manager.find_videos_in_folder(folder_path, recursive)


def find_audios_in_folder(folder_path: str, recursive: bool = False) -> List[str]:
    """Find all audio files in folder"""
    manager = get_manager()
    return manager.find_audios_in_folder(folder_path, recursive)


def normalize_path(path: str) -> str:
    """Normalize path"""
    manager = get_manager()
    return manager.normalize_path(path)


def get_filename(filepath: str, with_extension: bool = True) -> str:
    """Get filename from path"""
    manager = get_manager()
    return manager.get_filename(filepath, with_extension)


def ensure_unique_path(filepath: str) -> str:
    """Ensure path is unique"""
    manager = get_manager()
    return manager.ensure_unique_path(filepath)