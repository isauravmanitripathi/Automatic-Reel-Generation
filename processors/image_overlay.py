"""
Image Overlay Processor - COMPLETE FIX
Overlay images on video with animations
Uses position animations + enable expressions (no fade filters to avoid timing conflicts)
"""

import os
import random
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import ffmpeg

import config
from utils.ffmpeg_helper import get_video_info, get_video_duration, get_video_resolution
from utils.file_manager import FileManager


class ImageOverlayProcessor:
    """Handler for overlaying images on video with animations"""
    
    def __init__(self):
        """Initialize image overlay processor"""
        self.temp_dir = config.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.file_manager = FileManager()
    
    def process(
        self,
        video_path: str,
        images_folder: str,
        output_path: str,
        duration_per_image: Optional[float] = None,
        delay_between_images: float = 0.0,
        animation_style: str = 'random',
        animation_duration: float = None
    ) -> Optional[str]:
        """
        Overlay images from folder onto video with animations
        
        Args:
            video_path: Path to background video
            images_folder: Folder containing images
            output_path: Output video path
            duration_per_image: How long each image shows (auto-calculate if None)
            delay_between_images: Gap between images in seconds
            animation_style: Animation type ('slide_bottom', 'slide_left', 'slide_right', 
                           'slide_top', 'fade', 'random')
            animation_duration: Duration of animation in seconds (uses config default if None)
            
        Returns:
            Path to output video or None if failed
        """
        try:
            # Validate inputs
            if not os.path.exists(video_path):
                if config.DEBUG:
                    print(f"Video not found: {video_path}")
                return None
            
            if not os.path.exists(images_folder):
                if config.DEBUG:
                    print(f"Images folder not found: {images_folder}")
                return None
            
            # Load images from folder
            image_paths = self._load_images_from_folder(images_folder)
            
            if not image_paths:
                if config.DEBUG:
                    print("No images found in folder")
                return None
            
            # Get video info
            video_info = get_video_info(video_path)
            if not video_info:
                if config.DEBUG:
                    print("Could not read video info")
                return None
            
            video_duration = video_info['duration']
            video_width = video_info['width']
            video_height = video_info['height']
            
            # Calculate timing
            timing_info = self._calculate_timing(
                num_images=len(image_paths),
                video_duration=video_duration,
                duration_per_image=duration_per_image,
                delay_between_images=delay_between_images
            )
            
            if not timing_info:
                return None
            
            # Use animation duration from config if not provided
            if animation_duration is None:
                animation_duration = config.IMAGE_ANIMATION_DURATION
            
            # Build FFmpeg filter complex
            filter_complex = self._build_filter_complex(
                image_paths=image_paths,
                video_width=video_width,
                video_height=video_height,
                timing_info=timing_info,
                animation_style=animation_style,
                animation_duration=animation_duration
            )
            
            if config.VERBOSE or config.DEBUG:
                print(f"\n=== FILTER COMPLEX ===")
                print(filter_complex)
                print(f"======================\n")
            
            # Execute FFmpeg command
            success = self._execute_ffmpeg(
                video_path=video_path,
                image_paths=image_paths,
                filter_complex=filter_complex,
                output_path=output_path
            )
            
            if success and os.path.exists(output_path):
                return output_path
            
            return None
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error in image overlay process: {str(e)}")
                import traceback
                traceback.print_exc()
            return None
    
    def _load_images_from_folder(self, folder_path: str) -> List[str]:
        """
        Load all valid images from folder (sorted alphabetically)
        
        Args:
            folder_path: Path to folder containing images
            
        Returns:
            List of image file paths
        """
        image_paths = []
        
        try:
            folder = Path(folder_path)
            
            # Get all files
            for item in sorted(folder.iterdir()):
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in config.IMAGE_EXTENSIONS:
                        image_paths.append(str(item))
            
            if config.VERBOSE:
                print(f"Found {len(image_paths)} images in folder")
            
            return image_paths
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error loading images: {str(e)}")
            return []
    
    def _calculate_timing(
        self,
        num_images: int,
        video_duration: float,
        duration_per_image: Optional[float],
        delay_between_images: float
    ) -> Optional[Dict]:
        """
        Calculate timing for each image
        
        Args:
            num_images: Number of images
            video_duration: Total video duration
            duration_per_image: Duration each image shows (None for auto)
            delay_between_images: Gap between images
            
        Returns:
            Dict with timing info or None if invalid
        """
        try:
            # Auto-calculate duration if not provided
            if duration_per_image is None:
                # Calculate based on video duration and number of images
                # Account for delays AFTER each image (except the last one)
                total_delay_time = delay_between_images * (num_images - 1) if num_images > 1 else 0
                available_time = video_duration - total_delay_time
                
                if available_time <= 0:
                    if config.VERBOSE:
                        print("Video too short for delays, removing delays")
                    # Fallback: no delays, just fit images
                    delay_between_images = 0
                    available_time = video_duration
                
                duration_per_image = available_time / num_images
                
                # Ensure minimum duration
                if duration_per_image < 1.0:
                    duration_per_image = 1.0
                    if config.VERBOSE:
                        print(f"Warning: Setting minimum duration of 1.0s per image")
            
            # Calculate start and end times for each image
            start_times = []
            end_times = []
            current_time = 0.0
            
            for i in range(num_images):
                start_times.append(current_time)
                current_time += duration_per_image
                end_times.append(current_time)
                
                # Add delay after each image except the last one
                if i < num_images - 1:
                    current_time += delay_between_images
            
            # Check if we exceed video duration
            total_time = end_times[-1]
            
            if total_time > video_duration:
                # Scale everything down proportionally
                scale_factor = video_duration / total_time
                
                if config.VERBOSE:
                    print(f"Timeline exceeds video duration, scaling by {scale_factor:.3f}")
                
                start_times = [t * scale_factor for t in start_times]
                end_times = [t * scale_factor for t in end_times]
                duration_per_image = duration_per_image * scale_factor
                total_time = video_duration
            
            if config.VERBOSE:
                print(f"\n=== TIMING INFO ===")
                print(f"Number of images: {num_images}")
                print(f"Duration per image: {duration_per_image:.2f}s")
                print(f"Delay between images: {delay_between_images:.2f}s")
                print(f"Total timeline: {total_time:.2f}s")
                for i in range(num_images):
                    print(f"  Image {i+1}: {start_times[i]:.2f}s - {end_times[i]:.2f}s")
                print(f"===================\n")
            
            return {
                'duration_per_image': duration_per_image,
                'start_times': start_times,
                'end_times': end_times,
                'num_images': num_images,
                'total_duration': total_time,
                'delay_between_images': delay_between_images,
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error calculating timing: {str(e)}")
            return None
    
    def _calculate_image_dimensions(
        self,
        image_path: str,
        video_width: int,
        video_height: int
    ) -> Tuple[int, int]:
        """
        Calculate target dimensions for image (resize only if exceeds 85% of frame)
        Maintains aspect ratio and adds 15% padding from edges
        
        Args:
            image_path: Path to image
            video_width: Video width
            video_height: Video height
            
        Returns:
            Tuple of (target_width, target_height)
        """
        try:
            # Get image dimensions using ffprobe
            probe = ffmpeg.probe(image_path)
            
            # Find video stream (images are treated as video by ffprobe)
            img_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            
            if not img_stream:
                # Fallback to max allowed size
                max_width = int(video_width * config.IMAGE_MAX_SIZE_RATIO)
                max_height = int(video_height * config.IMAGE_MAX_SIZE_RATIO)
                return max_width, max_height
            
            img_width = int(img_stream['width'])
            img_height = int(img_stream['height'])
            
            # Calculate max allowed dimensions (85% of frame)
            max_width = int(video_width * config.IMAGE_MAX_SIZE_RATIO)
            max_height = int(video_height * config.IMAGE_MAX_SIZE_RATIO)
            
            # Check if image exceeds max dimensions
            if img_width <= max_width and img_height <= max_height:
                # Image fits within bounds - no resize needed
                return img_width, img_height
            
            # Image is too large - resize maintaining aspect ratio
            img_aspect = img_width / img_height
            max_aspect = max_width / max_height
            
            if img_aspect > max_aspect:
                # Image is wider - fit to max width
                target_width = max_width
                target_height = int(max_width / img_aspect)
            else:
                # Image is taller - fit to max height
                target_height = max_height
                target_width = int(max_height * img_aspect)
            
            # Ensure dimensions are even (required by some codecs)
            target_width = target_width - (target_width % 2)
            target_height = target_height - (target_height % 2)
            
            return target_width, target_height
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error calculating dimensions for {image_path}: {str(e)}")
            
            # Fallback
            max_width = int(video_width * config.IMAGE_MAX_SIZE_RATIO)
            max_height = int(video_height * config.IMAGE_MAX_SIZE_RATIO)
            return max_width, max_height
    
    def _build_filter_complex(
        self,
        image_paths: List[str],
        video_width: int,
        video_height: int,
        timing_info: Dict,
        animation_style: str,
        animation_duration: float
    ) -> str:
        """
        Build FFmpeg filter_complex for all image overlays
        Uses ONLY position animations and enable expressions (no fade filters)
        
        Args:
            image_paths: List of image paths
            video_width: Video width
            video_height: Video height
            timing_info: Timing information dict
            animation_style: Animation style
            animation_duration: Animation duration
            
        Returns:
            filter_complex string
        """
        filters = []
        
        start_times = timing_info['start_times']
        end_times = timing_info['end_times']
        
        # STEP 1: Scale and prepare all images
        for i, img_path in enumerate(image_paths):
            # Calculate dimensions
            img_width, img_height = self._calculate_image_dimensions(
                img_path,
                video_width,
                video_height
            )
            
            # Scale and add alpha channel for transparency support
            # format=yuva420p adds alpha channel
            scale_filter = (
                f"[{i + 1}:v]"
                f"scale={img_width}:{img_height}:force_original_aspect_ratio=decrease,"
                f"format=yuva420p"
                f"[img{i}]"
            )
            filters.append(scale_filter)
        
        # STEP 2: Build overlay chain with position-based animations
        current_layer = "[0:v]"
        
        for i, img_path in enumerate(image_paths):
            img_width, img_height = self._calculate_image_dimensions(
                img_path,
                video_width,
                video_height
            )
            
            start_time = start_times[i]
            end_time = end_times[i]
            actual_duration = end_time - start_time
            
            # Calculate center position
            center_x = (video_width - img_width) // 2
            center_y = (video_height - img_height) // 2
            
            # Choose animation style for this image
            current_animation = animation_style
            if animation_style == 'random':
                current_animation = random.choice([
                    'slide_bottom', 'slide_left', 'slide_right', 'slide_top', 'fade'
                ])
            
            # Animation timing
            anim_duration = min(animation_duration, actual_duration * 0.25)  # Max 25% of duration
            exit_start_time = end_time - anim_duration
            
            # Build position expressions based on animation type
            x_expr, y_expr = self._build_animation_expressions(
                animation_type=current_animation,
                video_width=video_width,
                video_height=video_height,
                img_width=img_width,
                img_height=img_height,
                center_x=center_x,
                center_y=center_y,
                start_time=start_time,
                end_time=end_time,
                anim_duration=anim_duration,
                exit_start_time=exit_start_time
            )
            
            # Enable expression - show image only during its time window
            enable_expr = f"between(t,{start_time},{end_time})"
            
            # Create overlay
            if i == len(image_paths) - 1:
                # Last overlay - output to final
                overlay_cmd = (
                    f"{current_layer}[img{i}]overlay="
                    f"x='{x_expr}':y='{y_expr}':enable='{enable_expr}'"
                )
            else:
                # Intermediate overlay
                overlay_cmd = (
                    f"{current_layer}[img{i}]overlay="
                    f"x='{x_expr}':y='{y_expr}':enable='{enable_expr}'[tmp{i}]"
                )
                current_layer = f"[tmp{i}]"
            
            filters.append(overlay_cmd)
        
        # Join all filters with semicolons
        filter_complex = ";".join(filters)
        
        return filter_complex
    
    def _build_animation_expressions(
        self,
        animation_type: str,
        video_width: int,
        video_height: int,
        img_width: int,
        img_height: int,
        center_x: int,
        center_y: int,
        start_time: float,
        end_time: float,
        anim_duration: float,
        exit_start_time: float
    ) -> Tuple[str, str]:
        """
        Build x and y position expressions for animation
        
        Returns:
            Tuple of (x_expr, y_expr)
        """
        
        if animation_type == 'slide_bottom':
            # Enter from bottom, exit to bottom
            off_screen_y = video_height + 100  # Start below screen
            
            x_expr = str(center_x)
            y_expr = (
                f"if(lt(t,{start_time}),{off_screen_y},"  # Before start: off-screen
                f"if(lt(t,{start_time + anim_duration}),"  # Entry animation
                f"{off_screen_y}-(({off_screen_y}-{center_y})*(t-{start_time})/{anim_duration}),"
                f"if(lt(t,{exit_start_time}),{center_y},"  # Static at center
                f"{center_y}+(({off_screen_y}-{center_y})*(t-{exit_start_time})/{anim_duration})"  # Exit animation
                f")))"
            )
        
        elif animation_type == 'slide_top':
            # Enter from top, exit to top
            off_screen_y = -img_height - 100  # Start above screen
            
            x_expr = str(center_x)
            y_expr = (
                f"if(lt(t,{start_time}),{off_screen_y},"
                f"if(lt(t,{start_time + anim_duration}),"
                f"{off_screen_y}+(({center_y}-{off_screen_y})*(t-{start_time})/{anim_duration}),"
                f"if(lt(t,{exit_start_time}),{center_y},"
                f"{center_y}-(({center_y}-{off_screen_y})*(t-{exit_start_time})/{anim_duration})"
                f")))"
            )
        
        elif animation_type == 'slide_left':
            # Enter from left, exit to left
            off_screen_x = -img_width - 100  # Start left of screen
            
            y_expr = str(center_y)
            x_expr = (
                f"if(lt(t,{start_time}),{off_screen_x},"
                f"if(lt(t,{start_time + anim_duration}),"
                f"{off_screen_x}+(({center_x}-{off_screen_x})*(t-{start_time})/{anim_duration}),"
                f"if(lt(t,{exit_start_time}),{center_x},"
                f"{center_x}-(({center_x}-{off_screen_x})*(t-{exit_start_time})/{anim_duration})"
                f")))"
            )
        
        elif animation_type == 'slide_right':
            # Enter from right, exit to right
            off_screen_x = video_width + 100  # Start right of screen
            
            y_expr = str(center_y)
            x_expr = (
                f"if(lt(t,{start_time}),{off_screen_x},"
                f"if(lt(t,{start_time + anim_duration}),"
                f"{off_screen_x}-(({off_screen_x}-{center_x})*(t-{start_time})/{anim_duration}),"
                f"if(lt(t,{exit_start_time}),{center_x},"
                f"{center_x}+(({off_screen_x}-{center_x})*(t-{exit_start_time})/{anim_duration})"
                f")))"
            )
        
        else:  # 'fade' - no position animation, just static centered position
            # The enable expression handles visibility
            x_expr = str(center_x)
            y_expr = str(center_y)
        
        return x_expr, y_expr
    
    def _execute_ffmpeg(
        self,
        video_path: str,
        image_paths: List[str],
        filter_complex: str,
        output_path: str
    ) -> bool:
        """
        Execute FFmpeg command to create overlay video
        
        Args:
            video_path: Background video path
            image_paths: List of image paths
            filter_complex: Filter complex string
            output_path: Output video path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build FFmpeg command
            cmd = ['ffmpeg']
            
            # Add video input
            cmd.extend(['-i', video_path])
            
            # Add all image inputs with loop
            for img_path in image_paths:
                cmd.extend(['-loop', '1', '-i', img_path])
            
            # Add filter complex
            cmd.extend(['-filter_complex', filter_complex])
            
            # Output settings
            cmd.extend([
                '-c:v', config.VIDEO_CODEC,
                '-preset', config.VIDEO_PRESET,
                '-crf', str(config.VIDEO_CRF),
                '-c:a', 'copy',  # Copy audio stream
                '-movflags', 'faststart',
                '-threads', str(config.FFMPEG_THREADS),
                '-shortest',  # Stop when shortest input ends (the video)
                '-y',  # Overwrite output
                output_path
            ])
            
            if config.VERBOSE or config.DEBUG:
                print(f"\n=== FFMPEG COMMAND ===")
                print(' '.join(cmd))
                print(f"======================\n")
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                if config.DEBUG:
                    print(f"FFmpeg error (return code {result.returncode}):")
                    print(f"STDERR: {result.stderr}")
                    print(f"STDOUT: {result.stdout}")
                return False
            
            if config.VERBOSE:
                print(f"✓ Video created successfully: {output_path}")
            
            return True
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error executing FFmpeg: {str(e)}")
                import traceback
                traceback.print_exc()
            return False
    
    def preview_timing(
        self,
        num_images: int,
        video_duration: float,
        duration_per_image: Optional[float] = None,
        delay_between_images: float = 0.0
    ) -> Optional[Dict]:
        """
        Preview timing configuration without processing
        
        Args:
            num_images: Number of images
            video_duration: Video duration
            duration_per_image: Duration per image (None for auto)
            delay_between_images: Delay between images
            
        Returns:
            Dict with timing preview
        """
        timing_info = self._calculate_timing(
            num_images=num_images,
            video_duration=video_duration,
            duration_per_image=duration_per_image,
            delay_between_images=delay_between_images
        )
        
        if not timing_info:
            return None
        
        # Add readable format
        preview = {
            'num_images': num_images,
            'video_duration': video_duration,
            'duration_per_image': timing_info['duration_per_image'],
            'delay_between_images': timing_info.get('delay_between_images', delay_between_images),
            'total_duration': timing_info['total_duration'],
            'timeline': []
        }
        
        for i in range(len(timing_info['start_times'])):
            start_time = timing_info['start_times'][i]
            end_time = timing_info['end_times'][i]
            actual_duration = end_time - start_time
            
            preview['timeline'].append({
                'image_index': i + 1,
                'start': f"{start_time:.2f}s",
                'end': f"{end_time:.2f}s",
                'duration': f"{actual_duration:.2f}s"
            })
        
        return preview


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================

def overlay_images_on_video(
    video_path: str,
    images_folder: str,
    output_path: str,
    duration_per_image: Optional[float] = None,
    delay_between_images: float = 0.0,
    animation_style: str = 'random'
) -> Optional[str]:
    """
    Main function to overlay images on video with animations
    
    Args:
        video_path: Path to background video
        images_folder: Folder containing images
        output_path: Output video path
        duration_per_image: Duration each image shows (auto if None)
        delay_between_images: Gap between images in seconds
        animation_style: Animation type
        
    Returns:
        Path to output video or None if failed
    """
    processor = ImageOverlayProcessor()
    return processor.process(
        video_path=video_path,
        images_folder=images_folder,
        output_path=output_path,
        duration_per_image=duration_per_image,
        delay_between_images=delay_between_images,
        animation_style=animation_style
    )


def preview_image_timing(
    num_images: int,
    video_duration: float,
    duration_per_image: Optional[float] = None,
    delay_between_images: float = 0.0
) -> Optional[Dict]:
    """
    Preview timing configuration for images
    """
    processor = ImageOverlayProcessor()
    return processor.preview_timing(
        num_images=num_images,
        video_duration=video_duration,
        duration_per_image=duration_per_image,
        delay_between_images=delay_between_images
    )


def get_images_from_folder(folder_path: str) -> List[str]:
    """
    Get list of images from folder
    """
    processor = ImageOverlayProcessor()
    return processor._load_images_from_folder(folder_path)


def validate_overlay_inputs(
    video_path: str,
    images_folder: str,
    duration_per_image: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Validate inputs for image overlay
    """
    # Check video
    if not os.path.exists(video_path):
        return False, "Video file not found"
    
    video_info = get_video_info(video_path)
    if not video_info:
        return False, "Invalid video file"
    
    # Check images folder
    if not os.path.exists(images_folder):
        return False, "Images folder not found"
    
    if not os.path.isdir(images_folder):
        return False, "Images path is not a folder"
    
    processor = ImageOverlayProcessor()
    images = processor._load_images_from_folder(images_folder)
    
    if not images:
        return False, "No valid images found in folder"
    
    # Check duration
    if duration_per_image is not None:
        if duration_per_image <= 0:
            return False, "Duration per image must be positive"
        
        if duration_per_image < 0.1:
            return False, "Duration per image too short (minimum 0.1s)"
    
    return True, f"Valid: {len(images)} images, video duration: {video_info['duration']:.2f}s"