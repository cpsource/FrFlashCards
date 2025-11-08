#!/usr/bin/env python3
"""
build_site.py

Build static HTML from Jinja templates.

Now this:
  - Builds hint pages listed in hints/hints.json
  - Builds static top-level pages like about.html, index.html, etc.
  - Builds vocab pages from templates/vocab/** into vocab/**
"""

import json
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
HINTS_DIR = BASE_DIR / "hints"
HINTS_JSON = HINTS_DIR / "hints.json"
OUTPUT_DIR = BASE_DIR  # where to write about.html, index.html, vocab/, etc.

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

    pages = ["about.html", "index.html"]  # extend as needed
    for page in pages:
        tpl_name = page
        out_path = OUTPUT_DIR / page

        print(f"Rendering {tpl_name} -> {out_path}")
        template = env.get_template(tpl_name)
        html = template.render(**ctx_base)
        out_path.write_text(html, encoding="utf-8")
        print(f"  ✓ wrote {out_path}")

def build_vocab_pages():
    """
    Render all templates under templates/vocab/**.html
    into vocab/**.html in the output directory, with prev/next links.
    """
    vocab_root = TEMPLATES_DIR / "vocab"
    if not vocab_root.exists():
        print(f"⚠️  {vocab_root} not found, skipping vocab.")
        return

    # Find all .html files under templates/vocab (recursively)
    tpl_files = sorted(vocab_root.rglob("*.html"))
    print(f"Building {len(tpl_files)} vocab page(s) from {vocab_root}.")

    # Build a list of URL paths for ordering, e.g. "vocab/greetings/bonjour.html"
    rel_template_names = [
        str(p.relative_to(TEMPLATES_DIR)).replace("\\", "/") for p in tpl_files
    ]

    ctx_base = {"current_year": datetime.now().year}

    for idx, tpl_path in enumerate(tpl_files):
        rel_tpl = str(tpl_path.relative_to(TEMPLATES_DIR)).replace("\\", "/")
        rel_v = tpl_path.relative_to(vocab_root)  # e.g. greetings/bonjour.html

        # Compute prev/next URLs (relative URLs under /vocab/)
        prev_url = None
        next_url = None

        if idx > 0:
            prev_rel_tpl = rel_template_names[idx - 1]  # "vocab/…/prev.html"
            prev_rel_v = Path(prev_rel_tpl).relative_to("vocab")
            prev_url = f"/vocab/{prev_rel_v.as_posix()}"

        if idx < len(tpl_files) - 1:
            next_rel_tpl = rel_template_names[idx + 1]
            next_rel_v = Path(next_rel_tpl).relative_to("vocab")
            next_url = f"/vocab/{next_rel_v.as_posix()}"

        tpl_name = rel_tpl               # e.g. "vocab/greetings/bonjour.html"
        out_path = OUTPUT_DIR / "vocab" / rel_v  # vocab/greetings/bonjour.html

        print(f"  Rendering {tpl_name} -> {out_path}")
        template = env.get_template(tpl_name)

        ctx = dict(ctx_base)
        ctx["prev_url"] = prev_url
        ctx["next_url"] = next_url

        html = template.render(**ctx)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"    ✓ wrote {out_path} (prev={prev_url}, next={next_url})")

def main():
    print(f"Templates dir: {TEMPLATES_DIR}")
    print(f"Hints dir:     {HINTS_DIR}")
    build_hints()
    build_static_pages()
    build_vocab_pages()
    print("Done.")

if __name__ == "__main__":
    main()

