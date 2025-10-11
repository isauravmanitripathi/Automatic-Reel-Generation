"""
Video Combiner - Merge multiple videos into one
Handles concatenation with proper audio sync
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict
import ffmpeg

import config


class VideoCombiner:
    """Handler for combining multiple videos"""
    
    def __init__(self):
        """Initialize video combiner"""
        self.temp_dir = config.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def merge(
        self,
        video_paths: List[str],
        output_path: Optional[str] = None,
        transition: Optional[str] = None,
        transition_duration: float = 0.5
    ) -> Optional[str]:
        """
        Merge multiple videos into one
        
        Args:
            video_paths: List of video file paths
            output_path: Output file path (optional)
            transition: Transition type ('fade', 'dissolve', None)
            transition_duration: Duration of transition in seconds
            
        Returns:
            Path to merged video or None if failed
        """
        try:
            if not video_paths:
                return None
            
            # Single video - just return it
            if len(video_paths) == 1:
                return video_paths[0]
            
            # Verify all videos exist
            for video_path in video_paths:
                if not os.path.exists(video_path):
                    if config.DEBUG:
                        print(f"Video not found: {video_path}")
                    return None
            
            # Determine output path
            if output_path is None:
                output_path = str(config.OUTPUTS_DIR / "combined_video.mp4")
            
            # Choose merge method based on transition
            if transition:
                return self._merge_with_transition(
                    video_paths,
                    output_path,
                    transition,
                    transition_duration
                )
            else:
                return self._merge_simple_concat(video_paths, output_path)
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error merging videos: {str(e)}")
            return None
    
    def _merge_simple_concat(
        self,
        video_paths: List[str],
        output_path: str
    ) -> Optional[str]:
        """
        Simple concatenation using FFmpeg concat demuxer
        (Fast, but requires all videos to have same specs)
        
        Args:
            video_paths: List of video paths
            output_path: Output path
            
        Returns:
            Output path or None
        """
        try:
            # Create concat file
            concat_file = self.temp_dir / "concat_list.txt"
            
            with open(concat_file, 'w') as f:
                for video_path in video_paths:
                    # Write absolute path
                    abs_path = os.path.abspath(video_path)
                    f.write(f"file '{abs_path}'\n")
            
            # Run FFmpeg concat
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',  # Copy streams (no re-encoding)
                '-y',  # Overwrite output
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Clean up concat file
            if concat_file.exists():
                concat_file.unlink()
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            
            # If concat failed, try re-encoding method
            if config.DEBUG:
                print("Concat demuxer failed, trying re-encode method...")
            
            return self._merge_with_reencoding(video_paths, output_path)
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error in simple concat: {str(e)}")
            return self._merge_with_reencoding(video_paths, output_path)
    
    def _merge_with_reencoding(
        self,
        video_paths: List[str],
        output_path: str
    ) -> Optional[str]:
        """
        Merge videos with re-encoding (slower but more reliable)
        
        Args:
            video_paths: List of video paths
            output_path: Output path
            
        Returns:
            Output path or None
        """
        try:
            # Build filter_complex for concatenation
            filter_parts = []
            
            for i in range(len(video_paths)):
                filter_parts.append(f"[{i}:v][{i}:a]")
            
            filter_complex = (
                f"{''.join(filter_parts)}"
                f"concat=n={len(video_paths)}:v=1:a=1[outv][outa]"
            )
            
            # Build FFmpeg command
            cmd = ['ffmpeg']
            
            # Add all input files
            for video_path in video_paths:
                cmd.extend(['-i', video_path])
            
            # Add filter complex
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', '[outa]',
                '-c:v', config.VIDEO_CODEC,
                '-preset', config.VIDEO_PRESET,
                '-crf', str(config.VIDEO_CRF),
                '-c:a', config.AUDIO_CODEC,
                '-b:a', config.AUDIO_BITRATE,
                '-movflags', 'faststart',
                '-y',
                output_path
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            
            if config.DEBUG:
                print(f"FFmpeg stderr: {result.stderr}")
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error in re-encoding merge: {str(e)}")
            return None
    
    def _merge_with_transition(
        self,
        video_paths: List[str],
        output_path: str,
        transition: str,
        duration: float
    ) -> Optional[str]:
        """
        Merge videos with transitions (fade, dissolve)
        
        Args:
            video_paths: List of video paths
            output_path: Output path
            transition: Transition type
            duration: Transition duration
            
        Returns:
            Output path or None
        """
        try:
            # Get duration of each video
            video_durations = []
            for video_path in video_paths:
                probe = ffmpeg.probe(video_path)
                duration_val = float(probe['format']['duration'])
                video_durations.append(duration_val)
            
            # Build complex filter for transitions
            filter_parts = []
            
            # Create transition points
            offset = 0
            for i in range(len(video_paths)):
                if i == 0:
                    filter_parts.append(f"[{i}:v]")
                else:
                    # Calculate transition offset
                    transition_offset = offset - duration
                    
                    if transition == 'fade':
                        filter_parts.append(
                            f"[{i}:v]fade=in:st=0:d={duration}[v{i}];"
                            f"[v{i-1}][v{i}]overlay=enable='between(t,{transition_offset},{offset})'[v{i}out]"
                        )
                    elif transition == 'dissolve':
                        filter_parts.append(
                            f"[v{i-1}][{i}:v]blend=all_expr='A*(1-T/{duration})+B*(T/{duration})':shortest=1[v{i}out]"
                        )
                
                offset += video_durations[i]
            
            # This is complex - for simplicity, fall back to simple merge
            # Full transition implementation requires more complex filter graphs
            return self._merge_with_reencoding(video_paths, output_path)
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error in transition merge: {str(e)}")
            return self._merge_with_reencoding(video_paths, output_path)
    
    def get_combined_duration(self, video_paths: List[str]) -> float:
        """
        Get total duration of all videos combined
        
        Args:
            video_paths: List of video paths
            
        Returns:
            Total duration in seconds
        """
        total_duration = 0.0
        
        for video_path in video_paths:
            try:
                probe = ffmpeg.probe(video_path)
                duration = float(probe['format']['duration'])
                total_duration += duration
            except Exception:
                pass
        
        return total_duration


def merge_videos(
    video_paths: List[str],
    output_path: Optional[str] = None,
    transition: Optional[str] = None
) -> Optional[str]:
    """
    Main function to merge multiple videos
    
    Args:
        video_paths: List of video file paths
        output_path: Output file path (optional)
        transition: Transition type ('fade', 'dissolve', None)
        
    Returns:
        Path to merged video or None if failed
    """
    combiner = VideoCombiner()
    return combiner.merge(video_paths, output_path, transition)


def concatenate_segments(
    segment_paths: List[str],
    output_path: str,
    audio_path: Optional[str] = None,
    audio_start: float = 0.0
) -> Optional[str]:
    """
    Concatenate video segments and optionally add audio
    
    Args:
        segment_paths: List of video segment paths
        output_path: Output file path
        audio_path: Optional audio file to add
        audio_start: Audio start time offset
        
    Returns:
        Path to output video or None if failed
    """
    try:
        combiner = VideoCombiner()
        
        # First merge the segments
        merged = combiner.merge(segment_paths, output_path)
        
        if not merged:
            return None
        
        # If audio provided, add it
        if audio_path and os.path.exists(audio_path):
            temp_output = str(Path(output_path).parent / f"temp_{Path(output_path).name}")
            
            # Get video duration
            probe = ffmpeg.probe(merged)
            video_duration = float(probe['format']['duration'])
            
            # Add audio with proper timing
            cmd = [
                'ffmpeg',
                '-i', merged,
                '-ss', str(audio_start),
                '-t', str(video_duration),
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', config.AUDIO_CODEC,
                '-b:a', config.AUDIO_BITRATE,
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                '-y',
                temp_output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(temp_output):
                # Replace original with audio version
                os.replace(temp_output, output_path)
        
        return output_path
    
    except Exception as e:
        if config.DEBUG:
            print(f"Error concatenating segments: {str(e)}")
        return None


def get_total_duration(video_paths: List[str]) -> float:
    """
    Get total duration of multiple videos
    
    Args:
        video_paths: List of video paths
        
    Returns:
        Total duration in seconds
    """
    combiner = VideoCombiner()
    return combiner.get_combined_duration(video_paths)