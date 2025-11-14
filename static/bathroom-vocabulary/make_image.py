#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_image.py
Generate an image (PNG) using OpenAI's image API.
Usage:
    python make_image.py "bar of soap"

This will produce: bar_of_soap.png
Requires: OPENAI_API_KEY
"""

import sys
import os
import re
import base64
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    print("[FATAL] Missing dependency: pip install openai", file=sys.stderr)
    sys.exit(1)


def slugify(name: str) -> str:
    """Convert spaces and special characters to underscores."""
    name = name.strip().lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name


def main():
    if len(sys.argv) != 2:
        print("Usage: python make_image.py <english-name>", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1].strip()
    if not name:
        print("Error: empty name.", file=sys.stderr)
        sys.exit(2)

    filename = slugify(name) + ".png"
    prompt = f"A detailed, high-quality photo or illustration of a {name}, isolated on a plain white background."

    print(f"[INFO] Generating image for: '{name}'")
    print(f"[INFO] Saving to: {filename}")

    if not os.getenv("OPENAI_API_KEY"):
        print("[FATAL] OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(3)

    client = OpenAI()

    try:
        # Generate image (default size 1024x1024)
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )

        # Extract base64 image data
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        Path(filename).write_bytes(image_bytes)
        print(f"[✅] Image saved: {filename}")

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()

