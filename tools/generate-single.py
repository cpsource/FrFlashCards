#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate-single.py

Generate a single image, MP3, and HTML flash card for a French word or idiom.

Usage:
  python3 generate-single.py "french expression"

Example:
  python3 generate-single.py "être bien dans ses baskets"

Behavior:
  - Uses OpenAI to generate <base>.png (unless it already exists).
  - Calls resize_png.py to resize the PNG to 64px (when generated).
  - Calls make_mp3_single.py to generate <base>.mp3 (unless it already exists).
  - Calls generate-french-examples.py 3 "<french expression>" and embeds the resulting HTML into <base>.html.
  - Includes footer.html at the bottom of the page.
"""

import os
import sys
import base64
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, BadRequestError, APIError, APIConnectionError, RateLimitError


MODEL = "gpt-image-1"
IMAGE_SIZE = "1024x1024"
BACKGROUND = "plain white background"


def load_api_key() -> str:
    """Load OPENAI_API_KEY from ~/.env or environment."""
    env_path = Path.home() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[FATAL] OPENAI_API_KEY not found.")
        sys.exit(1)
    return api_key


def generate_filename(french_expression: str) -> str:
    """Return sanitized filename based on expression."""
    filename = french_expression.replace("'", "-").replace(" ", "-")
    replacements = {
        "é": "e", "è": "e", "ê": "e", "à": "a", "â": "a",
        "ç": "c", "î": "i", "ï": "i", "ô": "o", "ù": "u", "û": "u",
    }
    for k, v in replacements.items():
        filename = filename.replace(k, v)
    filename = filename.lower().strip("-").replace("--", "-")
    return f"{filename}.png"


def explain_openai_error(e: Exception, context: str = ""):
    print("\n====== OPENAI ERROR ======")
    if context:
        print(f"Context: {context}")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {getattr(e, 'message', None) or str(e)}")
    print("====== END ERROR ======\n")


def build_prompt(expr: str) -> str:
    return (
        f"Photorealistic illustration of the French expression '{expr}'. "
        f"Depict its meaning visually in a clear, simple way. "
        f"Use a {BACKGROUND}, balanced lighting, no text or captions."
    )


def generate_image(client: OpenAI, prompt: str, size: str = IMAGE_SIZE) -> bytes:
    """Generate and return image bytes."""
    result = client.images.generate(model=MODEL, prompt=prompt, size=size)
    return base64.b64decode(result.data[0].b64_json)

def build_html_page(expr: str, png: str, mp3: str, examples_html: str, footer_html: str) -> str:
    """Generate full HTML content including footer.html."""
    title = expr
    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{title}</title>\n"
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">\n'
        "  <style>\n"
        "    body {\n"
        "      font-family: Helvetica, Arial, sans-serif;\n"
        "      background-color: #fff;\n"
        "      margin-top: 40px;\n"
        "      text-align: center;\n"
        "    }\n"
        "    img.card-image {\n"
        "      max-width: 300px;\n"
        "      margin: 20px auto;\n"
        "      display: block;\n"
        "    }\n"
        "    .examples-block {\n"
        "      margin-top: 10px; /* reduced vertical gap */\n"
        "      margin-bottom: 0; /* remove extra space above footer */\n"
        "    }\n"
        "    footer {\n"
        "      margin-top: 10px; /* minimal space above footer */\n"
        "    }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{title}</h1>\n"
        f'  <img src="{png}" alt="{title}" class="card-image img-fluid">\n'
        "  <p>\n"
        "    <audio controls>\n"
        f'      <source src="{mp3}" type="audio/mpeg">\n'
        "      Votre navigateur ne supporte pas la lecture audio.\n"
        "    </audio>\n"
        "  </p>\n"
        f'  <div class="examples-block">\n{examples_html}\n  </div>\n'
        f"{footer_html}\n"
        "</body>\n</html>\n"
    )

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-single.py \"french expression\"")
        sys.exit(1)

    expr = sys.argv[1]
    png_path = Path(generate_filename(expr))
    base = png_path.stem
    mp3_path = Path(f"{base}.mp3")
    html_path = Path(f"{base}.html")

    print(f"→ Generating: {expr}")
    client = OpenAI(api_key=load_api_key())

    # 1️⃣ Image
    if png_path.exists():
        print(f"✔ PNG already exists: {png_path}")
    else:
        print("⏳ Generating image...")
        try:
            img = generate_image(client, build_prompt(expr))
            png_path.write_bytes(img)
            print(f"✅ Saved {png_path}")
            subprocess.run(["python3", "resize_png.py", str(png_path), "64"])
        except Exception as e:
            explain_openai_error(e, "image")
            sys.exit(2)

    # 2️⃣ Audio
    if mp3_path.exists():
        print(f"✔ MP3 already exists: {mp3_path}")
    else:
        print("⏳ Generating MP3...")
        subprocess.run(
            ["python3", "make_mp3_single.py", base, "clear, natural, use a calm woman's French voice", expr],
            check=False,
        )

    # 3️⃣ Examples
    print("⏳ Generating French examples...")
    examples_proc = subprocess.run(
        ["python3", "generate-french-examples.py", "3", expr],
        capture_output=True,
        text=True,
    )
    examples_html = examples_proc.stdout.strip() if examples_proc.returncode == 0 else "<!-- examples failed -->"

    # 4️⃣ Include footer.html
    footer_path = Path("footer.html")
    footer_html = footer_path.read_text(encoding="utf-8") if footer_path.exists() else "<!-- footer missing -->"

    # 5️⃣ Write HTML page
    html_content = build_html_page(expr, png_path.name, mp3_path.name, examples_html, footer_html)
    html_path.write_text(html_content, encoding="utf-8")
    print(f"✅ Wrote HTML page: {html_path}")


if __name__ == "__main__":
    main()

