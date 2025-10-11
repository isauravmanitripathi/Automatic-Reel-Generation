"""
Pinterest downloader using gallery-dl
Supports Pinterest pins and boards
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse, parse_qs

import config


class PinterestDownloader:
    """Handler for Pinterest downloads using gallery-dl"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize Pinterest downloader
        
        Args:
            output_dir: Directory to save downloads (default: config.DOWNLOADS_DIR)
        """
        self.output_dir = output_dir or config.DOWNLOADS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_pin(self, url: str) -> Optional[Dict]:
        """
        Download single Pinterest pin
        
        Args:
            url: Pinterest pin URL
            
        Returns:
            Dict with download info or None if failed
        """
        try:
            # Create subdirectory for this pin
            pin_id = self._extract_pin_id(url)
            download_dir = self.output_dir / f"pinterest_{pin_id}"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Build gallery-dl command
            cmd = [
                'gallery-dl',
                '--write-metadata',
                '-d', str(download_dir),
                url
            ]
            
            # Execute
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
            
            # Find downloaded video
            video_files = self._find_video_files(download_dir)
            
            if not video_files:
                return None
            
            video_path = video_files[0]
            
            # Load metadata if available
            metadata = self._load_metadata(download_dir)
            
            return {
                'video_path': str(video_path),
                'title': metadata.get('description', 'Pinterest Video')[:100] if metadata else 'Pinterest Video',
                'url': url,
                'id': pin_id,
                'metadata': metadata,
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error downloading Pinterest pin: {str(e)}")
            return None
    
    def download_board(self, url: str, max_count: int = 50) -> List[Dict]:
        """
        Download videos from Pinterest board
        
        Args:
            url: Pinterest board URL
            max_count: Maximum number of videos to download
            
        Returns:
            List of download results
        """
        try:
            download_dir = self.output_dir / "pinterest_board"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = [
                'gallery-dl',
                '--write-metadata',
                '-d', str(download_dir),
                '--range', f'1-{max_count}',
                url
            ]
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return []
            
            # Find all videos
            video_files = self._find_video_files(download_dir)
            
            results = []
            for video_path in video_files:
                results.append({
                    'video_path': str(video_path),
                    'title': f'Pinterest Video {len(results) + 1}',
                    'url': url,
                })
            
            return results
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error downloading Pinterest board: {str(e)}")
            return []
    
    def download_search(self, search_url: str, max_count: int = 50) -> List[Dict]:
        """
        Download videos from Pinterest search results
        
        Args:
            search_url: Pinterest search URL
            max_count: Maximum number of videos to download
            
        Returns:
            List of download results
        """
        try:
            # Extract search term
            search_term = self._extract_search_term(search_url)
            
            download_dir = self.output_dir / f"pinterest_search_{search_term}"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = [
                'gallery-dl',
                '--write-metadata',
                '-d', str(download_dir),
                '--range', f'1-{max_count}',
                search_url
            ]
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return []
            
            # Find all videos
            video_files = self._find_video_files(download_dir)
            
            results = []
            for video_path in video_files:
                results.append({
                    'video_path': str(video_path),
                    'title': f'{search_term} - {len(results) + 1}',
                    'url': search_url,
                })
            
            return results
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error downloading Pinterest search: {str(e)}")
            return []
    
    def _extract_pin_id(self, url: str) -> str:
        """Extract pin ID from URL"""
        # Pinterest URLs: /pin/PIN_ID/
        parts = url.rstrip('/').split('/')
        
        for i, part in enumerate(parts):
            if part == 'pin' and i + 1 < len(parts):
                return parts[i + 1]
        
        # Fallback
        return str(hash(url))[:10]
    
    def _extract_search_term(self, url: str) -> str:
        """Extract search term from Pinterest search URL"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Pinterest uses 'q' parameter for search
            search_term = query_params.get('q', ['unknown'])[0]
            return search_term.replace(' ', '_')
        except Exception:
            return 'pinterest_search'
    
    def _find_video_files(self, directory: Path) -> List[Path]:
        """Find all video files in directory"""
        video_files = []
        
        for ext in config.VIDEO_EXTENSIONS:
            video_files.extend(directory.rglob(f'*{ext}'))
        
        # Sort by modification time
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


def download(url: str, max_count: int = 50, output_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Main download function for Pinterest
    
    Args:
        url: Pinterest URL (pin/board/search)
        max_count: Maximum videos to download for boards/searches
        output_dir: Custom output directory
        
    Returns:
        Dict with download results or None if failed
    """
    downloader = PinterestDownloader(output_dir)
    
    # Detect URL type
    if '/pin/' in url:
        # Single pin
        return downloader.download_pin(url)
    elif '/search/' in url or '?q=' in url:
        # Search results
        results = downloader.download_search(url, max_count)
        return results[0] if results else None
    else:
        # Board URL
        results = downloader.download_board(url, max_count)
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