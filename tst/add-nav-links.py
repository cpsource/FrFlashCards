#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
add-nav-links.py

Scans all .html flash cards in the current directory and ensures that each one
has exactly ONE correct pair of navigation links (Prev / Next), placed
immediately above the footer. Any old nav block is removed before inserting
the updated one.

Additionally:
  - If there is a preexisting index.html that is a *symlink*, it is removed.
  - The first flash card (alphabetically) is then soft-linked to index.html.
"""

import re
from pathlib import Path


def main():
    # ------------------------------------------------------------
    # 1. Collect card files (excluding index.html and footer.html)
    # ------------------------------------------------------------
    cards = sorted(
        f for f in Path(".").glob("*.html")
        if f.name not in {"index.html", "footer.html"}
    )

    if not cards:
        print("No flash card HTML files found.")
        return

    cards_list = [card.name for card in cards]
    print(f"Found {len(cards)} cards. Updating navigation...")

    # ------------------------------------------------------------
    # 2. Handle index.html symlink
    #    - If existing index.html is a symlink, remove it.
    #    - Then create a symlink from index.html to the first card.
    # ------------------------------------------------------------
    index_path = Path("index.html")
    if index_path.exists() or index_path.is_symlink():
        if index_path.is_symlink():
            print("Found existing symlink index.html → removing it.")
            index_path.unlink()
        else:
            print("index.html exists and is not a symlink → leaving it as-is.")
    # Only create symlink if index.html does not exist now
    if not index_path.exists():
        first_card = cards[0].name
        print(f"Creating symlink: index.html -> {first_card}")
        index_path.symlink_to(first_card)

    # ------------------------------------------------------------
    # 3. Add / update Prev / Next navigation in each card
    # ------------------------------------------------------------
    for i, card in enumerate(cards):
        prev_link = cards_list[i - 1] if i > 0 else None
        next_link = cards_list[i + 1] if i < len(cards) - 1 else None

        text = card.read_text(encoding="utf-8")

        # Remove any existing nav block inserted previously
        text = re.sub(
            r"<hr>\s*<p>.*?(?=</footer>|</body>)",  # find old nav area
            "",
            text,
            flags=re.DOTALL,
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

        card.write_text(text, encoding="utf-8")
        print(f"✔ Updated {card.name}")

    print("✅ All navigation links updated.")


if __name__ == "__main__":
    main()

