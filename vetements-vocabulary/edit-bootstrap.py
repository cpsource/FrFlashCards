#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
edit-footer.py

For each *.html file in the current directory:

  1. Remove the first <footer>...</footer> block.
  2. Remove the next <style>...</style> block that follows.
  3. Remove the Bootstrap JS block:
        <!-- Bootstrap JS (if not already loaded) -->
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
  4. Insert the *actual contents* of ../templates/partials/footer.html
     where the <footer> block began.
"""

import re
from pathlib import Path

FOOTER_PATH = Path("../templates/partials/footer.html")


def load_footer() -> str:
    """Load the actual footer HTML to inject."""
    if not FOOTER_PATH.exists():
        raise FileNotFoundError(f"Missing footer file: {FOOTER_PATH}")
    return FOOTER_PATH.read_text(encoding="utf-8")


def remove_block(text: str, start_pat: str, end_pat: str) -> str:
    """Remove the first block between start_pat and end_pat (inclusive)."""
    pattern = re.compile(start_pat + r".*?" + end_pat, re.DOTALL | re.IGNORECASE)
    return re.sub(pattern, "", text, count=1)


def remove_bootstrap_js_block(text: str) -> str:
    """Remove the specific Bootstrap JS block."""
    pattern = re.compile(
        r'<!--\s*Bootstrap JS \(if not already loaded\)\s*-->\s*'
        r'<script src="https://code\.jquery\.com/jquery-3\.5\.1\.slim\.min\.js"></script>\s*'
        r'<script src="https://cdn\.jsdelivr\.net/npm/bootstrap@4\.5\.2/dist/js/bootstrap\.bundle\.min\.js"></script>\s*',
        re.IGNORECASE | re.DOTALL,
    )
    return re.sub(pattern, "", text, count=1)


def process_html_file(path: Path, footer_html: str):
    """Process and modify one HTML file."""
    text = path.read_text(encoding="utf-8")

    # 1. Remove <footer>...</footer>
    match_footer = re.search(r"<footer.*?</footer>", text, re.DOTALL | re.IGNORECASE)
    if not match_footer:
        print(f"[SKIP] No <footer> block found in {path.name}")
        return

    start_idx = match_footer.start()
    end_idx = match_footer.end()

    before = text[:start_idx]
    after = text[end_idx:]

    # 2. Remove the next <style>...</style> block
    after = remove_block(after, r"<style.*?>", r"</style>")

    # 3. Remove the Bootstrap JS block
    after = remove_bootstrap_js_block(after)

    # 4. Insert the new footer
    new_text = before + footer_html.strip() + "\n" + after

    path.write_text(new_text, encoding="utf-8")
    print(f"[OK] Updated {path.name}")


def main():
    footer_html = load_footer()
    html_files = sorted(Path(".").glob("*.html"))
    if not html_files:
        print("No .html files found in current directory.")
        return

    for f in html_files:
        process_html_file(f, footer_html)


if __name__ == "__main__":
    main()

