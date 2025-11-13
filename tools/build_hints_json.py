#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_hints_json.py

Scan Jinja/HTML hint templates under templates/hints/ and build a hints.json
file that build_site.py can consume.

Expected by build_site.py:
  hints = json.load(open("hints/hints.json"))
  for hint in hints:
      fname = hint["file"]   # e.g. "L-heure-du-conte-hint.html"

So our output is a top-level JSON *list* of dicts like:
[
  {
    "file": "L-heure-du-conte-hint.html",
    "title": "L’heure du conte",
    "summary": "..."
  },
  ...
]

Usage:

  cd /var/www/FrFlashCards
  python3 build_hints_json.py

"""

import argparse
import json
import pathlib
import re
import sys
import html
from typing import Optional


def extract_tag_text(source: str, tag: str) -> Optional[str]:
    """
    Pull out inner text of the first <tag>...</tag>.
    Very simple: strips nested tags, unescapes HTML entities, trims whitespace.
    """
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    m = re.search(pattern, source, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    inner = m.group(1)
    # Strip other tags
    inner = re.sub(r"<[^>]+>", "", inner)
    inner = html.unescape(inner)
    inner = inner.strip()
    return inner or None


def extract_title(html_text: str, fallback: str) -> str:
    """Try <h1>, then <title>. If nothing, fall back to provided string."""
    title = extract_tag_text(html_text, "h1")
    if not title:
        title = extract_tag_text(html_text, "title")
    return title or fallback


def extract_summary(html_text: str) -> Optional[str]:
    """Use the first <p> as a short description/summary, if present."""
    return extract_tag_text(html_text, "p")


def build_hints_list(templates_dir: pathlib.Path) -> list[dict]:
    """
    Walk templates_dir for *.html and build hint metadata.

    Returns a list of dicts, each with at least:
      - file    : filename, e.g. "L-heure-du-conte-hint.html"
      - title   : human-friendly title
      - summary : first paragraph (optional, may be empty string)
    """
    if not templates_dir.exists() or not templates_dir.is_dir():
        print(f"[FATAL] templates dir not found: {templates_dir}", file=sys.stderr)
        sys.exit(1)

    hints: list[dict] = []

    html_files = sorted(templates_dir.glob("*.html"))
    if not html_files:
        print(f"[WARN] No .html files found in {templates_dir}", file=sys.stderr)

    for f in html_files:
        fname = f.name                     # e.g. "L-heure-du-conte-hint.html"
        hint_id = f.stem                   # e.g. "L-heure-du-conte-hint"

        try:
            text = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[WARN] Could not read {f}: {e}", file=sys.stderr)
            continue

        title = extract_title(text, fallback=hint_id)
        summary = extract_summary(text) or ""

        hints.append(
            {
                "file": fname,
                "title": title,
                "summary": summary,
            }
        )

        print(f"[OK] Added hint: file={fname!r}, title={title!r}")

    return hints


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build hints/hints.json from templates/hints/*.html"
    )
    parser.add_argument(
        "--templates-dir",
        default="templates/hints",
        help="Directory containing hint templates (default: templates/hints)",
    )
    parser.add_argument(
        "--output",
        default="hints/hints.json",
        help="Output JSON path (default: hints/hints.json)",
    )
    args = parser.parse_args()

    templates_dir = pathlib.Path(args.templates_dir)
    output_path = pathlib.Path(args.output)

    hints_list = build_hints_list(templates_dir)

    # Ensure parent dir exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(hints_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n[SUMMARY]")
    print(f"  total hints : {len(hints_list)}")
    print(f"  output file : {output_path.resolve()}")


if __name__ == "__main__":
    main()

