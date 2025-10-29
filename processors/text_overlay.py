"""
Text Overlay Processor - Add text with background box to video
Uses FFmpeg drawbox and drawtext filters to overlay text with colored background
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict

import config
from utils.ffmpeg_helper import get_video_info, get_video_resolution


class TextOverlayProcessor:
    """Handler for overlaying text with background box on video"""
    
    def __init__(self):
        """Initialize text overlay processor"""
        self.temp_dir = config.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def process(
        self,
        video_path: str,
        output_path: str,
        text: str,
        box_color: str = 'black',
        text_color: str = 'white',
        box_opacity: float = 0.7
    ) -> Optional[str]:
        """
        Overlay text with background box on video
        
        Args:
            video_path: Input video path
            output_path: Output video path
            text: Text to display
            box_color: Background box color (named color or hex)
            text_color: Text color (named color or hex)
            box_opacity: Box opacity (0-1)
            
        Returns:
            Path to output video or None if failed
        """
        try:
            # Validate video exists
            if not os.path.exists(video_path):
                if config.DEBUG:
                    print(f"Video not found: {video_path}")
                return None
            
            # Validate text
            if not text or len(text.strip()) == 0:
                if config.DEBUG:
                    print("Text cannot be empty")
                return None
            
            # Get video resolution
            resolution = get_video_resolution(video_path)
            if not resolution:
                if config.DEBUG:
                    print("Could not get video resolution")
                return None
            
            video_width, video_height = resolution
            
            if config.VERBOSE:
                print(f"\n=== TEXT OVERLAY PROCESSING ===")
                print(f"Video: {Path(video_path).name}")
                print(f"Resolution: {video_width}x{video_height}")
                print(f"Text: \"{text}\"")
                print(f"Box color: {box_color}")
                print(f"Text color: {text_color}")
                print(f"Opacity: {box_opacity}")
            
            # Calculate font size based on video width and text length
            font_size = self._calculate_font_size(text, video_width)
            
            if config.VERBOSE:
                print(f"Calculated font size: {font_size}px")
            
            # Calculate box dimensions
            box_width, box_height = self._calculate_box_dimensions(text, font_size)
            
            if config.VERBOSE:
                print(f"Box dimensions: {box_width}x{box_height}px")
            
            # Parse colors to FFmpeg format
            box_color_hex = self._parse_color(box_color)
            text_color_hex = self._parse_color(text_color)
            
            if config.VERBOSE:
                print(f"Box color (hex): {box_color_hex}")
                print(f"Text color (hex): {text_color_hex}")
            
            # Escape text for FFmpeg
            escaped_text = self._escape_text(text)
            
            # Build FFmpeg filter complex
            filter_complex = self._build_filter_complex(
                video_width=video_width,
                video_height=video_height,
                text=escaped_text,
                box_color=box_color_hex,
                text_color=text_color_hex,
                box_opacity=box_opacity,
                font_size=font_size,
                box_width=box_width,
                box_height=box_height
            )
            
            if config.VERBOSE or config.DEBUG:
                print(f"\n=== FILTER COMPLEX ===")
                print(filter_complex)
                print(f"======================\n")
            
            # Execute FFmpeg command
            success = self._execute_ffmpeg(
                video_path=video_path,
                output_path=output_path,
                filter_complex=filter_complex
            )
            
            if success and os.path.exists(output_path):
                if config.VERBOSE:
                    print(f"✓ Output saved: {output_path}")
                return output_path
            
            return None
            
        except Exception as e:
            if config.DEBUG:
                print(f"Error in text overlay process: {str(e)}")
                import traceback
                traceback.print_exc()
            return None
    
    def _calculate_font_size(self, text: str, video_width: int) -> int:
        """
        Calculate optimal font size to fit text in one line
        
        Args:
            text: Text to display
            video_width: Video width in pixels
            
        Returns:
            Font size in pixels (clamped between min and max)
        """
        # Reserve 85% of video width for text (15% for padding)
        available_width = video_width * 0.85
        
        # Get character count
        char_count = len(text)
        if char_count == 0:
            return config.TEXT_OVERLAY_MAX_FONT_SIZE
        
        # Estimate character width as 0.6 * font_size (average for most fonts)
        # Formula: available_width = char_count * (font_size * 0.6)
        # Solve for font_size: font_size = available_width / (char_count * 0.6)
        font_size = int(available_width / (char_count * 0.6))
        
        # Clamp between minimum and maximum
        font_size = max(
            config.TEXT_OVERLAY_MIN_FONT_SIZE,
            min(font_size, config.TEXT_OVERLAY_MAX_FONT_SIZE)
        )
        
        return font_size
    
    def _calculate_box_dimensions(self, text: str, font_size: int) -> Tuple[int, int]:
        """
        Calculate box width and height based on text and font size
        
        Args:
            text: Text to display
            font_size: Font size in pixels
            
        Returns:
            Tuple of (box_width, box_height)
        """
        padding = config.TEXT_OVERLAY_PADDING
        
        # Estimate text width (character count * font_size * 0.6)
        text_width = int(len(text) * font_size * 0.6)
        
        # Box width = text width + padding on both sides
        box_width = text_width + (padding * 2)
        
        # Box height = font size * 1.5 (to give vertical breathing room) + padding
        box_height = int(font_size * 1.5) + (padding * 2)
        
        return box_width, box_height
    
    def _parse_color(self, color: str) -> str:
        """
        Convert color to FFmpeg format (0xRRGGBB)
        
        Args:
            color: Color name or hex code
            
        Returns:
            Color in FFmpeg hex format (0xRRGGBB)
        """
        # Check if it's a named color from config
        if color in config.TEXT_OVERLAY_COLORS:
            return config.TEXT_OVERLAY_COLORS[color]
        
        # Check if it's already in hex format
        if color.startswith('#'):
            # Convert #RRGGBB to 0xRRGGBB
            return '0x' + color[1:]
        elif color.startswith('0x'):
            # Already in correct format
            return color
        
        # Default to black if unrecognized
        if config.DEBUG:
            print(f"Unrecognized color '{color}', defaulting to black")
        return config.TEXT_OVERLAY_COLORS['black']
    
    def _escape_text(self, text: str) -> str:
        """
        Escape special characters for FFmpeg drawtext filter
        
        FFmpeg drawtext requires escaping certain characters:
        - Backslashes (\)
        - Single quotes (')
        - Colons (:)
        
        Args:
            text: Original text
            
        Returns:
            Escaped text safe for FFmpeg
        """
        # Escape backslashes first (must be done first!)
        text = text.replace('\\', '\\\\\\\\')
        
        # Escape single quotes
        text = text.replace("'", "\\'")
        
        # Escape colons
        text = text.replace(':', '\\:')
        
        return text
    
    def _build_filter_complex(
        self,
        video_width: int,
        video_height: int,
        text: str,
        box_color: str,
        text_color: str,
        box_opacity: float,
        font_size: int,
        box_width: int,
        box_height: int
    ) -> str:
        """
        Build FFmpeg filter_complex for text overlay
        
        Creates a filter chain with:
        1. drawbox - draws colored rectangle for background
        2. drawtext - draws text on top of box
        
        Args:
            video_width: Video width
            video_height: Video height
            text: Escaped text to display
            box_color: Box color in hex format
            text_color: Text color in hex format
            box_opacity: Box opacity (0-1)
            font_size: Font size in pixels
            box_width: Box width
            box_height: Box height
            
        Returns:
            FFmpeg filter_complex string
        """
        bottom_margin = config.TEXT_OVERLAY_BOTTOM_MARGIN
        
        # Calculate box position (bottom center)
        # x: center horizontally = (video_width - box_width) / 2
        # y: position at bottom = video_height - box_height - bottom_margin
        box_x = f"(iw-{box_width})/2"
        box_y = f"ih-{box_height}-{bottom_margin}"
        
        # Calculate text position (centered within box)
        # x: center horizontally = (video_width - text_width) / 2
        # y: center vertically within box = video_height - (box_height/2) - (text_height/2) - bottom_margin
        text_x = "(w-text_w)/2"  # text_w is calculated by drawtext filter
        text_y = f"h-{box_height//2}-text_h/2-{bottom_margin}"  # text_h calculated by drawtext
        
        # Build drawbox filter
        # Draws filled rectangle with specified color and opacity
        drawbox = (
            f"drawbox="
            f"x={box_x}:"
            f"y={box_y}:"
            f"w={box_width}:"
            f"h={box_height}:"
            f"color={box_color}@{box_opacity}:"
            f"t=fill"  # t=fill means fill the box (not just outline)
        )
        
        # Build drawtext filter
        # Draws text with specified font size and color
        drawtext = (
            f"drawtext="
            f"text='{text}':"
            f"x={text_x}:"
            f"y={text_y}:"
            f"fontsize={font_size}:"
            f"fontcolor={text_color}"
        )
        
        # Combine filters with comma (sequential application)
        # First draw box, then draw text on top
        filter_complex = f"{drawbox},{drawtext}"
        
        return filter_complex
    
    def _execute_ffmpeg(
        self,
        video_path: str,
        output_path: str,
        filter_complex: str
    ) -> bool:
        """
        Execute FFmpeg command to apply text overlay
        
        Args:
            video_path: Input video path
            output_path: Output video path
            filter_complex: FFmpeg filter string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', video_path,                    # Input video
                '-vf', filter_complex,               # Video filter
                '-codec:v', config.VIDEO_CODEC,      # Video codec (h264)
                '-preset', config.VIDEO_PRESET,      # Encoding preset (medium)
                '-crf', str(config.VIDEO_CRF),       # Quality (23)
                '-codec:a', 'copy',                  # Copy audio stream (no re-encode)
                '-movflags', 'faststart',            # Enable fast start for web playback
                '-threads', str(config.FFMPEG_THREADS),  # Multi-threading
                '-y',                                # Overwrite output file
                output_path
            ]
            
            if config.VERBOSE or config.DEBUG:
                print(f"\n=== FFMPEG COMMAND ===")
                print(' '.join(cmd))
                print(f"======================\n")
            
            # Execute FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Check for errors
            if result.returncode != 0:
                if config.DEBUG:
                    print(f"FFmpeg error (return code {result.returncode}):")
                    print(f"STDERR: {result.stderr}")
                    print(f"STDOUT: {result.stdout}")
                return False
            
            if config.VERBOSE:
                print(f"✓ FFmpeg completed successfully")
            
            return True
            
        except Exception as e:
            if config.DEBUG:
                print(f"Error executing FFmpeg: {str(e)}")
                import traceback
                traceback.print_exc()
            return False
    
    def preview_settings(
        self,
        video_path: str,
        text: str
    ) -> Optional[Dict]:
        """
        Preview settings without actually processing
        
        Args:
            video_path: Video path
            text: Text to display
            
        Returns:
            Dict with preview information or None
        """
        try:
            # Get video info
            info = get_video_info(video_path)
            if not info:
                return None
            
            video_width = info['width']
            video_height = info['height']
            
            # Calculate settings
            font_size = self._calculate_font_size(text, video_width)
            box_width, box_height = self._calculate_box_dimensions(text, font_size)
            
            return {
                'video_width': video_width,
                'video_height': video_height,
                'video_duration': info['duration'],
                'font_size': font_size,
                'box_width': box_width,
                'box_height': box_height,
                'text_length': len(text),
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error in preview: {str(e)}")
            return None


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================

def overlay_text_on_video(
    video_path: str,
    output_path: str,
    text: str,
    box_color: str = 'black',
    text_color: str = 'white',
    box_opacity: float = 0.7
) -> Optional[str]:
    """
    Main function to overlay text on video with background box
    
    Args:
        video_path: Input video path
        output_path: Output video path
        text: Text to display
        box_color: Background box color (named or hex)
        text_color: Text color (named or hex)
        box_opacity: Box opacity (0-1)
        
    Returns:
        Path to output video or None if failed
    
    Example:
        >>> result = overlay_text_on_video(
        ...     video_path='input.mp4',
        ...     output_path='output.mp4',
        ...     text='www.example.com',
        ...     box_color='black',
        ...     text_color='white',
        ...     box_opacity=0.7
        ... )
        >>> print(result)
        'output.mp4'
    """
    processor = TextOverlayProcessor()
    return processor.process(
        video_path=video_path,
        output_path=output_path,
        text=text,
        box_color=box_color,
        text_color=text_color,
        box_opacity=box_opacity
    )


def validate_text_overlay_inputs(
    video_path: str,
    text: str
) -> Tuple[bool, str]:
    """
    Validate inputs for text overlay
    
    Args:
        video_path: Video path to validate
        text: Text to validate
        
    Returns:
        Tuple of (is_valid, message)
    
    Example:
        >>> valid, msg = validate_text_overlay_inputs('video.mp4', 'Hello World')
        >>> if valid:
        ...     print("Inputs are valid")
        ... else:
        ...     print(f"Validation failed: {msg}")
    """
    # Check video exists
    if not os.path.exists(video_path):
        return False, "Video file not found"
    
    # Check video is valid
    video_info = get_video_info(video_path)
    if not video_info:
        return False, "Invalid video file"
    
    # Check text is not empty
    if not text or len(text.strip()) == 0:
        return False, "Text cannot be empty"
    
    # Check text length
    if len(text) > 100:
        return False, "Text too long (max 100 characters)"
    
    return True, f"Valid - Video: {video_info['width']}x{video_info['height']}, Text: {len(text)} chars"


def preview_text_overlay(
    video_path: str,
    text: str
) -> Optional[Dict]:
    """
    Preview text overlay settings without processing
    
    Args:
        video_path: Video path
        text: Text to display
        
    Returns:
        Dict with preview information or None
    
    Example:
        >>> preview = preview_text_overlay('video.mp4', 'www.example.com')
        >>> print(f"Font size: {preview['font_size']}px")
        >>> print(f"Box size: {preview['box_width']}x{preview['box_height']}px")
    """
    processor = TextOverlayProcessor()
    return processor.preview_settings(video_path, text)