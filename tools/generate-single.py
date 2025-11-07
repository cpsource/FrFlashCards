#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_image_single.py

Generate a single image, MP3, and HTML flash card for a French word or idiom.

Usage:
  python3 generate_image_single.py "french expression"

Example:
  python3 generate_image_single.py "être bien dans ses baskets"

Behavior:
  - Uses OpenAI to generate <base>.png (unless it already exists).
  - Calls resize_png.py to resize the PNG to 64px (when generated).
  - Calls make_mp3_single.py to generate <base>.mp3 (unless it already exists).
  - Calls generate-french-examples.py 3 "<french expression>" and
    embeds the resulting HTML into <base>.html.
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
    filename = french_expression.replace("'", "-")
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


def build_html_page(
    french_expression: str,
    base_name: str,
    png_name: str,
    mp3_name: str,
    examples_html: str,
) -> str:
    """Build a simple HTML flash card page including image, audio, and examples."""
    title = french_expression
    # We insert examples_html as-is (already HTML from generate-french-examples.py)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{title}</title>\n"
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '  <link rel="stylesheet"\n'
        '        href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">\n'
        "  <style>\n"
        "    body {\n"
        "      font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif;\n"
        "      background-color: #ffffff;\n"
        "      margin-top: 40px;\n"
        "      text-align: center;\n"
        "    }\n"
        "    img.card-image {\n"
        "      max-width: 300px;\n"
        "      margin: 20px auto;\n"
        "      display: block;\n"
        "    }\n"
        "    .examples-block {\n"
        "      margin-top: 30px;\n"
        "    }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{title}</h1>\n"
        f'  <img src="{png_name}" alt="{title}" class="card-image img-fluid">\n'
        "  <p>\n"
        "    <audio controls>\n"
        f'      <source src="{mp3_name}" type="audio/mpeg">\n'
        "      Votre navigateur ne supporte pas la lecture audio.\n"
        "    </audio>\n"
        "  </p>\n"
        '  <div class="examples-block">\n'
        f"{examples_html}\n"
        "  </div>\n"
        '  <hr>\n'
        '  <a href="../index.html" class="btn btn-secondary">↩️ Retour</a>\n'
        "</body>\n"
        "</html>\n"
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_image_single.py \"french expression\"")
        sys.exit(1)

    french_expression = sys.argv[1]

    # Base PNG filename and paths
    png_path = Path(generate_filename(french_expression))
    base_name = png_path.stem  # e.g. "etre-bien-dans-ses-baskets"
    mp3_path = Path(f"{base_name}.mp3")
    html_path = Path(f"{base_name}.html")

    print(f"→ Processing expression: {french_expression}")
    print(f"  Base name  : {base_name}")
    print(f"  PNG file   : {png_path}")
    print(f"  MP3 file   : {mp3_path}")
    print(f"  HTML file  : {html_path}")

    api_key = load_api_key()
    client = OpenAI(api_key=api_key)

    # ------------------------------------------------------------
    # 1. Image generation (skip if PNG already exists)
    # ------------------------------------------------------------
    if png_path.exists():
        print(f"✔ PNG already exists, skipping image generation: {png_path}")
    else:
        prompt = build_prompt(french_expression)
        print(f"  Model: {MODEL}")
        print(f"  Prompt: {prompt[:100]}...")

        try:
            print("\n⏳ Calling OpenAI API for image...")
            png_bytes = generate_image(client, prompt)
            png_path.write_bytes(png_bytes)
            print(f"✅ Saved image: {png_path.resolve()}")

            # Resize the image to 64px
            print(f"\n⏳ Resizing image to 64px...")
            resize_command = ["python3", "resize_png.py", str(png_path), "64"]
            print(f"  Running: {' '.join(resize_command)}")

            result = subprocess.run(resize_command, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Resize successful")
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
            print(f"[ERROR] Unexpected during image step: {e}")
            sys.exit(3)

    # ------------------------------------------------------------
    # 2. MP3 generation (skip if MP3 already exists)
    # ------------------------------------------------------------
    if mp3_path.exists():
        print(f"✔ MP3 already exists, skipping audio generation: {mp3_path}")
    else:
        print(f"\n⏳ Generating MP3 for: {french_expression}")
        mp3_command = [
            "python3",
            "make_mp3_single.py",
            base_name,
            "clear, natural, use a calm woman's French voice",
            french_expression,
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

    # ------------------------------------------------------------
    # 3. Generate French examples HTML (using external script)
    # ------------------------------------------------------------
    print("\n⏳ Generating French examples HTML...")
    examples_cmd = [
        "python3",
        "generate-french-examples.py",
        "3",
        french_expression,
    ]
    print(f"  Running: {' '.join(examples_cmd)}")
    examples_result = subprocess.run(examples_cmd, capture_output=True, text=True)

    if examples_result.returncode != 0:
        print(f"❌ Example generation failed with code {examples_result.returncode}")
        if examples_result.stderr:
            print(f"  Error: {examples_result.stderr.strip()}")
        examples_html = "<!-- examples could not be generated -->"
    else:
        examples_html = examples_result.stdout.strip()
        print("✅ Examples generated successfully")

    # ------------------------------------------------------------
    # 4. Build HTML card file
    # ------------------------------------------------------------
    print("\n⏳ Building HTML flash card...")
    html_content = build_html_page(
        french_expression=french_expression,
        base_name=base_name,
        png_name=png_path.name,
        mp3_name=mp3_path.name,
        examples_html=examples_html,
    )
    html_path.write_text(html_content, encoding="utf-8")
    print(f"✅ HTML flash card written to: {html_path.resolve()}")


if __name__ == "__main__":
    main()

