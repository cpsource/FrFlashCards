#!/usr/bin/env python3
"""
resize_png.py - Reduces PNG file size to approximately 150KB
Usage: python resize_png.py <input.png>
"""

import sys
import os
from PIL import Image

def get_file_size_kb(filepath):
    """Get file size in KB"""
    return os.path.getsize(filepath) / 1024

def resize_image(input_path, target_size_kb=150, quality_start=85):
    """
    Resize and compress PNG to target file size
    
    Args:
        input_path: Path to input PNG file
        target_size_kb: Target file size in KB (default 150)
        quality_start: Starting quality for compression (default 85)
    """
    
    if not os.path.exists(input_path):
        print(f"ERROR: File '{input_path}' not found!")
        sys.exit(1)
    
    if not input_path.lower().endswith('.png'):
        print("ERROR: File must be a PNG image!")
        sys.exit(1)
    
    # Get original file info
    original_size = get_file_size_kb(input_path)
    print(f"Original file: {input_path}")
    print(f"Original size: {original_size:.2f} KB")
    
    # Open image
    try:
        img = Image.open(input_path)
        original_width, original_height = img.size
        print(f"Original dimensions: {original_width}x{original_height}")
    except Exception as e:
        print(f"ERROR: Could not open image: {e}")
        sys.exit(1)
    
    # Create output filename
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}_resized.png"
    
    # If already smaller than target, just inform user
    if original_size <= target_size_kb:
        print(f"\nFile is already {original_size:.2f} KB (≤ {target_size_kb} KB)")
        print("No resizing needed!")
        return
    
    # Start with a scale factor based on file size ratio
    # Estimate: file size roughly proportional to pixel count
    scale_factor = (target_size_kb / original_size) ** 0.5
    
    # Try progressively smaller sizes until we hit target
    attempts = 0
    max_attempts = 10
    
    while attempts < max_attempts:
        attempts += 1
        
        # Calculate new dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        print(f"\nAttempt {attempts}: Trying {new_width}x{new_height} (scale: {scale_factor:.3f})")
        
        # Resize image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save with optimization
        resized_img.save(output_path, 'PNG', optimize=True)
        
        # Check result size
        result_size = get_file_size_kb(output_path)
        print(f"Result size: {result_size:.2f} KB")
        
        # Check if we're within acceptable range (target ± 10%)
        if target_size_kb * 0.9 <= result_size <= target_size_kb * 1.1:
            print(f"\n✓ Success! Created: {output_path}")
            print(f"✓ Final size: {result_size:.2f} KB")
            print(f"✓ Final dimensions: {new_width}x{new_height}")
            print(f"✓ Reduction: {((original_size - result_size) / original_size * 100):.1f}%")
            return
        
        # Adjust scale factor for next attempt
        if result_size > target_size_kb:
            # File too large, make smaller
            scale_factor *= 0.9
        else:
            # File too small, make larger
            scale_factor *= 1.05
    
    # If we exhausted attempts, use the last result
    print(f"\n✓ Created: {output_path}")
    print(f"✓ Final size: {result_size:.2f} KB (target was {target_size_kb} KB)")
    print(f"✓ Final dimensions: {new_width}x{new_height}")
    print(f"Note: Closest result after {max_attempts} attempts")

def main():
    if len(sys.argv) != 2:
        print("Usage: python resize_png.py <input.png>")
        print("Example: python resize_png.py photo.png")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    print("=" * 60)
    print("PNG Resizer - Target: ~150KB")
    print("=" * 60)
    
    resize_image(input_path, target_size_kb=150)
    
    print("=" * 60)

if __name__ == "__main__":
    main()

