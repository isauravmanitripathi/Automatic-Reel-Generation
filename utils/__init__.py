"""
Utils module for Better Reel Generator
Provides utility functions for FFmpeg, file management, and validation
"""

from .ffmpeg_helper import (
    check_ffmpeg,
    get_video_info,
    get_audio_duration,
    get_video_duration,
    extract_audio_from_video,
    get_video_resolution,
    get_video_fps,
    get_video_codec,
    convert_video_format,
)

from .file_manager import (
    FileManager,
    create_temp_dir,
    cleanup_temp_files,
    get_file_size,
    get_file_extension,
    is_video_file,
    is_audio_file,
    ensure_dir_exists,
)

from .validators import (
    is_valid_url,
    is_valid_video,
    is_valid_audio,
    detect_source,
    validate_file_size,
    validate_video_duration,
)

__all__ = [
    # FFmpeg Helper
    'check_ffmpeg',
    'get_video_info',
    'get_audio_duration',
    'get_video_duration',
    'extract_audio_from_video',
    'get_video_resolution',
    'get_video_fps',
    'get_video_codec',
    'convert_video_format',
    
    # File Manager
    'FileManager',
    'create_temp_dir',
    'cleanup_temp_files',
    'get_file_size',
    'get_file_extension',
    'is_video_file',
    'is_audio_file',
    'ensure_dir_exists',
    
    # Validators
    'is_valid_url',
    'is_valid_video',
    'is_valid_audio',
    'detect_source',
    'validate_file_size',
    'validate_video_duration',
]

__version__ = '1.0.0'