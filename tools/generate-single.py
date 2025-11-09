#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate-single.py

Generate a single image, MP3, and HTML flash card for a French word or idiom.

Usage:
  python3 generate-single.py [--only-mp3] [--trial-run] "french expression"
"""

import os
import sys
import base64
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

MODEL = "gpt-image-1"
IMAGE_SIZE = "1024x1024"
BACKGROUND = "plain white background"


def load_api_key() -> str:
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


def safe_filename_from_text(text: str) -> str:
    """Convert text to a filesystem-safe name: replace spaces, quotes, and slashes."""
    safe = text.strip().replace(" ", "-").replace("'", "-").replace("/", "-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe


def generate_filename(french_expression: str) -> str:
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
    result = client.images.generate(model=MODEL, prompt=prompt, size=size)
    return base64.b64decode(result.data[0].b64_json)


def build_html_page(expr: str, png: str, mp3: str, examples_html: str, footer_html: str) -> str:
    page_title = "Nommez Celle Image"
    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{page_title}</title>\n"
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">\n'
        "  <style>\n"
        "    body { font-family: Helvetica, Arial, sans-serif; background-color: #fff; margin-top: 40px; text-align: center; }\n"
        "    img.card-image { max-width: 300px; margin: 20px auto; display: block; }\n"
        "    .examples-block { margin-top: 10px; margin-bottom: 0; }\n"
        "    footer { margin-top: 10px; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{page_title}</h1>\n"
        f'  <img src="{png}" alt="{page_title}" class="card-image img-fluid">\n'
        "  <p><button id=\"show-answer-btn\" class=\"btn btn-primary\">Clique pour la réponse</button></p>\n"
        '  <div id="answer-section" style="display:none; margin-top: 20px;">\n'
        f"    <h2>{expr}</h2>\n"
        "    <p><audio controls>\n"
        f'      <source src="{mp3}" type="audio/mpeg">\n'
        "      Votre navigateur ne supporte pas la lecture audio.\n"
        "    </audio></p>\n"
        f'    <div class="examples-block">\n{examples_html}\n    </div>\n'
        f"{footer_html}\n"
        "  </div>\n"
        "  <script>\n"
        "    document.addEventListener('DOMContentLoaded', function() {\n"
        "      var btn = document.getElementById('show-answer-btn');\n"
        "      var section = document.getElementById('answer-section');\n"
        "      if (btn && section) {\n"
        "        btn.addEventListener('click', function() {\n"
        "          section.style.display = 'block';\n"
        "          btn.style.display = 'none';\n"
        "        });\n"
        "      }\n"
        "    });\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate a French flashcard (image, mp3, html).")
    parser.add_argument("expression", help="French expression to generate")
    parser.add_argument("--only-mp3", action="store_true", help="Only generate/rebuild the MP3, skipping others")
    parser.add_argument("--trial-run", action="store_true", help="Show what would be done without executing")
    args = parser.parse_args()

    expr = args.expression
    safe_text_name = safe_filename_from_text(expr)
    png_path = Path(generate_filename(expr))
    base = png_path.stem
    mp3_path = Path(f"{safe_text_name}.mp3")
    html_path = Path(f"{base}.html")

    print(f"→ Processing: {expr}")

    def run_subprocess(cmd):
        if args.trial_run:
            print(f"[TRIAL] Would run: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        else:
            return subprocess.run(cmd, capture_output=True, text=True)

    # --- ONLY MP3 MODE ---
    if args.only_mp3:
        print("🎵 Only-MP3 mode enabled.")
        cmd = ["python3", "make_mp3_single.py", safe_text_name, "clear, natural, use a calm woman's French voice", expr]
        run_subprocess(cmd)
        print(f"✅ MP3 regenerated as {safe_text_name}.mp3 for: {expr}")
        sys.exit(0)

    # --- Normal full generation ---
    client = OpenAI(api_key=load_api_key())

    # 1️⃣ Image
    if png_path.exists():
        print(f"✔ PNG already exists: {png_path}")
    else:
        print("⏳ Generating image...")
        if args.trial_run:
            print(f"[TRIAL] Would generate image for '{expr}'")
        else:
            try:
                img = generate_image(client, build_prompt(expr))
                png_path.write_bytes(img)
                print(f"✅ Saved {png_path}")
                subprocess.run(["python3", "resize_png.py", str(png_path), "64"])
            except Exception as e:
                explain_openai_error(e, "image")
                sys.exit(2)

    # 2️⃣ Audio
    print("⏳ Generating MP3...")
    run_subprocess(["python3", "make_mp3_single.py", safe_text_name,
                    "clear, natural, use a calm woman's French voice", expr])

    # 3️⃣ Examples
    print("⏳ Generating French examples...")
    examples_proc = run_subprocess(["python3", "generate-french-examples.py", "3", expr])
    examples_html = examples_proc.stdout.strip() if examples_proc.returncode == 0 else "<!-- examples failed -->"

    # 4️⃣ Footer include
    footer_path = Path("footer.html")
    footer_html = footer_path.read_text(encoding="utf-8") if footer_path.exists() else "<!-- footer missing -->"

    # 5️⃣ Write HTML
    html_content = build_html_page(expr, png_path.name, mp3_path.name, examples_html, footer_html)
    if args.trial_run:
        print(f"[TRIAL] Would write HTML file: {html_path}")
    else:
        html_path.write_text(html_content, encoding="utf-8")
        print(f"✅ Wrote HTML page: {html_path}")


if __name__ == "__main__":
    main()

