#!/usr/bin/env python3
"""
Builds an index page (verbs.html) for your A1 verb conjugation pages.

Usage:
    python build_verbs_index.py [directory]

If no directory is given, uses the current working directory.
It scans for *.html files (excluding verbs.html) and generates a themed
index with proper relative links. The script tries to read <title> from
each page; if not found, it falls back to the filename stem.
"""
from __future__ import annotations
import argparse
import os
import sys
import re
from datetime import datetime
from html import escape

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)


def sniff_title(html_path: str) -> str:
    """Return a nice display title for an HTML file.
    Prefer <title>, else first <h1>, else the filename stem.
    """
    name = os.path.splitext(os.path.basename(html_path))[0]
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(8192)  # enough to cover <head>
    except Exception:
        return name

    m = TITLE_RE.search(head)
    if m:
        # Collapse whitespace
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        return t if t else name

    m = H1_RE.search(head)
    if m:
        t = re.sub(r"<[^>]+>", "", m.group(1))  # strip tags
        t = re.sub(r"\s+", " ", t).strip()
        return t if t else name

    return name


def find_html_pages(root: str) -> list[dict]:
    items = []
    for entry in os.listdir(root):
        if not entry.lower().endswith(".html"):
            continue
        if entry.lower() in {"verbs.html", "index.html"}:
            continue
        path = os.path.join(root, entry)
        if not os.path.isfile(path):
            continue
        title = sniff_title(path)
        mtime = os.path.getmtime(path)
        items.append({
            "file": entry,
            "title": title,
            "mtime": mtime,
        })
    # Sort alphabetically by display title (casefold for unicode-friendly sort)
    items.sort(key=lambda d: d["title"].casefold())
    return items


def render_index(items: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cards = []
    for it in items:
        title = escape(it["title"])
        href = escape(it["file"])  # relative link
        updated = datetime.fromtimestamp(it["mtime"]).strftime("%Y-%m-%d")
        cards.append(f"""
        <a class=card href="{href}">
          <div class=card-title>{title}</div>
          <div class=card-sub>Updated {updated}</div>
        </a>
        """)

    cards_html = "\n".join(cards) if cards else "<p class=empty>No verb pages found yet.</p>"

    return f"""<!doctype html>
<html lang=en>
<head>
  <meta charset=utf-8>
  <meta name=viewport content="width=device-width, initial-scale=1">
  <title>A1 Verbs – Index</title>
  <style>
    :root{{--bg:#0b0d10;--surface:#131720;--muted:#1b2130;--text:#e7ecf3;--sub:#a7b3c6;--accent:#6bd3ff}}
    html,body{{margin:0;padding:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,"Helvetica Neue",Arial,"Noto Sans",sans-serif}}
    .container{{max-width:980px;margin:28px auto;padding:0 16px}}
    h1{{font-size:clamp(1.6rem,2.6vw,2.2rem);margin:8px 0 6px}}
    p.lead{{color:var(--sub)}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin-top:18px}}
    .card{{display:block;background:linear-gradient(180deg,var(--surface),#0f131b);border:1px solid #1e2535;border-radius:14px;padding:14px;text-decoration:none;color:var(--text);transition:transform .12s ease, border-color .12s ease}}
    .card:hover{{transform:translateY(-2px);border-color:#2a3650}}
    .card-title{{font-weight:700;margin-bottom:6px}}
    .card-sub{{color:var(--sub);font-size:.9rem}}
    .footer{{margin-top:22px;color:var(--sub);font-size:.9rem}}
    .empty{{color:var(--sub)}}
    .small{{font-size:.9rem;color:var(--sub)}}
    .kbd{{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:.85rem;background:#0e1526;border:1px solid #27324b;border-radius:6px;padding:.1rem .35rem}}
  </style>
</head>
<body>
  <div class=container>
    <h1>🥖 A1 Verbs – Index</h1>
    <p class=lead>Auto‑generated on {escape(now)}. Click a card to open a verb page. Add more by dropping their <span class=kbd>.html</span> files in this folder.</p>
    <div class=grid>
      {cards_html}
    </div>
    <p class=footer>Tip: Keep individual pages named like <span class=kbd>etre.html</span>, <span class=kbd>avoir.html</span>, etc., or any name with a meaningful <span class=kbd>&lt;title&gt;</span>.</p>
  </div>
</body>
</html>"""


def write_verbs_html(target_dir: str, html: str) -> str:
    out_path = os.path.join(target_dir, "verbs.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build verbs.html index for verb pages")
    ap.add_argument("directory", nargs="?", default=os.getcwd(), help="Directory to scan (default: CWD)")
    args = ap.parse_args(argv)

    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        return 2

    items = find_html_pages(directory)
    html = render_index(items)
    out_path = write_verbs_html(directory, html)
    print(f"Wrote {out_path} with {len(items)} entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

