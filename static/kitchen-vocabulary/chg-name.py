#!/usr/bin/env python3
"""
Usage:
    python make_rename_script.py vocab.csv

Given a CSV file, produces a bash script called rename.sh that contains
mv commands to rename:

  first_col -> second_col

for both .mp3 and .png, with these transformations:

- First column:
    spaces → underscores (_)

- Second column:
    leading l'XXX or l’XXX → l-XXX
    spaces → hyphens (-)
"""

import csv
import sys
import os
import re
from pathlib import Path


def make_base_from_first(col1: str) -> str:
    """First column: replace spaces with underscores."""
    col1 = col1.strip()
    return col1.replace(" ", "_")


def make_base_from_second(col2: str) -> str:
    """
    Second column:
      - replace leading l'XXX or l’XXX with l-XXX (case-insensitive)
      - replace spaces with hyphens
    """
    col2 = col2.strip()

    # Handle l'xxx or l’xxx at start (ASCII or curly apostrophe)
    col2 = re.sub(r"^l['’]", "l-", col2, flags=re.IGNORECASE)

    # Replace spaces with hyphens
    col2 = col2.replace(" ", "-")

    return col2


def main():
    if len(sys.argv) != 2:
        print("Usage: python make_rename_script.py <csv-file>", file=sys.stderr)
        sys.exit(1)

    csv_path = Path(sys.argv[0]).parent / sys.argv[1] if not os.path.isabs(sys.argv[1]) else Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    out_path = Path("rename.sh")

    lines = ["#!/bin/bash", "set -e", "", "# Auto-generated rename commands"]

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue

            # Skip header if it looks like one
            if i == 0 and any(col.lower() in ("english", "french") for col in row):
                continue

            if len(row) < 2:
                continue  # not enough columns

            col1 = row[0].strip()
            col2 = row[1].strip()
            if not col1 or not col2:
                continue

            base1 = make_base_from_first(col1)
            base2 = make_base_from_second(col2)

            # Add mv commands for .mp3 and .png
            lines.append(f'# {col1} -> {col2}')
            lines.append(f'mv "{base1}.mp3" "{base2}.mp3"')
            lines.append(f'mv "{base1}.png" "{base2}.png"')
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path} with rename commands.")


if __name__ == "__main__":
    main()

