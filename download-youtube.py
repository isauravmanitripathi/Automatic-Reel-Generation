#!/usr/bin/env python3
"""
YouTube Downloader with yt-dlp
Downloads best quality video/audio and re-encodes for Mac compatibility
"""

import subprocess
import sys
import os
import shutil


def check_dependencies():
    """Check if yt-dlp and ffmpeg are installed"""
    dependencies = {
        'yt-dlp': 'yt-dlp',
        'ffmpeg': 'ffmpeg'
    }
    
    missing = []
    for name, command in dependencies.items():
        # Use shutil.which() to find the command in PATH
        # This works even in virtual environments
        if shutil.which(command):
            print(f"✓ {name} is installed")
        else:
            missing.append(name)
            print(f"✗ {name} is NOT installed")
    
    if missing:
        print("\nPlease install missing dependencies:")
        for dep in missing:
            if dep == 'yt-dlp':
                print("  pip install yt-dlp")
            elif dep == 'ffmpeg':
                print("  brew install ffmpeg  (on Mac)")
        sys.exit(1)


def get_url():
    """Get URL from user"""
    while True:
        url = input("\nEnter the video URL: ").strip()
        if url:
            return url
        print("Please enter a valid URL")


def get_download_type():
    """Ask user whether to download audio or video"""
    while True:
        print("\nWhat would you like to download?")
        print("1. Video (MP4)")
        print("2. Audio (MP3)")
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == '1':
            return 'video'
        elif choice == '2':
            return 'audio'
        else:
            print("Invalid choice. Please enter 1 or 2.")


def check_video_availability(url):
    """Check if video is available and get info"""
    print("\n🔍 Checking video availability...")
    
    command = [
        'yt-dlp',
        '--dump-json',
        '--no-warnings',
        url
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("✓ Video is available")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Cannot access this video. Possible reasons:")
        print("   • Video is age-restricted")
        print("   • Video is private or deleted")
        print("   • Video is geo-blocked in your region")
        print("   • Invalid URL")
        print("\nTry:")
        print("   • Using a different video URL")
        print("   • Checking if you can watch it in your browser")
        return False


def download_video(url, output_dir='downloads'):
    """Download video in best quality and re-encode to MP4"""
    print("\n🎬 Downloading video...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # yt-dlp options for video with multiple fallback formats
    command = [
        'yt-dlp',
        # Try best quality first, with multiple fallbacks
        '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
        '--merge-output-format', 'mp4',
        '--output', f'{output_dir}/%(title)s.%(ext)s',
        # Re-encode to ensure Mac compatibility
        '--postprocessor-args', 'ffmpeg:-c:v libx264 -c:a aac -movflags +faststart',
        '--progress',
        '--no-warnings',
        # Add cookies if needed for age-restricted content
        '--cookies-from-browser', 'chrome',  # Try to use Chrome cookies
        url
    ]
    
    try:
        subprocess.run(command, check=True)
        print("\n✅ Video downloaded successfully!")
        print(f"📁 Location: {output_dir}/")
        return True
    except subprocess.CalledProcessError as e:
        # Try without cookies as fallback
        print("\n⚠️  First attempt failed, trying alternative method...")
        
        command_no_cookies = [
            'yt-dlp',
            '--format', 'best',  # Simple fallback
            '--merge-output-format', 'mp4',
            '--output', f'{output_dir}/%(title)s.%(ext)s',
            '--postprocessor-args', 'ffmpeg:-c:v libx264 -c:a aac -movflags +faststart',
            '--progress',
            '--no-warnings',
            url
        ]
        
        try:
            subprocess.run(command_no_cookies, check=True)
            print("\n✅ Video downloaded successfully!")
            print(f"📁 Location: {output_dir}/")
            return True
        except subprocess.CalledProcessError:
            print(f"\n❌ Error downloading video")
            print("This video cannot be downloaded. Please try a different video.")
            return False


def download_audio(url, output_dir='downloads'):
    """Download audio and convert to MP3"""
    print("\n🎵 Downloading audio...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # yt-dlp options for audio
    command = [
        'yt-dlp',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '0',  # Best quality
        '--output', f'{output_dir}/%(title)s.%(ext)s',
        '--postprocessor-args', 'ffmpeg:-ar 48000 -b:a 320k',
        '--progress',
        '--no-warnings',
        '--cookies-from-browser', 'chrome',
        url
    ]
    
    try:
        subprocess.run(command, check=True)
        print("\n✅ Audio downloaded successfully!")
        print(f"📁 Location: {output_dir}/")
        return True
    except subprocess.CalledProcessError:
        # Try without cookies
        print("\n⚠️  First attempt failed, trying alternative method...")
        
        command_no_cookies = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--output', f'{output_dir}/%(title)s.%(ext)s',
            '--postprocessor-args', 'ffmpeg:-ar 48000 -b:a 320k',
            '--progress',
            '--no-warnings',
            url
        ]
        
        try:
            subprocess.run(command_no_cookies, check=True)
            print("\n✅ Audio downloaded successfully!")
            print(f"📁 Location: {output_dir}/")
            return True
        except subprocess.CalledProcessError:
            print(f"\n❌ Error downloading audio")
            print("This video cannot be downloaded. Please try a different video.")
            return False


def main():
    """Main function"""
    print("=" * 50)
    print("YouTube Downloader with yt-dlp")
    print("=" * 50)
    
    # Check dependencies
    check_dependencies()
    
    # Get user input
    url = get_url()
    
    # Check if video is available
    if not check_video_availability(url):
        sys.exit(1)
    
    download_type = get_download_type()
    
    # Download based on user choice
    success = False
    if download_type == 'video':
        success = download_video(url)
    else:
        success = download_audio(url)
    
    if success:
        print("\n✨ Done!")
    else:
        print("\n⚠️  Download failed. Please try a different video.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Download cancelled by user")
        sys.exit(0)