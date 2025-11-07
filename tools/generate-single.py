#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_image_single.py

Generate a single image for a French word or idiom.

Usage:
  python3 generate_image_single.py "french expression"

Example:
  python3 generate_image_single.py "être bien dans ses baskets"

Environment:
  Must have OPENAI_API_KEY defined in ~/.env
"""

import os
import sys
import base64
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, BadRequestError, APIError, APIConnectionError, RateLimitError


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
MODEL = "gpt-image-1"
IMAGE_SIZE = "1024x1024"
STYLE = "photorealistic"
BACKGROUND = "plain white background"
# ------------------------------------------------------------


def load_api_key() -> str:
    """Load OPENAI_API_KEY from ~/.env or environment."""
    env_path = Path.home() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[FATAL] OPENAI_API_KEY not found in ~/.env or environment.")
        print("→ Add a line like this to your ~/.env file:")
        print("   OPENAI_API_KEY=sk-...")
        sys.exit(1)
    return api_key


def generate_filename(french_expression: str) -> str:
    """Generate a filename from the French expression.
    Replace spaces with '-', apostrophes with '-', and add .png extension."""
    # Replace apostrophes with dashes
    filename = french_expression.replace("'", "-")
    # Replace spaces with dashes
    filename = filename.replace(" ", "-")
    # Remove any other special characters that might cause issues
    filename = filename.replace("é", "e").replace("è", "e").replace("ê", "e")
    filename = filename.replace("à", "a").replace("â", "a")
    filename = filename.replace("ç", "c")
    filename = filename.replace("î", "i").replace("ï", "i")
    filename = filename.replace("ô", "o")
    filename = filename.replace("ù", "u").replace("û", "u")
    # Convert to lowercase
    filename = filename.lower()
    # Remove any double dashes
    while "--" in filename:
        filename = filename.replace("--", "-")
    # Remove leading/trailing dashes
    filename = filename.strip("-")
    # Add .png extension
    return f"{filename}.png"


def explain_openai_error(e: Exception, context: str = ""):
    print("\n====== OPENAI ERROR ======")
    if context:
        print(f"Context: {context}")
    print(f"Type: {type(e).__name__}")
    msg = getattr(e, "message", None) or str(e)
    print(f"Message: {msg}")
    code = getattr(e, 'code', None)
    if code:
        print(f"Code: {code}")
    status = getattr(e, 'status_code', None)
    if status:
        print(f"HTTP Status: {status}")
    print("====== END ERROR ======\n")


def build_prompt(french_expression: str) -> str:
    """Return a polished English image prompt for the given expression."""
    return (
        f"Photorealistic illustration of the French expression '{french_expression}'. "
        f"Depict the meaning visually in a simple, clear way. "
        f"Use a {BACKGROUND}, good lighting, and balanced composition. "
        f"No text, captions, or labels in the image."
    )


def generate_image(client: OpenAI, prompt: str, size: str = IMAGE_SIZE) -> bytes:
    """Call OpenAI API and return decoded PNG bytes."""
    result = client.images.generate(model=MODEL, prompt=prompt, size=size)
    b64 = result.data[0].b64_json
    return base64.b64decode(b64)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_image_single.py \"french expression\"")
        sys.exit(1)

    french_expression = sys.argv[1]
    output_file = Path(generate_filename(french_expression))

    print(f"→ Generating image for: {french_expression}")
    print(f"  Output file: {output_file}")

    api_key = load_api_key()
    client = OpenAI(api_key=api_key)

    prompt = build_prompt(french_expression)
    print(f"  Model: {MODEL}")
    print(f"  Prompt: {prompt[:100]}...")

    try:
        print("\n⏳ Calling OpenAI API...")
        png_bytes = generate_image(client, prompt)
        output_file.write_bytes(png_bytes)
        print(f"✅ Saved image: {output_file.resolve()}")
        
        # Now resize the image to 64px
        print(f"\n⏳ Resizing image to 64px...")
        resize_command = ["python3", "resize_png.py", str(output_file), "64"]
        print(f"  Running: {' '.join(resize_command)}")
        
        result = subprocess.run(resize_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Resize successful")
            if result.stdout:
                print(f"  Output: {result.stdout.strip()}")
        else:
            print(f"❌ Resize failed with code {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()}")
                
    except (BadRequestError, APIError, APIConnectionError, RateLimitError) as e:
        explain_openai_error(e, "Image generation failed")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Unexpected: {e}")
        sys.exit(3)


    # ------------------------------------------------------------
    # After successful resize, build MP3
    # ------------------------------------------------------------
    if result.returncode == 0:
        base_name = output_file.stem  # e.g. "bonjour_ca"
        french_text = french_expression
        print(f"\n⏳ Generating MP3 for: {french_text}")
        mp3_command = [
            "python3",
            "make_mp3_single.py",
            base_name,
            "clear, natural, use a calm woman's French voice",
            french_text
        ]
        print(f"  Running: {' '.join(mp3_command)}")
        mp3_result = subprocess.run(mp3_command, capture_output=True, text=True)

        if mp3_result.returncode == 0:
            print("✅ MP3 generation successful")
            if mp3_result.stdout:
                print(f"  Output: {mp3_result.stdout.strip()}")
        else:
            print(f"❌ MP3 generation failed with code {mp3_result.returncode}")
            if mp3_result.stderr:
                print(f"  Error: {mp3_result.stderr.strip()}")
            
if __name__ == "__main__":
    main()
