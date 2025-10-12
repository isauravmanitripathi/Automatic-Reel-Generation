"""
Validators - URL validation, file validation, and source detection
Provides validation functions for URLs, files, and media content
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple
from urllib.parse import urlparse, parse_qs
import validators as validator_lib

import config
from .ffmpeg_helper import get_video_info, get_audio_info


class Validator:
    """Validator for URLs, files, and media content"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if URL is valid
        
        Args:
            url: URL string to validate
            
        Returns:
            True if valid URL, False otherwise
        """
        try:
            # Use validators library
            result = validator_lib.url(url)
            return result is True
        except Exception:
            return False
    
    @staticmethod
    def detect_source(url: str) -> Optional[str]:
        """
        Detect the source platform from URL
        
        Args:
            url: URL to analyze
            
        Returns:
            Source name ('youtube', 'instagram', 'pinterest') or None
        """
        try:
            url_lower = url.lower()
            
            # Check YouTube patterns
            for pattern in config.URL_PATTERNS['youtube']:
                if re.search(pattern, url_lower):
                    return 'youtube'
            
            # Check Instagram patterns
            for pattern in config.URL_PATTERNS['instagram']:
                if re.search(pattern, url_lower):
                    return 'instagram'
            
            # Check Pinterest patterns
            for pattern in config.URL_PATTERNS['pinterest']:
                if re.search(pattern, url_lower):
                    return 'pinterest'
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error detecting source: {str(e)}")
            return None
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if URL is from YouTube"""
        return Validator.detect_source(url) == 'youtube'
    
    @staticmethod
    def is_instagram_url(url: str) -> bool:
        """Check if URL is from Instagram"""
        return Validator.detect_source(url) == 'instagram'
    
    @staticmethod
    def is_pinterest_url(url: str) -> bool:
        """Check if URL is from Pinterest"""
        return Validator.detect_source(url) == 'pinterest'
    
    @staticmethod
    def is_shorts_url(url: str) -> bool:
        """Check if URL is a YouTube Short"""
        return '/shorts/' in url.lower()
    
    @staticmethod
    def is_reel_url(url: str) -> bool:
        """Check if URL is an Instagram Reel"""
        return '/reel/' in url.lower()
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extract video ID from URL
        
        Args:
            url: Video URL
            
        Returns:
            Video ID or None
        """
        try:
            source = Validator.detect_source(url)
            
            if source == 'youtube':
                # YouTube video ID patterns
                patterns = [
                    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]+)',
                    r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        return match.group(1)
            
            elif source == 'instagram':
                # Instagram post/reel ID
                match = re.search(r'/(?:p|reel|tv)/([a-zA-Z0-9_-]+)', url)
                if match:
                    return match.group(1)
            
            elif source == 'pinterest':
                # Pinterest pin ID
                match = re.search(r'/pin/(\d+)', url)
                if match:
                    return match.group(1)
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error extracting video ID: {str(e)}")
            return None
    
    # ========================================================================
    # NEW: LOCAL PATH VALIDATION
    # ========================================================================
    
    @staticmethod
    def is_valid_path(path: str) -> bool:
        """
        Check if path exists and is accessible
        
        Args:
            path: File or folder path
            
        Returns:
            True if valid path, False otherwise
        """
        try:
            # Expand user home directory and resolve path
            expanded = os.path.expanduser(path)
            resolved = os.path.abspath(expanded)
            
            # Check if exists and is readable
            if not os.path.exists(resolved):
                return False
            
            if not os.access(resolved, os.R_OK):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def is_video_folder(folder_path: str) -> Tuple[bool, int]:
        """
        Check if folder contains video files
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Tuple of (has_videos, count)
        """
        try:
            if not os.path.isdir(folder_path):
                return False, 0
            
            video_count = 0
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    ext = Path(item_path).suffix.lower()
                    if ext in config.VIDEO_EXTENSIONS:
                        video_count += 1
            
            return video_count > 0, video_count
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error checking video folder: {str(e)}")
            return False, 0
    
    @staticmethod
    def validate_local_video(filepath: str) -> Tuple[bool, str]:
        """
        Comprehensive validation for local video file
        
        Args:
            filepath: Path to video file
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check if file exists
        if not os.path.exists(filepath):
            return False, "File does not exist"
        
        # Check if it's a file (not a directory)
        if not os.path.isfile(filepath):
            return False, "Path is not a file"
        
        # Check if readable
        if not os.access(filepath, os.R_OK):
            return False, "File is not readable (permission denied)"
        
        # Check extension
        ext = Path(filepath).suffix.lower()
        if ext not in config.VIDEO_EXTENSIONS:
            return False, f"Unsupported video format: {ext}"
        
        # Validate with FFmpeg (can read video info)
        try:
            info = get_video_info(filepath)
            if not info:
                return False, "Cannot read video file (may be corrupted)"
            
            # Basic sanity checks
            if info.get('duration', 0) <= 0:
                return False, "Invalid video duration"
            
            if info.get('width', 0) <= 0 or info.get('height', 0) <= 0:
                return False, "Invalid video resolution"
        
        except Exception as e:
            return False, f"Error reading video: {str(e)}"
        
        # Check file size
        size_valid, size_msg = Validator.validate_file_size(filepath)
        if not size_valid:
            return False, size_msg
        
        # Check duration
        duration_valid, duration_msg = Validator.validate_video_duration(filepath)
        if not duration_valid:
            return False, duration_msg
        
        return True, "Video is valid"
    
    @staticmethod
    def validate_local_audio(filepath: str) -> Tuple[bool, str]:
        """
        Comprehensive validation for local audio file
        
        Args:
            filepath: Path to audio file
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check if file exists
        if not os.path.exists(filepath):
            return False, "File does not exist"
        
        # Check if it's a file
        if not os.path.isfile(filepath):
            return False, "Path is not a file"
        
        # Check if readable
        if not os.access(filepath, os.R_OK):
            return False, "File is not readable (permission denied)"
        
        # Check extension
        ext = Path(filepath).suffix.lower()
        if ext not in config.AUDIO_EXTENSIONS:
            return False, f"Unsupported audio format: {ext}"
        
        # Validate with FFmpeg
        try:
            info = get_audio_info(filepath)
            if not info:
                return False, "Cannot read audio file (may be corrupted)"
            
            if info.get('duration', 0) <= 0:
                return False, "Invalid audio duration"
        
        except Exception as e:
            return False, f"Error reading audio: {str(e)}"
        
        # Check file size
        size_valid, size_msg = Validator.validate_file_size(filepath)
        if not size_valid:
            return False, size_msg
        
        return True, "Audio is valid"
    
    # ========================================================================
    # EXISTING FILE VALIDATION (kept as-is)
    # ========================================================================
    
    @staticmethod
    def is_valid_video_file(filepath: str) -> bool:
        """
        Check if file is a valid video
        
        Args:
            filepath: Path to file
            
        Returns:
            True if valid video file, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return False
            
            # Check extension
            ext = Path(filepath).suffix.lower()
            if ext not in config.VIDEO_EXTENSIONS:
                return False
            
            # Try to get video info
            info = get_video_info(filepath)
            
            # Validate info
            if info and info.get('duration', 0) > 0:
                return True
            
            return False
        
        except Exception:
            return False
    
    @staticmethod
    def is_valid_audio_file(filepath: str) -> bool:
        """
        Check if file is a valid audio file
        
        Args:
            filepath: Path to file
            
        Returns:
            True if valid audio file, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return False
            
            # Check extension
            ext = Path(filepath).suffix.lower()
            if ext not in config.AUDIO_EXTENSIONS:
                return False
            
            # Try to get audio info
            info = get_audio_info(filepath)
            
            # Validate info
            if info and info.get('duration', 0) > 0:
                return True
            
            return False
        
        except Exception:
            return False
    
    @staticmethod
    def validate_file_size(filepath: str, max_size_mb: Optional[int] = None) -> Tuple[bool, str]:
        """
        Validate file size
        
        Args:
            filepath: Path to file
            max_size_mb: Maximum allowed size in MB (uses config default if None)
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(filepath):
                return False, "File not found"
            
            if max_size_mb is None:
                max_size_mb = config.MAX_FILE_SIZE_MB
            
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                return False, f"File too large: {file_size_mb:.2f}MB (max: {max_size_mb}MB)"
            
            return True, f"File size OK: {file_size_mb:.2f}MB"
        
        except Exception as e:
            return False, f"Error checking file size: {str(e)}"
    
    @staticmethod
    def validate_video_duration(
        filepath: str,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate video duration
        
        Args:
            filepath: Path to video file
            min_duration: Minimum duration in seconds (uses config default if None)
            max_duration: Maximum duration in seconds (optional)
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(filepath):
                return False, "File not found"
            
            info = get_video_info(filepath)
            
            if not info:
                return False, "Could not read video file"
            
            duration = info.get('duration', 0)
            
            if min_duration is None:
                min_duration = config.MIN_VIDEO_DURATION
            
            if duration < min_duration:
                return False, f"Video too short: {duration:.2f}s (min: {min_duration}s)"
            
            if max_duration and duration > max_duration:
                return False, f"Video too long: {duration:.2f}s (max: {max_duration}s)"
            
            return True, f"Duration OK: {duration:.2f}s"
        
        except Exception as e:
            return False, f"Error checking duration: {str(e)}"
    
    @staticmethod
    def validate_video_resolution(
        filepath: str,
        min_width: int = 720,
        min_height: int = 480
    ) -> Tuple[bool, str]:
        """
        Validate video resolution
        
        Args:
            filepath: Path to video file
            min_width: Minimum width in pixels
            min_height: Minimum height in pixels
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(filepath):
                return False, "File not found"
            
            info = get_video_info(filepath)
            
            if not info:
                return False, "Could not read video file"
            
            width = info.get('width', 0)
            height = info.get('height', 0)
            
            if width < min_width or height < min_height:
                return False, f"Resolution too low: {width}x{height} (min: {min_width}x{min_height})"
            
            return True, f"Resolution OK: {width}x{height}"
        
        except Exception as e:
            return False, f"Error checking resolution: {str(e)}"
    
    @staticmethod
    def validate_audio_duration(
        filepath: str,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate audio duration
        
        Args:
            filepath: Path to audio file
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(filepath):
                return False, "File not found"
            
            info = get_audio_info(filepath)
            
            if not info:
                return False, "Could not read audio file"
            
            duration = info.get('duration', 0)
            
            if min_duration and duration < min_duration:
                return False, f"Audio too short: {duration:.2f}s (min: {min_duration}s)"
            
            if max_duration and duration > max_duration:
                return False, f"Audio too long: {duration:.2f}s (max: {max_duration}s)"
            
            return True, f"Duration OK: {duration:.2f}s"
        
        except Exception as e:
            return False, f"Error checking audio duration: {str(e)}"
    
    @staticmethod
    def validate_batch_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a batch of URLs
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            Tuple of (valid_urls, invalid_urls)
        """
        valid_urls = []
        invalid_urls = []
        
        for url in urls:
            if Validator.is_valid_url(url) and Validator.detect_source(url):
                valid_urls.append(url)
            else:
                invalid_urls.append(url)
        
        return valid_urls, invalid_urls
    
    @staticmethod
    def validate_batch_size(urls: List[str]) -> Tuple[bool, str]:
        """
        Validate batch size
        
        Args:
            urls: List of URLs
            
        Returns:
            Tuple of (is_valid, message)
        """
        count = len(urls)
        max_count = config.MAX_URLS_PER_BATCH
        
        if count == 0:
            return False, "No URLs provided"
        
        if count > max_count:
            return False, f"Too many URLs: {count} (max: {max_count})"
        
        return True, f"Batch size OK: {count} URLs"
    
    @staticmethod
    def get_url_info(url: str) -> Optional[dict]:
        """
        Get information about a URL
        
        Args:
            url: URL to analyze
            
        Returns:
            Dict with URL info or None
        """
        try:
            if not Validator.is_valid_url(url):
                return None
            
            source = Validator.detect_source(url)
            video_id = Validator.extract_video_id(url)
            
            parsed = urlparse(url)
            
            return {
                'url': url,
                'source': source,
                'video_id': video_id,
                'domain': parsed.netloc,
                'path': parsed.path,
                'is_youtube': source == 'youtube',
                'is_instagram': source == 'instagram',
                'is_pinterest': source == 'pinterest',
                'is_shorts': Validator.is_shorts_url(url),
                'is_reel': Validator.is_reel_url(url),
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting URL info: {str(e)}")
            return None
    
    @staticmethod
    def check_file_accessibility(filepath: str) -> Tuple[bool, str]:
        """
        Check if file is accessible
        
        Args:
            filepath: Path to file
            
        Returns:
            Tuple of (is_accessible, message)
        """
        try:
            if not os.path.exists(filepath):
                return False, "File does not exist"
            
            if not os.path.isfile(filepath):
                return False, "Path is not a file"
            
            if not os.access(filepath, os.R_OK):
                return False, "File is not readable"
            
            return True, "File is accessible"
        
        except Exception as e:
            return False, f"Error checking file: {str(e)}"


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    return Validator.is_valid_url(url)


def detect_source(url: str) -> Optional[str]:
    """Detect source platform from URL"""
    return Validator.detect_source(url)


def is_valid_video(filepath: str) -> bool:
    """Check if file is a valid video"""
    return Validator.is_valid_video_file(filepath)


def is_valid_audio(filepath: str) -> bool:
    """Check if file is a valid audio file"""
    return Validator.is_valid_audio_file(filepath)


def validate_file_size(filepath: str, max_size_mb: Optional[int] = None) -> Tuple[bool, str]:
    """Validate file size"""
    return Validator.validate_file_size(filepath, max_size_mb)


def validate_video_duration(
    filepath: str,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None
) -> Tuple[bool, str]:
    """Validate video duration"""
    return Validator.validate_video_duration(filepath, min_duration, max_duration)


def validate_audio_duration(
    filepath: str,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None
) -> Tuple[bool, str]:
    """Validate audio duration"""
    return Validator.validate_audio_duration(filepath, min_duration, max_duration)


def is_youtube_url(url: str) -> bool:
    """Check if URL is from YouTube"""
    return Validator.is_youtube_url(url)


def is_instagram_url(url: str) -> bool:
    """Check if URL is from Instagram"""
    return Validator.is_instagram_url(url)


def is_pinterest_url(url: str) -> bool:
    """Check if URL is from Pinterest"""
    return Validator.is_pinterest_url(url)


def is_shorts_url(url: str) -> bool:
    """Check if URL is a YouTube Short"""
    return Validator.is_shorts_url(url)


def is_reel_url(url: str) -> bool:
    """Check if URL is an Instagram Reel"""
    return Validator.is_reel_url(url)


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from URL"""
    return Validator.extract_video_id(url)


def get_url_info(url: str) -> Optional[dict]:
    """Get information about a URL"""
    return Validator.get_url_info(url)


def validate_batch_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
    """Validate a batch of URLs, returns (valid, invalid)"""
    return Validator.validate_batch_urls(urls)


def validate_batch_size(urls: List[str]) -> Tuple[bool, str]:
    """Validate batch size"""
    return Validator.validate_batch_size(urls)


def check_file_accessibility(filepath: str) -> Tuple[bool, str]:
    """Check if file is accessible"""
    return Validator.check_file_accessibility(filepath)


def validate_resolution(
    filepath: str,
    min_width: int = 720,
    min_height: int = 480
) -> Tuple[bool, str]:
    """Validate video resolution"""
    return Validator.validate_video_resolution(filepath, min_width, min_height)


# ============================================================================
# NEW: LOCAL PATH VALIDATION FUNCTIONS
# ============================================================================

def is_valid_path(path: str) -> bool:
    """Check if path is valid and accessible"""
    return Validator.is_valid_path(path)


def is_video_folder(folder_path: str) -> Tuple[bool, int]:
    """Check if folder contains videos, returns (has_videos, count)"""
    return Validator.is_video_folder(folder_path)


def validate_local_video(filepath: str) -> Tuple[bool, str]:
    """Comprehensive validation for local video file"""
    return Validator.validate_local_video(filepath)


def validate_local_audio(filepath: str) -> Tuple[bool, str]:
    """Comprehensive validation for local audio file"""
    return Validator.validate_local_audio(filepath)