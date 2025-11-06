#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_image_single.py

Generate a single image for a French word or idiom.

Usage:
  python3 generate_image_single.py <output_filename.png> "french expression"

Example:
  python3 generate_image_single.py etre_bien_dans_ses_baskets.png "être bien dans ses baskets"

Environment:
  Must have OPENAI_API_KEY defined in ~/.env
"""

import os
import sys
import base64
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
    if len(sys.argv) < 3:
        print("Usage: python3 generate_image_single.py <output_filename.png> \"french expression\"")
        sys.exit(1)

    output_file = Path(sys.argv[1])
    french_expression = sys.argv[2]

    api_key = load_api_key()
    client = OpenAI(api_key=api_key)

    prompt = build_prompt(french_expression)
    print(f"→ Generating image for: {french_expression}")
    print(f"  Output file: {output_file}")
    print(f"  Model: {MODEL}")

    try:
        png_bytes = generate_image(client, prompt)
        output_file.write_bytes(png_bytes)
        print(f"✅ Saved image: {output_file.resolve()}")
    except (BadRequestError, APIError, APIConnectionError, RateLimitError) as e:
        explain_openai_error(e, "Image generation failed")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Unexpected: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()

