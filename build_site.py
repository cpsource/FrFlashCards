#!/usr/bin/env python3
"""
build_site.py

Build static HTML from Jinja templates.

Now this:
  - Builds hint pages listed in hints/hints.json
  - Builds static top-level pages like about.html, index.html, etc.
"""

import json
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
HINTS_DIR = BASE_DIR / "hints"
HINTS_JSON = HINTS_DIR / "hints.json"
OUTPUT_DIR = BASE_DIR  # where to write about.html, index.html, etc.

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

def build_hints():
    if not HINTS_JSON.exists():
        print(f"⚠️  {HINTS_JSON} not found, skipping hints.")
        return

    data = json.loads(HINTS_JSON.read_text(encoding="utf-8"))
    print(f"Building {len(data)} hint page(s) from {HINTS_JSON}.")

    ctx_base = {"current_year": datetime.now().year}

    for hint in data:
        fname = hint["file"]          # e.g. "L-heure-du-conte-hint.html"
        tpl_name = f"hints/{fname}"   # templates/hints/L-heure-du-conte-hint.html
        out_path = HINTS_DIR / fname  # hints/L-heure-du-conte-hint.html

        print(f"  Rendering {tpl_name} -> {out_path}")

        template = env.get_template(tpl_name)
        html = template.render(**ctx_base, hint=hint)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"    ✓ wrote {out_path}")

def build_static_pages():
    """
    Render static templates like about.html, index.html, etc.
    These should live in templates/ and NOT require dynamic JSON.
    """
    ctx_base = {"current_year": datetime.now().year}

    pages = ["about.html"]  # extend this list as you add new static pages
    for page in pages:
        tpl_name = page
        out_path = OUTPUT_DIR / page

        print(f"Rendering {tpl_name} -> {out_path}")
        template = env.get_template(tpl_name)
        html = template.render(**ctx_base)
        out_path.write_text(html, encoding="utf-8")
        print(f"  ✓ wrote {out_path}")

def main():
    print(f"Templates dir: {TEMPLATES_DIR}")
    print(f"Hints dir:     {HINTS_DIR}")
    build_hints()
    build_static_pages()
    print("Done.")

if __name__ == "__main__":
    main()

