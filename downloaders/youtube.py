"""
YouTube downloader using yt-dlp
Supports YouTube videos, Shorts, and audio extraction
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, List
import yt_dlp

import config


class YouTubeDownloader:
    """Handler for YouTube downloads using yt-dlp"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize YouTube downloader
        
        Args:
            output_dir: Directory to save downloads (default: config.DOWNLOADS_DIR)
        """
        self.output_dir = output_dir or config.DOWNLOADS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # yt-dlp options for video
        self.video_opts = {
            'format': config.YTDLP_FORMAT,
            'outtmpl': str(self.output_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': not config.VERBOSE,
            'no_warnings': not config.VERBOSE,
            'extract_flat': False,
            'ignoreerrors': False,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        # yt-dlp options for audio only
        self.audio_opts = {
            'format': config.YTDLP_AUDIO_FORMAT,
            'outtmpl': str(self.output_dir / '%(title)s_%(id)s_audio.%(ext)s'),
            'quiet': not config.VERBOSE,
            'no_warnings': not config.VERBOSE,
            'extract_flat': False,
            'ignoreerrors': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
        }
    
    def download_video(self, url: str) -> Optional[Dict]:
        """
        Download video from YouTube
        
        Args:
            url: YouTube video/shorts URL
            
        Returns:
            Dict with download info or None if failed
            {
                'video_path': str,
                'title': str,
                'duration': float,
                'url': str,
                'id': str
            }
        """
        try:
            with yt_dlp.YoutubeDL(self.video_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Download the video
                ydl.download([url])
                
                # Get the downloaded file path
                video_path = ydl.prepare_filename(info)
                
                # Handle format conversion (might have different extension)
                video_path = self._find_downloaded_file(video_path)
                
                if not video_path or not os.path.exists(video_path):
                    return None
                
                return {
                    'video_path': video_path,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'url': url,
                    'id': info.get('id', 'unknown'),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error downloading video: {str(e)}")
            return None
    
    def download_audio(self, url: str) -> Optional[Dict]:
        """
        Download audio only from YouTube
        
        Args:
            url: YouTube video/shorts URL
            
        Returns:
            Dict with download info or None if failed
        """
        try:
            with yt_dlp.YoutubeDL(self.audio_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Download the audio
                ydl.download([url])
                
                # Get the downloaded file path
                audio_path = ydl.prepare_filename(info)
                
                # Handle format conversion
                audio_path = self._find_downloaded_file(audio_path, is_audio=True)
                
                if not audio_path or not os.path.exists(audio_path):
                    return None
                
                return {
                    'audio_path': audio_path,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'url': url,
                    'id': info.get('id', 'unknown'),
                }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error downloading audio: {str(e)}")
            return None
    
    def download_both(self, url: str) -> Optional[Dict]:
        """
        Download both video and audio separately
        
        Args:
            url: YouTube video/shorts URL
            
        Returns:
            Dict with both paths or None if failed
        """
        video_result = self.download_video(url)
        audio_result = self.download_audio(url)
        
        if video_result and audio_result:
            return {
                'video_path': video_result['video_path'],
                'audio_path': audio_result['audio_path'],
                'title': video_result['title'],
                'duration': video_result['duration'],
                'url': url,
                'id': video_result['id'],
            }
        
        return video_result  # Return video only if audio fails
    
    def _find_downloaded_file(self, expected_path: str, is_audio: bool = False) -> Optional[str]:
        """
        Find the actual downloaded file (might have different extension)
        
        Args:
            expected_path: Expected file path from yt-dlp
            is_audio: Whether looking for audio file
            
        Returns:
            Actual file path or None
        """
        # Try exact path first
        if os.path.exists(expected_path):
            return expected_path
        
        # Try without extension and search
        base_path = os.path.splitext(expected_path)[0]
        directory = os.path.dirname(expected_path)
        basename = os.path.basename(base_path)
        
        # Search for files matching the base name
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.startswith(basename):
                    full_path = os.path.join(directory, file)
                    
                    # Check if it's the right type
                    ext = os.path.splitext(file)[1].lower()
                    if is_audio and ext in config.AUDIO_EXTENSIONS:
                        return full_path
                    elif not is_audio and ext in config.VIDEO_EXTENSIONS:
                        return full_path
        
        return None
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video information without downloading
        
        Args:
            url: YouTube video/shorts URL
            
        Returns:
            Dict with video info or None
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'url': url,
                    'id': info.get('id', 'unknown'),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting video info: {str(e)}")
            return None


def download(url: str, download_audio: bool = False, output_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Main download function for YouTube
    
    Args:
        url: YouTube video/shorts URL
        download_audio: Whether to download audio separately
        output_dir: Custom output directory
        
    Returns:
        Dict with download results or None if failed
    """
    downloader = YouTubeDownloader(output_dir)
    
    if download_audio:
        return downloader.download_both(url)
    else:
        return downloader.download_video(url)


def download_playlist(playlist_url: str, max_videos: int = 50, download_audio: bool = False) -> List[Dict]:
    """
    Download videos from a YouTube playlist
    
    Args:
        playlist_url: YouTube playlist URL
        max_videos: Maximum number of videos to download
        download_audio: Whether to download audio separately
        
    Returns:
        List of download results
    """
    downloader = YouTubeDownloader()
    results = []
    
    try:
        # Get playlist info
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            
            if not playlist_info or 'entries' not in playlist_info:
                return results
            
            # Download each video (up to max_videos)
            for i, entry in enumerate(playlist_info['entries'][:max_videos]):
                if not entry:
                    continue
                
                video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry['id']}"
                
                result = download(video_url, download_audio)
                
                if result:
                    results.append(result)
    
    except Exception as e:
        if config.DEBUG:
            print(f"Error downloading playlist: {str(e)}")
    
    return results


def check_ytdlp_installed() -> bool:
    """
    Check if yt-dlp is installed
    
    Returns:
        True if installed, False otherwise
    """
    try:
        subprocess.run(['yt-dlp', '--version'], 
                      capture_output=True, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False