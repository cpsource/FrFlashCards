#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make-flash-card-simple.py

Usage:
  python3 make-flash-card-simple.py "French expression"

Takes one argument: the French name of the flash card.
- Builds a base name from the argument:
    * spaces -> '-'
    * apostrophes (') -> '-'
    * accents removed
    * everything lowercased
- Creates an HTML file: <base-name>.html
- Uses <base-name>.png for the image
- Uses <base-name>.mp3 for the audio
- At the <footer> section, imports footer.html
"""

import sys
import unicodedata
from pathlib import Path
import html


def make_basename(french_name: str) -> str:
    """
    Convert the French expression into a safe base name:
      - strip leading/trailing spaces
      - lowercase
      - remove accents
      - replace spaces with '-'
      - replace apostrophes with '-'
      - keep only a-z, 0-9, and '-'
      - collapse multiple '-' and strip at ends
    """
    s = french_name.strip().lower()
    # Remove accents
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))

    # Replace spaces and apostrophes
    s = s.replace("'", "-").replace(" ", "-")

    # Keep only safe characters
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    s = "".join(c for c in s if c in allowed)

    # Collapse multiple dashes
    while "--" in s:
        s = s.replace("--", "-")

    # Strip leading/trailing dashes
    s = s.strip("-")

    return s


def build_html(french_text: str, base_name: str) -> str:
    """
    Build the HTML content for the flash card,
    modeled on the provided example file.
    """
    title_text = french_text
    escaped_title = html.escape(title_text, quote=True)

    img_src = f"{base_name}.png"
    mp3_src = f"{base_name}.mp3"

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{escaped_title}</title>
  <link rel="stylesheet"
        href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <style>
    body {{
      text-align: center;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      background-color: #fffdfd;
      margin-top: 40px;
    }}
    img {{
      max-width: 300px;
      margin: 20px auto;
    }}
  </style>
</head>
<body>
  <h1>{escaped_title}</h1>
  <img src="{img_src}" alt="{escaped_title}" class="img-fluid">

  <p class="lead">Signification : (ajoutez la signification ici.)</p>

  <audio controls>
    <source src="{mp3_src}" type="audio/mpeg">
    Votre navigateur ne supporte pas la lecture audio.
  </audio>

  <hr>
  <a href="../index.html" class="btn btn-secondary">↩️ Retour</a>

  <footer>
    {{% include "footer.html" %}}
  </footer>
</body>
</html>
"""
    return html_content


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 make-flash-card-simple.py \"French expression\"")
        sys.exit(1)

    french_text = sys.argv[1]
    base_name = make_basename(french_text)
    html_filename = f"{base_name}.html"

    html_content = build_html(french_text, base_name)

    out_path = Path(html_filename)
    out_path.write_text(html_content, encoding="utf-8")

    print(f"✅ Created flash card HTML: {out_path.resolve()}")
    print(f"   French text: {french_text}")
    print(f"   Base name : {base_name}")
    print(f"   Image     : {base_name}.png")
    print(f"   Audio     : {base_name}.mp3")


if __name__ == "__main__":
    main()

