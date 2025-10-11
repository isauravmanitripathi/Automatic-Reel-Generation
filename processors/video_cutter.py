"""
Video Cutter - Extract segments and merge with audio
Handles video cutting at specified timestamps
"""

import os
import random
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import ffmpeg

import config


class VideoCutter:
    """Handler for cutting videos into segments"""
    
    def __init__(self):
        """Initialize video cutter"""
        self.temp_dir = config.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_segment(
        self,
        video_path: str,
        start_time: float,
        duration: float,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract a segment from video
        
        Args:
            video_path: Input video path
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Output path (optional)
            
        Returns:
            Path to extracted segment or None
        """
        try:
            if not os.path.exists(video_path):
                return None
            
            # Generate output path if not provided
            if output_path is None:
                output_path = str(
                    self.temp_dir / f"segment_{start_time:.2f}_{duration:.2f}.mp4"
                )
            
            # Extract segment using FFmpeg
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', video_path,
                '-t', str(duration),
                '-c:v', config.VIDEO_CODEC,
                '-preset', 'ultrafast',  # Fast for segments
                '-crf', str(config.VIDEO_CRF),
                '-c:a', config.AUDIO_CODEC,
                '-b:a', config.AUDIO_BITRATE,
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error extracting segment: {str(e)}")
            return None
    
    def create_segments_from_timestamps(
        self,
        video_path: str,
        timestamps: List[float],
        audio_duration: float,
        order: str = 'sequential'
    ) -> List[str]:
        """
        Create video segments based on timestamps
        
        Args:
            video_path: Input video path
            timestamps: List of cut points in seconds
            audio_duration: Total audio duration to match
            order: 'sequential' or 'random'
            
        Returns:
            List of segment file paths
        """
        try:
            # Get video info
            probe = ffmpeg.probe(video_path)
            video_duration = float(probe['format']['duration'])
            
            # Calculate segment durations based on timestamps
            segment_durations = []
            for i in range(len(timestamps) - 1):
                duration = timestamps[i + 1] - timestamps[i]
                if duration > config.MIN_SEGMENT_DURATION:
                    segment_durations.append(duration)
            
            # If not enough segments, add remaining time
            if segment_durations:
                total_segments_duration = sum(segment_durations)
                if total_segments_duration < audio_duration:
                    # Add one more segment
                    remaining = audio_duration - total_segments_duration
                    if remaining > config.MIN_SEGMENT_DURATION:
                        segment_durations.append(remaining)
            else:
                # No valid segments, use entire video
                segment_durations = [min(audio_duration, video_duration)]
            
            # Generate segments
            segments = []
            current_video_time = 0.0
            
            for i, seg_duration in enumerate(segment_durations):
                # Ensure we don't exceed video duration
                if current_video_time + seg_duration > video_duration:
                    # Loop back to start
                    current_video_time = 0.0
                
                # Extract segment
                segment_path = self.extract_segment(
                    video_path,
                    current_video_time,
                    seg_duration,
                    output_path=str(self.temp_dir / f"segment_{i:04d}.mp4")
                )
                
                if segment_path:
                    segments.append(segment_path)
                
                # Move to next position
                if order == 'sequential':
                    current_video_time += seg_duration
                else:  # random
                    # Pick random position in video
                    max_start = max(0, video_duration - seg_duration)
                    current_video_time = random.uniform(0, max_start)
            
            return segments
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error creating segments: {str(e)}")
            return []
    
    def merge_segments_with_audio(
        self,
        segment_paths: List[str],
        audio_path: str,
        audio_start: float,
        audio_end: float,
        output_path: str
    ) -> Optional[str]:
        """
        Merge video segments and overlay audio
        
        Args:
            segment_paths: List of video segment paths
            audio_path: Path to audio file
            audio_start: Audio start time
            audio_end: Audio end time
            output_path: Output file path
            
        Returns:
            Path to output video or None
        """
        try:
            if not segment_paths:
                return None
            
            # Create concat file
            concat_file = self.temp_dir / "segments_concat.txt"
            
            with open(concat_file, 'w') as f:
                for segment_path in segment_paths:
                    abs_path = os.path.abspath(segment_path)
                    f.write(f"file '{abs_path}'\n")
            
            # First, concatenate video segments without audio
            temp_video = str(self.temp_dir / "temp_concat.mp4")
            
            cmd_concat = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y',
                temp_video
            ]
            
            result = subprocess.run(cmd_concat, capture_output=True, text=True)
            
            if result.returncode != 0 or not os.path.exists(temp_video):
                # Try with re-encoding
                cmd_concat = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', str(concat_file),
                    '-c:v', config.VIDEO_CODEC,
                    '-preset', config.VIDEO_PRESET,
                    '-crf', str(config.VIDEO_CRF),
                    '-y',
                    temp_video
                ]
                
                result = subprocess.run(cmd_concat, capture_output=True, text=True)
                
                if result.returncode != 0:
                    return None
            
            # Now add audio
            audio_duration = audio_end - audio_start
            
            cmd_audio = [
                'ffmpeg',
                '-i', temp_video,
                '-ss', str(audio_start),
                '-t', str(audio_duration),
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', config.AUDIO_CODEC,
                '-b:a', config.AUDIO_BITRATE,
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                '-movflags', 'faststart',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd_audio, capture_output=True, text=True)
            
            # Cleanup
            if concat_file.exists():
                concat_file.unlink()
            if os.path.exists(temp_video):
                os.unlink(temp_video)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error merging segments with audio: {str(e)}")
            return None
    
    def cleanup_segments(self, segment_paths: List[str]) -> None:
        """
        Clean up temporary segment files
        
        Args:
            segment_paths: List of segment paths to delete
        """
        for segment_path in segment_paths:
            try:
                if os.path.exists(segment_path):
                    os.unlink(segment_path)
            except Exception as e:
                if config.DEBUG:
                    print(f"Could not delete {segment_path}: {str(e)}")


def create_segments(
    video_path: str,
    cut_points: List[float],
    order: str,
    audio_duration: float
) -> List[str]:
    """
    Create video segments from cut points
    
    Args:
        video_path: Input video path
        cut_points: List of timestamps to cut at
        order: 'sequential' or 'random'
        audio_duration: Target audio duration
        
    Returns:
        List of segment file paths
    """
    cutter = VideoCutter()
    return cutter.create_segments_from_timestamps(
        video_path,
        cut_points,
        audio_duration,
        order
    )


def merge_with_audio(
    segments: List[str],
    audio_path: str,
    audio_start: float,
    audio_end: float,
    output_path: str
) -> Optional[str]:
    """
    Merge segments with audio track
    
    Args:
        segments: List of video segment paths
        audio_path: Path to audio file
        audio_start: Audio start time in seconds
        audio_end: Audio end time in seconds
        output_path: Output file path
        
    Returns:
        Path to final video or None
    """
    cutter = VideoCutter()
    return cutter.merge_segments_with_audio(
        segments,
        audio_path,
        audio_start,
        audio_end,
        output_path
    )


def extract_segment(
    video_path: str,
    start_time: float,
    duration: float,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Extract single segment from video
    
    Args:
        video_path: Input video path
        start_time: Start time in seconds
        duration: Duration in seconds
        output_path: Output path (optional)
        
    Returns:
        Path to extracted segment or None
    """
    cutter = VideoCutter()
    return cutter.extract_segment(video_path, start_time, duration, output_path)


def cleanup_temp_segments(segment_paths: List[str]) -> None:
    """
    Clean up temporary segment files
    
    Args:
        segment_paths: List of segment paths to delete
    """
    cutter = VideoCutter()
    cutter.cleanup_segments(segment_paths)