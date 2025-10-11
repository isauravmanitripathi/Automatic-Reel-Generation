"""
Configuration constants for Better Reel Generator
"""
import os
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
NORMALIZED_DIR = PROJECT_ROOT / "normalized"
TEMP_DIR = PROJECT_ROOT / "temp"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Create directories if they don't exist
for directory in [DOWNLOADS_DIR, NORMALIZED_DIR, TEMP_DIR, OUTPUTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# VIDEO SETTINGS
# ============================================================================
# Target resolutions for different platforms
RESOLUTIONS = {
    'reels': (1080, 1920),      # Instagram Reels / TikTok (9:16)
    'shorts': (1080, 1920),     # YouTube Shorts (9:16)
    'story': (1080, 1920),      # Instagram Story (9:16)
    'landscape': (1920, 1080),  # YouTube (16:9)
    'square': (1080, 1080),     # Instagram Square (1:1)
}

# Video encoding settings
VIDEO_CODEC = 'libx264'
VIDEO_PRESET = 'medium'  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
VIDEO_CRF = 23  # Constant Rate Factor (0-51, lower = better quality, 18-28 recommended)
TARGET_FPS = 30
TARGET_BITRATE = '5M'

# Audio encoding settings
AUDIO_CODEC = 'aac'
AUDIO_BITRATE = '192k'
AUDIO_SAMPLE_RATE = 48000

# ============================================================================
# DOWNLOAD SETTINGS
# ============================================================================
# yt-dlp settings
YTDLP_FORMAT = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
YTDLP_AUDIO_FORMAT = 'bestaudio[ext=m4a]/bestaudio'

# gallery-dl settings (for Instagram/Pinterest)
GALLERY_DL_CONFIG = {
    'extractor': {
        'instagram': {
            'videos': True,
            'video-reels': True
        },
        'pinterest': {
            'videos': True
        }
    }
}

# Maximum concurrent downloads
MAX_CONCURRENT_DOWNLOADS = 3

# ============================================================================
# AUDIO ANALYSIS SETTINGS
# ============================================================================
# Beat detection
BEAT_TRACK_UNITS = 'time'  # 'time' or 'frames'
BEAT_HOP_LENGTH = 512
BEAT_START_BPM = 120

# Vocal detection
VOCAL_THRESHOLD = 0.5  # Lower = more sensitive
VOCAL_MIN_CHANGES = 5

# ============================================================================
# VIDEO CUTTING SETTINGS
# ============================================================================
# Cutting modes
CUT_MODES = {
    'beats': 'Beat Detection',
    'vocals': 'Vocal Changes',
    'hybrid': 'Beats + Vocals'
}

# Segment ordering
ORDER_MODES = {
    'sequential': 'Sequential (in order)',
    'random': 'Random (shuffled)'
}

# Minimum and maximum segment duration (seconds)
MIN_SEGMENT_DURATION = 0.3
MAX_SEGMENT_DURATION = 5.0

# ============================================================================
# FFMPEG SETTINGS
# ============================================================================
FFMPEG_THREADS = os.cpu_count() or 4
FFMPEG_LOGLEVEL = 'error'  # quiet, panic, fatal, error, warning, info, verbose, debug

# Normalization filters
NORMALIZE_FILTERS = {
    'denoise': 'hqdn3d=1.5:1.5:6:6',
    'stabilize': 'deshake',
    'sharpen': 'unsharp=5:5:1.0:5:5:0.0',
}

# ============================================================================
# FILE MANAGEMENT
# ============================================================================
# Supported file extensions
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# Maximum file size for processing (in MB)
MAX_FILE_SIZE_MB = 1000

# Auto-cleanup temp files after processing
AUTO_CLEANUP = True
CLEANUP_AFTER_DAYS = 7

# ============================================================================
# URL PATTERNS
# ============================================================================
URL_PATTERNS = {
    'youtube': [
        r'youtube\.com/watch',
        r'youtube\.com/shorts',
        r'youtu\.be/',
        r'youtube\.com/embed'
    ],
    'instagram': [
        r'instagram\.com/reel',
        r'instagram\.com/p/',
        r'instagram\.com/tv'
    ],
    'pinterest': [
        r'pinterest\.com/pin',
        r'pin\.it/'
    ]
}

# ============================================================================
# CLI SETTINGS
# ============================================================================
# Rich console theme
CONSOLE_THEME = {
    'success': 'green',
    'error': 'red',
    'warning': 'yellow',
    'info': 'cyan',
    'progress': 'magenta'
}

# Progress bar style
PROGRESS_BAR_STYLE = 'bar.complete'

# ============================================================================
# VALIDATION RULES
# ============================================================================
# Minimum video duration (seconds)
MIN_VIDEO_DURATION = 1.0

# Maximum number of URLs to process at once
MAX_URLS_PER_BATCH = 20

# Maximum total video duration for combining (seconds)
MAX_COMBINED_DURATION = 300  # 5 minutes

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_MESSAGES = {
    'invalid_url': '❌ Invalid URL provided',
    'download_failed': '❌ Download failed',
    'no_videos': '❌ No videos found',
    'normalization_failed': '❌ Video normalization failed',
    'combine_failed': '❌ Failed to combine videos',
    'audio_analysis_failed': '❌ Audio analysis failed',
    'cutting_failed': '❌ Video cutting failed',
    'invalid_audio': '❌ Invalid audio file',
    'ffmpeg_not_found': '❌ FFmpeg not found. Please install FFmpeg.',
}

SUCCESS_MESSAGES = {
    'download_complete': '✅ Download complete',
    'normalization_complete': '✅ Normalization complete',
    'combine_complete': '✅ Videos combined successfully',
    'audio_analysis_complete': '✅ Audio analysis complete',
    'cutting_complete': '✅ Video cutting complete',
    'generation_complete': '✅ Video generation complete',
}

# ============================================================================
# DEBUG MODE
# ============================================================================
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VERBOSE = os.getenv('VERBOSE', 'False').lower() == 'true'

# ============================================================================
# VERSION
# ============================================================================
VERSION = '1.0.0'
APP_NAME = 'Better Reel Generator'