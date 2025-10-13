#!/usr/bin/env python3
"""
Extract all Python files from a directory and save to a single text file
Ignores hidden files/folders (starting with .)
"""

import os
from pathlib import Path


def extract_python_files(root_folder, output_file):
    """
    Extract all .py files from root folder and save to output file
    
    Args:
        root_folder: Root directory to search
        output_file: Output text file path
    """
    root_path = Path(root_folder).resolve()
    
    # Check if root folder exists
    if not root_path.exists():
        print(f"❌ Error: Folder '{root_folder}' does not exist")
        return
    
    # Find all .py files
    python_files = []
    
    for item in root_path.rglob("*.py"):
        # Skip hidden files and folders (starting with .)
        parts = item.relative_to(root_path).parts
        
        # Check if any part of path starts with '.'
        if any(part.startswith('.') for part in parts):
            continue
        
        # Check if it's a file (not directory)
        if item.is_file():
            python_files.append(item)
    
    # Sort files by path for organized output
    python_files.sort()
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PYTHON FILES EXTRACTION\n")
        f.write(f"Root Folder: {root_folder}\n")
        f.write(f"Total Files: {len(python_files)}\n")
        f.write("=" * 80 + "\n\n")
        
        for py_file in python_files:
            # Get relative path from root
            relative_path = py_file.relative_to(root_path)
            
            # Write separator
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"FILE: {relative_path}\n")
            f.write("=" * 80 + "\n\n")
            
            # Read and write file content
            try:
                with open(py_file, 'r', encoding='utf-8') as py_content:
                    content = py_content.read()
                    f.write(content)
                    
                    # Add newlines if file doesn't end with newline
                    if not content.endswith('\n'):
                        f.write('\n')
                    
                    f.write("\n")  # Extra newline between files
                
                print(f"✓ Extracted: {relative_path}")
            
            except Exception as e:
                error_msg = f"Error reading file: {str(e)}\n"
                f.write(error_msg)
                print(f"✗ Failed: {relative_path} - {str(e)}")
    
    print(f"\n✅ Extraction complete!")
    print(f"📄 Output saved to: {output_file}")
    print(f"📊 Total files extracted: {len(python_files)}")


def main():
    """Main function"""
    # Configuration
    root_folder = "/Volumes/hard-drive/better-reel-gen"
    output_file = "extracted_python_code.txt"
    
    print("=" * 80)
    print("PYTHON CODE EXTRACTOR")
    print("=" * 80)
    print(f"\nRoot Folder: {root_folder}")
    print(f"Output File: {output_file}")
    print("\nSearching for .py files...\n")
    
    # Extract files
    extract_python_files(root_folder, output_file)


if __name__ == "__main__":
    main()