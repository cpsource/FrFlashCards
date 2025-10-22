#!/usr/bin/env python3
"""
resize_png.py - Reduces PNG file size to approximately 150KB and resizes to 4" width
Usage: python resize_png.py <input.png>
"""

import sys
import os
from PIL import Image

def get_file_size_kb(filepath):
    """Get file size in KB"""
    return os.path.getsize(filepath) / 1024

def resize_image(input_path, target_size_kb=150, target_width_inches=4, dpi=96):
    """
    Resize PNG to 4" width (maintaining aspect ratio) and compress to target file size
    
    Args:
        input_path: Path to input PNG file
        target_size_kb: Target file size in KB (default 150)
        target_width_inches: Target width in inches (default 4)
        dpi: Dots per inch for conversion (default 96 - standard screen DPI)
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
        print(f"Original dimensions: {original_width}x{original_height} pixels")
    except Exception as e:
        print(f"ERROR: Could not open image: {e}")
        sys.exit(1)
    
    # Calculate target width in pixels (4 inches at given DPI)
    target_width_pixels = int(target_width_inches * dpi)
    
    # Calculate target height maintaining aspect ratio
    aspect_ratio = original_height / original_width
    target_height_pixels = int(target_width_pixels * aspect_ratio)
    
    print(f"\nTarget dimensions for {target_width_inches}\" width at {dpi} DPI:")
    print(f"  {target_width_pixels}x{target_height_pixels} pixels")
    
    # Create output filename
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}_resized.png"
    
    # Resize to target dimensions
    print(f"\nResizing to {target_width_pixels}x{target_height_pixels}...")
    resized_img = img.resize((target_width_pixels, target_height_pixels), Image.Resampling.LANCZOS)
    
    # Save with optimization
    resized_img.save(output_path, 'PNG', optimize=True)
    
    result_size = get_file_size_kb(output_path)
    print(f"Initial result size: {result_size:.2f} KB")
    
    # If file is still too large, we need to reduce quality/dimensions further
    if result_size > target_size_kb * 1.2:
        print(f"\nFile still larger than {target_size_kb} KB, applying additional compression...")
        
        # Try reducing dimensions slightly while maintaining aspect ratio
        scale_factor = (target_size_kb / result_size) ** 0.5
        adjusted_width = int(target_width_pixels * scale_factor)
        adjusted_height = int(target_height_pixels * scale_factor)
        
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts and result_size > target_size_kb * 1.1:
            attempts += 1
            
            print(f"  Attempt {attempts}: Trying {adjusted_width}x{adjusted_height}")
            
            # Resize from original image for better quality
            resized_img = img.resize((adjusted_width, adjusted_height), Image.Resampling.LANCZOS)
            resized_img.save(output_path, 'PNG', optimize=True)
            
            result_size = get_file_size_kb(output_path)
            print(f"  Result size: {result_size:.2f} KB")
            
            if result_size <= target_size_kb * 1.1:
                break
            
            # Adjust dimensions for next attempt
            scale_factor *= 0.95
            adjusted_width = int(target_width_pixels * scale_factor)
            adjusted_height = int(target_height_pixels * scale_factor)
    
    # Final report
    final_width, final_height = Image.open(output_path).size
    final_width_inches = final_width / dpi
    
    print(f"\n{'=' * 60}")
    print(f"✓ Success! Created: {output_path}")
    print(f"✓ Final size: {result_size:.2f} KB (target: ~{target_size_kb} KB)")
    print(f"✓ Final dimensions: {final_width}x{final_height} pixels")
    print(f"✓ Final width: {final_width_inches:.2f} inches at {dpi} DPI")
    print(f"✓ Size reduction: {((original_size - result_size) / original_size * 100):.1f}%")
    print(f"✓ Aspect ratio maintained: {aspect_ratio:.3f}")
    print(f"{'=' * 60}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python resize_png.py <input.png>")
        print("Example: python resize_png.py photo.png")
        print("\nThis will resize the image to 4 inches wide (~150KB)")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    print("=" * 60)
    print("PNG Resizer - Target: 4\" wide, ~150KB")
    print("=" * 60)
    
    resize_image(input_path, target_size_kb=150, target_width_inches=4)

if __name__ == "__main__":
    main()

