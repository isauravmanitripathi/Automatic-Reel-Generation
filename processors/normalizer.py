"""
Video Normalizer - Normalize videos to consistent format
Handles fps, codec, resolution, bitrate normalization and cropping
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import ffmpeg

import config


class VideoNormalizer:
    """Handler for video normalization using FFmpeg"""
    
    def __init__(self):
        """Initialize video normalizer"""
        self.temp_dir = config.NORMALIZED_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def normalize(
        self,
        video_path: str,
        target_resolution: Tuple[int, int] = (1080, 1920),
        target_fps: int = 30,
        target_codec: str = 'libx264',
        target_bitrate: str = '5M',
        crop_mode: str = 'center',
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Normalize video to target specifications
        
        Args:
            video_path: Input video path
            target_resolution: Target (width, height)
            target_fps: Target frames per second
            target_codec: Target video codec
            target_bitrate: Target video bitrate
            crop_mode: How to handle aspect ratio ('center', 'fit', 'stretch')
            output_path: Custom output path (optional)
            
        Returns:
            Path to normalized video or None if failed
        """
        try:
            if not os.path.exists(video_path):
                if config.DEBUG:
                    print(f"Video file not found: {video_path}")
                return None
            
            # Get input video info
            video_info = self._get_video_info(video_path)
            if not video_info:
                return None
            
            # Determine output path
            if output_path is None:
                input_name = Path(video_path).stem
                output_path = str(self.temp_dir / f"{input_name}_normalized.mp4")
            
            # Build FFmpeg filter chain
            filter_chain = self._build_filter_chain(
                video_info,
                target_resolution,
                target_fps,
                crop_mode
            )
            
            # Build FFmpeg command
            success = self._run_ffmpeg_normalize(
                video_path,
                output_path,
                filter_chain,
                target_codec,
                target_bitrate
            )
            
            if success and os.path.exists(output_path):
                return output_path
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error normalizing video: {str(e)}")
            return None
    
    def _get_video_info(self, video_path: str) -> Optional[Dict]:
        """
        Get video information using ffprobe
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dict with video info or None
        """
        try:
            probe = ffmpeg.probe(video_path)
            
            # Find video stream
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                return None
            
            # Extract info
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            
            # Get fps
            fps_str = video_stream.get('r_frame_rate', '30/1')
            fps_parts = fps_str.split('/')
            fps = int(fps_parts[0]) / int(fps_parts[1]) if len(fps_parts) == 2 else 30
            
            # Get duration
            duration = float(probe['format'].get('duration', 0))
            
            # Get codec
            codec = video_stream.get('codec_name', 'unknown')
            
            # Get bitrate
            bitrate = probe['format'].get('bit_rate', '0')
            
            return {
                'width': width,
                'height': height,
                'fps': fps,
                'duration': duration,
                'codec': codec,
                'bitrate': bitrate,
                'aspect_ratio': width / height if height > 0 else 16/9,
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting video info: {str(e)}")
            return None
    
    def _build_filter_chain(
        self,
        video_info: Dict,
        target_resolution: Tuple[int, int],
        target_fps: int,
        crop_mode: str
    ) -> str:
        """
        Build FFmpeg filter chain for normalization
        
        Args:
            video_info: Input video information
            target_resolution: Target (width, height)
            target_fps: Target fps
            crop_mode: Cropping mode
            
        Returns:
            FFmpeg filter string
        """
        filters = []
        
        target_width, target_height = target_resolution
        input_width = video_info['width']
        input_height = video_info['height']
        
        target_aspect = target_width / target_height
        input_aspect = input_width / input_height
        
        # Handle resolution and aspect ratio
        if crop_mode == 'center':
            # Crop to target aspect ratio, then scale
            if input_aspect > target_aspect:
                # Input is wider - crop width
                crop_width = int(input_height * target_aspect)
                crop_height = input_height
                crop_x = (input_width - crop_width) // 2
                crop_y = 0
            else:
                # Input is taller - crop height
                crop_width = input_width
                crop_height = int(input_width / target_aspect)
                crop_x = 0
                crop_y = (input_height - crop_height) // 2
            
            # Add crop filter
            filters.append(f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}")
            
            # Add scale filter
            filters.append(f"scale={target_width}:{target_height}")
        
        elif crop_mode == 'fit':
            # Scale to fit within target resolution (may have black bars)
            filters.append(
                f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
                f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
            )
        
        elif crop_mode == 'stretch':
            # Just scale (ignore aspect ratio)
            filters.append(f"scale={target_width}:{target_height}")
        
        # Add fps filter if needed
        if abs(video_info['fps'] - target_fps) > 0.1:
            filters.append(f"fps={target_fps}")
        
        # Optional: Add quality enhancement filters
        # Denoise slightly
        # filters.append("hqdn3d=1.5:1.5:6:6")
        
        return ','.join(filters)
    
    def _run_ffmpeg_normalize(
        self,
        input_path: str,
        output_path: str,
        filter_chain: str,
        codec: str,
        bitrate: str
    ) -> bool:
        """
        Run FFmpeg normalization command
        
        Args:
            input_path: Input video path
            output_path: Output video path
            filter_chain: FFmpeg filter string
            codec: Video codec
            bitrate: Video bitrate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build FFmpeg command using ffmpeg-python
            stream = ffmpeg.input(input_path)
            
            # Apply video filters
            stream = ffmpeg.filter(stream, 'scale', filter_chain) if not filter_chain else stream
            
            # If we have a complex filter chain, use it directly
            if filter_chain:
                stream = stream.filter('null')  # Placeholder, we'll use -vf directly
            
            # Output with settings
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec=codec,
                video_bitrate=bitrate,
                acodec=config.AUDIO_CODEC,
                audio_bitrate=config.AUDIO_BITRATE,
                preset=config.VIDEO_PRESET,
                crf=config.VIDEO_CRF,
                movflags='faststart',
                **{'threads': config.FFMPEG_THREADS}
            )
            
            # Run with filter chain if provided
            if filter_chain:
                # Use subprocess for complex filters
                cmd = [
                    'ffmpeg',
                    '-i', input_path,
                    '-vf', filter_chain,
                    '-c:v', codec,
                    '-b:v', bitrate,
                    '-c:a', config.AUDIO_CODEC,
                    '-b:a', config.AUDIO_BITRATE,
                    '-preset', config.VIDEO_PRESET,
                    '-crf', str(config.VIDEO_CRF),
                    '-movflags', 'faststart',
                    '-threads', str(config.FFMPEG_THREADS),
                    '-y',  # Overwrite output
                    output_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                
                return result.returncode == 0
            else:
                # Use ffmpeg-python
                ffmpeg.run(stream, overwrite_output=True, quiet=not config.VERBOSE)
                return True
        
        except Exception as e:
            if config.DEBUG:
                print(f"FFmpeg error: {str(e)}")
            return False
    
    def get_video_stats(self, video_path: str) -> Optional[Dict]:
        """
        Get detailed video statistics
        
        Args:
            video_path: Path to video
            
        Returns:
            Dict with video stats
        """
        return self._get_video_info(video_path)
    
    def needs_normalization(
        self,
        video_path: str,
        target_resolution: Tuple[int, int] = (1080, 1920),
        target_fps: int = 30
    ) -> bool:
        """
        Check if video needs normalization
        
        Args:
            video_path: Path to video
            target_resolution: Target resolution
            target_fps: Target fps
            
        Returns:
            True if normalization needed
        """
        info = self._get_video_info(video_path)
        
        if not info:
            return True
        
        # Check resolution
        if info['width'] != target_resolution[0] or info['height'] != target_resolution[1]:
            return True
        
        # Check fps (with tolerance)
        if abs(info['fps'] - target_fps) > 1:
            return True
        
        # Check codec
        if info['codec'] != 'h264':
            return True
        
        return False


def normalize_video(
    video_path: str,
    target_resolution: Tuple[int, int] = None,
    target_fps: int = None,
    crop_mode: str = 'center',
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Main function to normalize a video
    
    Args:
        video_path: Input video path
        target_resolution: Target (width, height) - defaults to reels size
        target_fps: Target fps - defaults to 30
        crop_mode: How to handle aspect ratio ('center', 'fit', 'stretch')
        output_path: Custom output path
        
    Returns:
        Path to normalized video or None if failed
    """
    if target_resolution is None:
        target_resolution = config.RESOLUTIONS['reels']
    
    if target_fps is None:
        target_fps = config.TARGET_FPS
    
    normalizer = VideoNormalizer()
    
    return normalizer.normalize(
        video_path=video_path,
        target_resolution=target_resolution,
        target_fps=target_fps,
        target_codec=config.VIDEO_CODEC,
        target_bitrate=config.TARGET_BITRATE,
        crop_mode=crop_mode,
        output_path=output_path
    )


def batch_normalize(
    video_paths: List[str],
    target_resolution: Tuple[int, int] = None,
    target_fps: int = None,
    crop_mode: str = 'center'
) -> List[str]:
    """
    Normalize multiple videos
    
    Args:
        video_paths: List of video paths
        target_resolution: Target resolution
        target_fps: Target fps
        crop_mode: Cropping mode
        
    Returns:
        List of normalized video paths
    """
    if target_resolution is None:
        target_resolution = config.RESOLUTIONS['reels']
    
    if target_fps is None:
        target_fps = config.TARGET_FPS
    
    normalizer = VideoNormalizer()
    normalized_videos = []
    
    for video_path in video_paths:
        normalized = normalizer.normalize(
            video_path=video_path,
            target_resolution=target_resolution,
            target_fps=target_fps,
            crop_mode=crop_mode
        )
        
        if normalized:
            normalized_videos.append(normalized)
    
    return normalized_videos


def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed
    
    Returns:
        True if installed, False otherwise
    """
    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False