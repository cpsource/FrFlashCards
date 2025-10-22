#!/usr/bin/env python3
"""
generate_build_script.py - Creates a bash script to build all web pages from lesanimaux directory
Scans for .mp3 files and generates corresponding bldwebpage.py commands
"""

import os
import sys
from pathlib import Path

def scan_directory(directory):
    """Scan directory for .mp3 files and return sorted list"""
    print(f"Scanning directory: {directory}")
    
    if not os.path.exists(directory):
        print(f"ERROR: Directory '{directory}' does not exist!")
        sys.exit(1)
    
    mp3_files = []
    for file in os.listdir(directory):
        if file.endswith('.mp3'):
            mp3_files.append(file)
    
    # Sort files to ensure consistent ordering
    mp3_files.sort()
    
    print(f"Found {len(mp3_files)} .mp3 files")
    return mp3_files

def create_bash_script(mp3_files, directory, output_file='build_pages.sh'):
    """Generate bash script to build all web pages"""
    
    max_n = len(mp3_files)
    print(f"Maximum N (maxN): {max_n}")
    
    if max_n == 0:
        print("WARNING: No .mp3 files found. No bash script created.")
        sys.exit(1)
    
    print(f"\nGenerating bash script: {output_file}")
    
    with open(output_file, 'w') as f:
        # Write bash header
        f.write("#!/bin/bash\n")
        f.write("# Auto-generated script to build web pages\n")
        f.write(f"# Generated from {max_n} .mp3 files in {directory}\n\n")
        f.write("set -e  # Exit on error\n\n")
        
        # Generate command for each mp3 file
        for idx, mp3_file in enumerate(mp3_files, start=1):
            # Remove .mp3 extension to get base name
            base_name = mp3_file[:-4]
            
            # Create image filename
            image_file = f"{directory}/{base_name}.png"
            
            # Create audio file path
            audio_file = f"{directory}/{mp3_file}"
            
            # Create text by replacing hyphens with spaces
            text = base_name.replace('-', ' ')
            
            # Write the command
            command = f'python tools/bldwebpage.py "{image_file}" "{audio_file}" "{text}" {idx} {max_n}\n'
            f.write(command)
            
            print(f"  [{idx}/{max_n}] Added: {base_name}")
        
        f.write("\necho 'All pages built successfully!'\n")
    
    # Make the bash script executable
    os.chmod(output_file, 0o755)
    
    print(f"\n✓ Bash script created: {output_file}")
    print(f"✓ Script is executable")
    print(f"\nTo run the script, execute: ./{output_file}")

def main():
    directory = "lesanimaux"
    output_file = "build_pages.sh"
    
    print("=" * 60)
    print("Web Page Build Script Generator")
    print("=" * 60)
    
    # Scan directory for mp3 files
    mp3_files = scan_directory(directory)
    
    # Create bash script
    create_bash_script(mp3_files, directory, output_file)
    
    print("=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
