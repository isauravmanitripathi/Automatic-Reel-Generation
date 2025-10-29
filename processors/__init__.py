"""
Processors module for Better Reel Generator
Handles video normalization, combination, audio analysis, cutting, and image overlay
"""

from .normalizer import normalize_video, batch_normalize
from .combiner import merge_videos, concatenate_segments
from .audio_analyzer import detect_beats, detect_vocal_changes, analyze_audio
from .video_cutter import create_segments, merge_with_audio, extract_segment
from .image_overlay import (
    overlay_images_on_video,
    preview_image_timing,
    get_images_from_folder,
    validate_overlay_inputs,
    ImageOverlayProcessor
)
from .text_overlay import (
    overlay_text_on_video,
    TextOverlayProcessor,
    validate_text_overlay_inputs,
    preview_text_overlay,
)

__all__ = [
    # Normalizer
    'normalize_video',
    'batch_normalize',
    
    # Combiner
    'merge_videos',
    'concatenate_segments',
    
    # Audio Analyzer
    'detect_beats',
    'detect_vocal_changes',
    'analyze_audio',
    
    # Video Cutter
    'create_segments',
    'merge_with_audio',
    'extract_segment',
    
    # Image Overlay
    'overlay_images_on_video',
    'preview_image_timing',
    'get_images_from_folder',
    'validate_overlay_inputs',
    'ImageOverlayProcessor',
    
    # Text Overlay
    'overlay_text_on_video',
    'TextOverlayProcessor',
    'validate_text_overlay_inputs',
    'preview_text_overlay',
]

__version__ = '1.0.0'