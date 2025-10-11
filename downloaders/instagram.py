"""
Instagram downloader using gallery-dl
Supports Instagram Reels, Posts, and IGTV
"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List

import config


class InstagramDownloader:
    """Handler for Instagram downloads using gallery-dl"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize Instagram downloader
        
        Args:
            output_dir: Directory to save downloads (default: config.DOWNLOADS_DIR)
        """
        self.output_dir = output_dir or config.DOWNLOADS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_reel(self, url: str, cookies_file: Optional[str] = None) -> Optional[Dict]:
        """
        Download Instagram Reel
        
        Args:
            url: Instagram reel URL
            cookies_file: Optional cookies file for authentication
            
        Returns:
            Dict with download info or None if failed
        """
        try:
            # Create a specific subdirectory for this download
            download_id = self._extract_id_from_url(url)
            download_dir = self.output_dir / f"instagram_{download_id}"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Build gallery-dl command
            cmd = [
                'gallery-dl',
                '--write-metadata',
                '-d', str(download_dir),
            ]
            
            # Add cookies if provided
            if cookies_file and os.path.exists(cookies_file):
                cmd.extend(['--cookies', cookies_file])
            
            cmd.append(url)
            
            # Execute download
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                if config.DEBUG:
                    print(f"gallery-dl error: {result.stderr}")
                return None
            
            # Find downloaded video file
            video_files = self._find_video_files(download_dir)
            
            if not video_files:
                return None
            
            video_path = video_files[0]  # Use first video found
            
            # Try to load metadata
            metadata = self._load_metadata(download_dir)
            
            return {
                'video_path': str(video_path),
                'title': metadata.get('description', '')[:100] if metadata else 'Instagram Reel',
                'url': url,
                'id': download_id,
                'metadata': metadata,
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error downloading Instagram reel: {str(e)}")
            return None
    
    def download_post(self, url: str, cookies_file: Optional[str] = None) -> Optional[Dict]:
        """
        Download Instagram Post (may contain multiple videos/images)
        
        Args:
            url: Instagram post URL
            cookies_file: Optional cookies file
            
        Returns:
            Dict with download info
        """
        # Same logic as download_reel, gallery-dl handles both
        return self.download_reel(url, cookies_file)
    
    def download_profile_reels(self, profile_url: str, max_count: int = 50, 
                               cookies_file: Optional[str] = None) -> List[Dict]:
        """
        Download multiple reels from a profile
        
        Args:
            profile_url: Instagram profile URL
            max_count: Maximum number of reels to download
            cookies_file: Optional cookies file
            
        Returns:
            List of download results
        """
        try:
            download_dir = self.output_dir / "instagram_profile"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = [
                'gallery-dl',
                '--write-metadata',
                '-d', str(download_dir),
                '--range', f'1-{max_count}',
            ]
            
            if cookies_file and os.path.exists(cookies_file):
                cmd.extend(['--cookies', cookies_file])
            
            cmd.append(profile_url)
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return []
            
            # Find all downloaded videos
            video_files = self._find_video_files(download_dir)
            
            results = []
            for video_path in video_files:
                results.append({
                    'video_path': str(video_path),
                    'title': f'Instagram Reel {len(results) + 1}',
                    'url': profile_url,
                })
            
            return results
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error downloading profile reels: {str(e)}")
            return []
    
    def _extract_id_from_url(self, url: str) -> str:
        """Extract ID from Instagram URL"""
        # Instagram URLs: /p/CODE/, /reel/CODE/, /tv/CODE/
        parts = url.rstrip('/').split('/')
        for i, part in enumerate(parts):
            if part in ['p', 'reel', 'tv'] and i + 1 < len(parts):
                return parts[i + 1]
        
        # Fallback: use hash of URL
        return str(hash(url))[:10]
    
    def _find_video_files(self, directory: Path) -> List[Path]:
        """Find all video files in directory"""
        video_files = []
        
        for ext in config.VIDEO_EXTENSIONS:
            video_files.extend(directory.rglob(f'*{ext}'))
        
        # Sort by modification time (newest first)
        video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return video_files
    
    def _load_metadata(self, directory: Path) -> Optional[Dict]:
        """Load metadata JSON file if exists"""
        json_files = list(directory.rglob('*.json'))
        
        if not json_files:
            return None
        
        try:
            with open(json_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None


def download(url: str, cookies_file: Optional[str] = None, output_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Main download function for Instagram
    
    Args:
        url: Instagram URL (reel/post/profile)
        cookies_file: Optional cookies file for authentication
        output_dir: Custom output directory
        
    Returns:
        Dict with download results or None if failed
    """
    downloader = InstagramDownloader(output_dir)
    
    # Detect URL type
    if '/reel/' in url or '/p/' in url or '/tv/' in url:
        return downloader.download_reel(url, cookies_file)
    else:
        # Assume profile URL
        results = downloader.download_profile_reels(url, max_count=10, cookies_file=cookies_file)
        return results[0] if results else None


def check_gallery_dl_installed() -> bool:
    """
    Check if gallery-dl is installed
    
    Returns:
        True if installed, False otherwise
    """
    try:
        subprocess.run(['gallery-dl', '--version'], 
                      capture_output=True, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False