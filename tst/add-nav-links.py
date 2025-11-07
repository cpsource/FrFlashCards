#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
add-nav-links.py

Scans all .html flash cards in the current directory and ensures that each one
has exactly ONE correct pair of navigation links (Prev / Next), placed
immediately above the footer. Any old nav block is removed before inserting
the updated one.
"""

import re
from pathlib import Path

def main():
    cards = sorted(
        f for f in Path(".").glob("*.html")
        if f.name not in {"index.html", "footer.html"}
    )

    if not cards:
        print("No flash card HTML files found.")
        return

    cards_list = [card.name for card in cards]
    print(f"Found {len(cards)} cards. Updating navigation...")

    for i, card in enumerate(cards):
        prev_link = cards_list[i - 1] if i > 0 else None
        next_link = cards_list[i + 1] if i < len(cards) - 1 else None

        text = Path(card).read_text(encoding="utf-8")

        # Remove any existing nav block inserted previously
        text = re.sub(
            r"<hr>\s*<p>.*?(?=</footer>|</body>)",  # find old nav area
            "",
            text,
            flags=re.DOTALL
        )

        # Build new nav HTML
        nav_html = "<hr>\n<p>\n"
        if prev_link:
            nav_html += f'  <a href="{prev_link}" class="btn btn-secondary">&larr; Précédent</a>\n'
        if next_link:
            nav_html += f'  <a href="{next_link}" class="btn btn-primary">Suivant &rarr;</a>\n'
        nav_html += "</p>\n"

        # Insert just before </footer> if present, else before </body>
        if "</footer>" in text:
            text = text.replace("</footer>", f"{nav_html}</footer>")
        elif "</body>" in text:
            text = text.replace("</body>", f"{nav_html}</body>")
        else:
            text += f"\n{nav_html}\n"

        Path(card).write_text(text, encoding="utf-8")
        print(f"✔ Updated {card.name}")

    print("✅ All navigation links updated.")


if __name__ == "__main__":
    main()

