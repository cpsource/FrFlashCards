#!/usr/bin/env python3
"""
update_hints.py

Usage:
    python update_hints.py L-heure-du-conte-hint.html

This script:
- Reads hints.html in the same directory as the given file.
- Adds a new row to the hints table.
- Updates the "Total Resources" count.
"""

import sys
import re
from pathlib import Path
from html import unescape


def extract_title_and_description(hint_path: Path):
    """Extract <title> and the first <p> as description from the hint HTML."""
    html = hint_path.read_text(encoding="utf-8")

    # ---- Title ----
    m_title = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m_title:
        title = m_title.group(1).strip()
        title = re.sub(r"\s+", " ", title)
        # Strip trailing " - frflashy.com" or similar if present
        title = re.sub(r"\s*[-–]\s*frflashy\.com\s*$", "", title, flags=re.IGNORECASE)
    else:
        title = hint_path.stem  # fallback

    # ---- Description (first <p>) ----
    m_p = re.search(r"<p[^>]*>(.*?)</p>", html, re.IGNORECASE | re.DOTALL)
    if m_p:
        raw = m_p.group(1)
        # remove any tags inside the <p>...</p>
        text = re.sub(r"<.*?>", "", raw)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        # short summary
        max_len = 160
        if len(text) > max_len:
            cut = text[:max_len]
            # avoid cutting mid-word
            if " " in cut:
                cut = cut.rsplit(" ", 1)[0]
            text = cut + "…"
        description = text
    else:
        description = "Additional explanation and examples."

    return title, description


def update_hints_index(hints_index: Path, new_hint: Path):
    """Insert new hint row and update stats in hints.html."""
    html = hints_index.read_text(encoding="utf-8")

    # Count existing resources by number of ".resource-number" divs
    existing_count = html.count('class="resource-number"')
    if existing_count <= 0:
        raise RuntimeError("Could not find any existing resource-number entries in hints.html")

    new_number = existing_count + 1

    title, description = extract_title_and_description(new_hint)

    # Build new <tr> block (matching existing formatting/indentation)
    new_row = f"""
                    <tr>
                        <td style="text-align: center;">
                            <div class="resource-number">{new_number}</div>
                        </td>
                        <td>
                            <a href="{new_hint.name}" class="resource-title">{title}</a>
                            <div class="resource-description">{description}</div>
                        </td>
                    </tr>"""

    # Insert new row before closing </tbody>
    tbody_close_pos = html.rfind("</tbody>")
    if tbody_close_pos == -1:
        raise RuntimeError("Could not find </tbody> in hints.html")

    html = html[:tbody_close_pos] + new_row + "\n" + html[tbody_close_pos:]

    # Update "Total Resources" stat-number (first numeric stat-number before 'Total Resources')
    # Pattern: <div class="stat-number">3</div><div class="stat-label">Total Resources
    pattern = r'(<div class="stat-number">)\s*\d+\s*(</div>\s*<div class="stat-label">Total Resources)'
    html, replaced = re.subn(pattern, rf"\g<1>{new_number}\g<2>", html, count=1)
    if replaced == 0:
        print("Warning: could not update the Total Resources stat-number.")

    hints_index.write_text(html, encoding="utf-8")
    print(f"Added hint #{new_number}: {title}")
    print(f"File: {new_hint.name}")
    print(f"Updated: {hints_index.name}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_hints.py <new_hint_html_file>")
        sys.exit(1)

    new_hint = Path(sys.argv[1]).resolve()
    if not new_hint.exists():
        print(f"Error: file not found: {new_hint}")
        sys.exit(1)

    # Assume hints.html is in the same directory as the new hint file
    hints_index = new_hint.parent / "hints.html"
    if not hints_index.exists():
        print(f"Error: hints.html not found in {new_hint.parent}")
        sys.exit(1)

    update_hints_index(hints_index, new_hint)


if __name__ == "__main__":
    main()

