#!/usr/bin/env python3
"""
Bing Image Downloader using icrawler
Downloads images based on search term
"""

import os
import sys
from pathlib import Path
from icrawler.builtin import BingImageCrawler


def download_images():
    """Download images from Bing based on user input"""
    
    print("=" * 60)
    print("BING IMAGE DOWNLOADER (using icrawler)")
    print("=" * 60)
    
    # Get search term
    search_term = input("\nEnter search term (e.g., 'sunset beach'): ").strip()
    
    if not search_term:
        print("❌ No search term provided")
        return
    
    # Get number of images
    try:
        num_images = input("How many images to download? (default: 10): ").strip()
        num_images = int(num_images) if num_images else 10
        
        if num_images <= 0:
            print("❌ Number must be positive")
            return
        
        if num_images > 1000:
            print("⚠️  Warning: Downloading 1000+ images may take a while")
            confirm = input("Continue? (y/n): ").strip().lower()
            if confirm != 'y':
                return
    
    except ValueError:
        print("❌ Invalid number")
        return
    
    # Create folder name from search term
    folder_name = search_term.replace(' ', '_').lower()
    output_folder = os.path.join('downloads', folder_name)
    
    # Create output folder
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 60)
    print(f"📥 Downloading {num_images} images for: '{search_term}'")
    print(f"📁 Saving to: {output_folder}")
    print("=" * 60)
    print("\n⏳ Please wait...\n")
    
    try:
        # Initialize Bing crawler
        bing_crawler = BingImageCrawler(
            storage={'root_dir': output_folder}
        )
        
        # Download images
        bing_crawler.crawl(
            keyword=search_term,
            max_num=num_images,
            min_size=(200, 200),  # Minimum image size (width, height)
        )
        
        # Count downloaded images
        downloaded = len([f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f))])
        
        print("\n" + "=" * 60)
        print(f"✅ Download complete!")
        print(f"📊 Downloaded: {downloaded} images")
        print(f"📁 Location: {output_folder}")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Error during download: {str(e)}")
        return
    
    # Ask if user wants to download more
    print("\nWhat would you like to do?")
    print("1. Download more images")
    print("2. Exit")
    
    choice = input("\nEnter choice (1/2): ").strip()
    
    if choice == "1":
        print("\n")
        download_images()  # Recursive call
    else:
        print("\n👋 Goodbye!")


def main():
    """Main function"""
    try:
        download_images()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()