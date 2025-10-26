#!/usr/bin/env python3
"""
check_mp3_png.py - Verifies that every .mp3 file has a corresponding .png file
Usage: python check_mp3_png.py <directory>
"""

import os
import sys
from pathlib import Path

def check_mp3_png_pairs(directory):
    """
    Check if every .mp3 file has a corresponding .png file
    
    Args:
        directory: Path to directory to scan
    
    Returns:
        True if all mp3 files have corresponding png files, False otherwise
    """
    
    if not os.path.exists(directory):
        print(f"ERROR: Directory '{directory}' does not exist!")
        sys.exit(1)
    
    if not os.path.isdir(directory):
        print(f"ERROR: '{directory}' is not a directory!")
        sys.exit(1)
    
    print(f"Scanning directory: {directory}")
    print("=" * 60)
    
    # Find all .mp3 files
    mp3_files = []
    for file in os.listdir(directory):
        if file.endswith('.mp3'):
            mp3_files.append(file)
    
    if not mp3_files:
        print("No .mp3 files found in directory")
        return True
    
    mp3_files.sort()
    print(f"Found {len(mp3_files)} .mp3 file(s)\n")
    
    # Check for corresponding .png files
    missing_png = []
    all_good = []
    
    for mp3_file in mp3_files:
        # Get base name without extension
        base_name = os.path.splitext(mp3_file)[0]
        png_file = f"{base_name}.png"
        png_path = os.path.join(directory, png_file)
        
        if os.path.exists(png_path):
            all_good.append(mp3_file)
            print(f"✓ {mp3_file} → {png_file}")
        else:
            missing_png.append((mp3_file, png_file))
            print(f"✗ {mp3_file} → MISSING: {png_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  Total .mp3 files: {len(mp3_files)}")
    print(f"  With .png files:  {len(all_good)}")
    print(f"  Missing .png:     {len(missing_png)}")
    
    if missing_png:
        print("\n" + "=" * 60)
        print("ERROR: The following .mp3 files are missing .png files:")
        for mp3, png in missing_png:
            print(f"  - {mp3} (expected: {png})")
        print("=" * 60)
        return False
    else:
        print("\n✓ All .mp3 files have corresponding .png files!")
        print("=" * 60)
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_mp3_png.py <directory>")
        print("Example: python check_mp3_png.py lesanimaux")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    success = check_mp3_png_pairs(directory)
    
    # Exit with error code if files are missing
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
