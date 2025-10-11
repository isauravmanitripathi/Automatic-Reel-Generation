"""
FFmpeg Helper - Utility functions for FFmpeg operations
Provides wrappers for common FFmpeg tasks
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import ffmpeg

import config


class FFmpegHelper:
    """Helper class for FFmpeg operations"""
    
    @staticmethod
    def check_installed() -> bool:
        """
        Check if FFmpeg is installed and accessible
        
        Returns:
            True if FFmpeg is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def get_version() -> Optional[str]:
        """
        Get FFmpeg version
        
        Returns:
            Version string or None
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse version from first line
                first_line = result.stdout.split('\n')[0]
                version = first_line.split(' ')[2] if len(first_line.split(' ')) > 2 else 'unknown'
                return version
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def probe_file(file_path: str) -> Optional[Dict]:
        """
        Probe media file using ffprobe
        
        Args:
            file_path: Path to media file
            
        Returns:
            Dict with file information or None
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            probe = ffmpeg.probe(file_path)
            return probe
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error probing file: {str(e)}")
            return None
    
    @staticmethod
    def get_video_info(video_path: str) -> Optional[Dict]:
        """
        Get detailed video information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dict with video info or None
        """
        try:
            probe = FFmpegHelper.probe_file(video_path)
            
            if not probe:
                return None
            
            # Find video stream
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            
            # Find audio stream
            audio_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                None
            )
            
            if not video_stream:
                return None
            
            # Extract video info
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            # Get fps
            fps_str = video_stream.get('r_frame_rate', '30/1')
            fps_parts = fps_str.split('/')
            fps = int(fps_parts[0]) / int(fps_parts[1]) if len(fps_parts) == 2 else 30.0
            
            # Get duration
            duration = float(probe['format'].get('duration', 0))
            
            # Get codecs
            video_codec = video_stream.get('codec_name', 'unknown')
            audio_codec = audio_stream.get('codec_name', 'none') if audio_stream else 'none'
            
            # Get bitrates
            video_bitrate = video_stream.get('bit_rate', '0')
            audio_bitrate = audio_stream.get('bit_rate', '0') if audio_stream else '0'
            
            # Get file size
            file_size = int(probe['format'].get('size', 0))
            
            return {
                'width': width,
                'height': height,
                'fps': fps,
                'duration': duration,
                'video_codec': video_codec,
                'audio_codec': audio_codec,
                'video_bitrate': video_bitrate,
                'audio_bitrate': audio_bitrate,
                'file_size': file_size,
                'aspect_ratio': width / height if height > 0 else 0,
                'has_audio': audio_stream is not None,
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting video info: {str(e)}")
            return None
    
    @staticmethod
    def get_audio_info(audio_path: str) -> Optional[Dict]:
        """
        Get detailed audio information
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with audio info or None
        """
        try:
            probe = FFmpegHelper.probe_file(audio_path)
            
            if not probe:
                return None
            
            # Find audio stream
            audio_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                None
            )
            
            if not audio_stream:
                return None
            
            # Extract audio info
            duration = float(probe['format'].get('duration', 0))
            codec = audio_stream.get('codec_name', 'unknown')
            bitrate = audio_stream.get('bit_rate', '0')
            sample_rate = int(audio_stream.get('sample_rate', 0))
            channels = int(audio_stream.get('channels', 0))
            
            return {
                'duration': duration,
                'codec': codec,
                'bitrate': bitrate,
                'sample_rate': sample_rate,
                'channels': channels,
                'file_size': int(probe['format'].get('size', 0)),
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting audio info: {str(e)}")
            return None
    
    @staticmethod
    def get_video_duration(video_path: str) -> float:
        """
        Get video duration in seconds
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds, 0.0 if error
        """
        try:
            info = FFmpegHelper.get_video_info(video_path)
            return info['duration'] if info else 0.0
        except Exception:
            return 0.0
    
    @staticmethod
    def get_audio_duration(audio_path: str) -> float:
        """
        Get audio duration in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, 0.0 if error
        """
        try:
            info = FFmpegHelper.get_audio_info(audio_path)
            return info['duration'] if info else 0.0
        except Exception:
            return 0.0
    
    @staticmethod
    def get_video_resolution(video_path: str) -> Optional[Tuple[int, int]]:
        """
        Get video resolution
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (width, height) or None
        """
        try:
            info = FFmpegHelper.get_video_info(video_path)
            return (info['width'], info['height']) if info else None
        except Exception:
            return None
    
    @staticmethod
    def get_video_fps(video_path: str) -> Optional[float]:
        """
        Get video FPS
        
        Args:
            video_path: Path to video file
            
        Returns:
            FPS value or None
        """
        try:
            info = FFmpegHelper.get_video_info(video_path)
            return info['fps'] if info else None
        except Exception:
            return None
    
    @staticmethod
    def get_video_codec(video_path: str) -> Optional[str]:
        """
        Get video codec
        
        Args:
            video_path: Path to video file
            
        Returns:
            Codec name or None
        """
        try:
            info = FFmpegHelper.get_video_info(video_path)
            return info['video_codec'] if info else None
        except Exception:
            return None
    
    @staticmethod
    def extract_audio_from_video(
        video_path: str,
        output_path: Optional[str] = None,
        audio_format: str = 'm4a'
    ) -> Optional[str]:
        """
        Extract audio track from video
        
        Args:
            video_path: Path to video file
            output_path: Output audio file path (optional)
            audio_format: Audio format (m4a, mp3, wav, etc.)
            
        Returns:
            Path to extracted audio or None
        """
        try:
            if not os.path.exists(video_path):
                return None
            
            # Generate output path if not provided
            if output_path is None:
                video_name = Path(video_path).stem
                output_path = str(config.TEMP_DIR / f"{video_name}_audio.{audio_format}")
            
            # Extract audio
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'copy' if audio_format == 'm4a' else config.AUDIO_CODEC,
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error extracting audio: {str(e)}")
            return None
    
    @staticmethod
    def convert_video_format(
        input_path: str,
        output_path: str,
        output_format: str = 'mp4',
        video_codec: str = None,
        audio_codec: str = None
    ) -> bool:
        """
        Convert video to different format
        
        Args:
            input_path: Input video path
            output_path: Output video path
            output_format: Output format (mp4, mov, avi, etc.)
            video_codec: Video codec (optional, uses config default)
            audio_codec: Audio codec (optional, uses config default)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(input_path):
                return False
            
            if video_codec is None:
                video_codec = config.VIDEO_CODEC
            
            if audio_codec is None:
                audio_codec = config.AUDIO_CODEC
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', video_codec,
                '-c:a', audio_codec,
                '-preset', config.VIDEO_PRESET,
                '-crf', str(config.VIDEO_CRF),
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0 and os.path.exists(output_path)
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error converting video: {str(e)}")
            return False
    
    @staticmethod
    def create_thumbnail(
        video_path: str,
        output_path: Optional[str] = None,
        time_offset: float = 1.0,
        width: int = 320
    ) -> Optional[str]:
        """
        Create thumbnail from video
        
        Args:
            video_path: Path to video file
            output_path: Output image path (optional)
            time_offset: Time offset in seconds for thumbnail
            width: Thumbnail width in pixels
            
        Returns:
            Path to thumbnail or None
        """
        try:
            if not os.path.exists(video_path):
                return None
            
            if output_path is None:
                video_name = Path(video_path).stem
                output_path = str(config.TEMP_DIR / f"{video_name}_thumb.jpg")
            
            cmd = [
                'ffmpeg',
                '-ss', str(time_offset),
                '-i', video_path,
                '-vframes', '1',
                '-vf', f'scale={width}:-1',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error creating thumbnail: {str(e)}")
            return None
    
    @staticmethod
    def has_audio_stream(video_path: str) -> bool:
        """
        Check if video has audio stream
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if video has audio, False otherwise
        """
        try:
            info = FFmpegHelper.get_video_info(video_path)
            return info['has_audio'] if info else False
        except Exception:
            return False
    
    @staticmethod
    def get_video_bitrate(video_path: str) -> Optional[str]:
        """
        Get video bitrate
        
        Args:
            video_path: Path to video file
            
        Returns:
            Bitrate string or None
        """
        try:
            info = FFmpegHelper.get_video_info(video_path)
            return info['video_bitrate'] if info else None
        except Exception:
            return None


# Module-level convenience functions
def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed"""
    return FFmpegHelper.check_installed()


def get_video_info(video_path: str) -> Optional[Dict]:
    """Get video information"""
    return FFmpegHelper.get_video_info(video_path)


def get_audio_info(audio_path: str) -> Optional[Dict]:
    """Get audio information"""
    return FFmpegHelper.get_audio_info(audio_path)


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds"""
    return FFmpegHelper.get_video_duration(video_path)


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds"""
    return FFmpegHelper.get_audio_duration(audio_path)


def extract_audio_from_video(video_path: str, output_path: Optional[str] = None) -> Optional[str]:
    """Extract audio from video"""
    return FFmpegHelper.extract_audio_from_video(video_path, output_path)


def get_video_resolution(video_path: str) -> Optional[Tuple[int, int]]:
    """Get video resolution"""
    return FFmpegHelper.get_video_resolution(video_path)


def get_video_fps(video_path: str) -> Optional[float]:
    """Get video FPS"""
    return FFmpegHelper.get_video_fps(video_path)


def get_video_codec(video_path: str) -> Optional[str]:
    """Get video codec"""
    return FFmpegHelper.get_video_codec(video_path)


def convert_video_format(input_path: str, output_path: str, output_format: str = 'mp4') -> bool:
    """Convert video format"""
    return FFmpegHelper.convert_video_format(input_path, output_path, output_format)