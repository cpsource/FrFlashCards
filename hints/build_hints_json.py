#!/usr/bin/env python3
"""
build_hints_json.py

Scans the current hints directory (the directory this file is in)
for .html files and builds a JSON index (hints.json) containing
title, filename, and description for each hint page.

Usage:
    python3 build_hints_json.py
"""

import json
import re
from pathlib import Path
from html import unescape

# --- CONFIG ---
BASE_DIR = Path(__file__).resolve().parent
# Your hint HTML files are in the same directory as this script:
HINTS_DIR = BASE_DIR
OUTPUT_FILE = BASE_DIR / "hints.json"


def debug(msg):
    print(f"[DEBUG] {msg}")


def extract_title_and_description(html_text, filename="<unknown>"):
    """Extract the <title> and first <p> content from a page."""
    # title
    title_match = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r"\s*[-–]\s*frflashy\.com\s*$", "", title, flags=re.IGNORECASE)
    else:
        title = "Untitled"
        debug(f"No <title> found in {filename}, using 'Untitled'.")

    # description
    desc_match = re.search(r"<p[^>]*>(.*?)</p>", html_text, re.IGNORECASE | re.DOTALL)
    if desc_match:
        desc = re.sub(r"<.*?>", "", desc_match.group(1))
        desc = unescape(desc)
        desc = re.sub(r"\s+", " ", desc).strip()
    else:
        desc = ""
        debug(f"No <p> found in {filename}, description left empty.")

    debug(
        f"Extracted from {filename}: "
        f"title='{title}', desc='{desc[:60]}{'…' if len(desc) > 60 else ''}'"
    )
    return title, desc


def build_json():
    """Scan the hints directory and produce hints.json."""
    debug(f"BASE_DIR     = {BASE_DIR}")
    debug(f"HINTS_DIR    = {HINTS_DIR}")
    debug(f"OUTPUT_FILE  = {OUTPUT_FILE}")

    hints = []
    if not HINTS_DIR.exists():
        debug("HINTS_DIR does not exist! No hints will be found.")
    else:
        html_files = sorted(HINTS_DIR.glob("*.html"))
        debug(f"Found {len(html_files)} .html files in hints directory.")
        for html_file in html_files:
            debug(f"Checking file: {html_file.name}")
            if html_file.name == "hints.html":
                debug("  Skipping hints.html (index page).")
                continue

            try:
                html = html_file.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                debug(f"  ERROR reading {html_file.name}: {e}")
                continue

            title, desc = extract_title_and_description(html, filename=html_file.name)

            hints.append({
                "title": title,
                "file": html_file.name,
                "description": desc,
            })

    debug(f"Total hints to write: {len(hints)}")

    json_text = json.dumps(hints, indent=2, ensure_ascii=False)
    debug(f"JSON text length (chars): {len(json_text)}")

    try:
        OUTPUT_FILE.write_text(json_text, encoding="utf-8")
        debug(f"Wrote JSON to {OUTPUT_FILE}")
        debug(f"Final file size (bytes): {OUTPUT_FILE.stat().st_size}")
    except Exception as e:
        debug(f"ERROR writing to {OUTPUT_FILE}: {e}")
        raise

    print(f"✅ Built {OUTPUT_FILE} with {len(hints)} entries.")


if __name__ == "__main__":
    build_json()

