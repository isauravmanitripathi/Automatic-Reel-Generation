"""
Downloaders module for Better Reel Generator
Handles downloading from YouTube, Instagram, and Pinterest
"""

from .youtube import download as download_youtube
from .instagram import download as download_instagram
from .pinterest import download as download_pinterest

__all__ = [
    'download_youtube',
    'download_instagram',
    'download_pinterest',
]

# Version
__version__ = '1.0.0'