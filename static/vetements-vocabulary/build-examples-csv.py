#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_examples_from_vocab.py

Usage:
  python3 build_examples_from_vocab.py vocab.csv

Input CSV:
  col1: English name
  col2: French name
  col3: gender
  First row is a header and will be skipped.

For each row:
  - Adjust col2 by building a base name:
        spaces  -> '-'
        apostrophes (') -> '-'
        slashes (/) -> '-'
  - Open "<base-name>.txt" and read its first 3 non-empty lines (French examples)
  - For each of those 3 lines, write a row to examples.csv:

      col1: original French name (from col2)
      col2: French example line
      col3: English translation of that line (via OpenAI)

Output:
  examples.csv — created in the same directory as the input CSV.
  examples-error.log — errors and warnings written here.
"""

import csv
import sys
import os
from pathlib import Path

from openai import OpenAI

MODEL_TRANSLATE = "gpt-4o-mini"


def load_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        msg = "[FATAL] OPENAI_API_KEY not found in environment."
        print(msg, file=sys.stderr)
        raise SystemExit(1)
    return OpenAI(api_key=api_key)


def translate_line(client: OpenAI, french: str) -> str:
    """Translate a single French sentence into natural English."""
    resp = client.chat.completions.create(
        model=MODEL_TRANSLATE,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise and concise translator. "
                    "Translate the French sentence into natural English. "
                    "Return only the translation, nothing else."
                ),
            },
            {
                "role": "user",
                "content": french,
            },
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content or ""
    return content.strip()


def log(msg: str, fh):
    """Log message to stderr and to the given log file handle."""
    line = msg.rstrip()
    print(line, file=sys.stderr)
    if fh is not None:
        print(line, file=fh)


def make_base_name(french_name: str) -> str:
    """
    Build base name for .txt file from French name:
      - spaces -> '-'
      - apostrophes (') -> '-'
      - slashes (/) -> '-'
    """
    base = french_name
    base = base.replace(" / ", "-")
    base = base.replace("/", "-")
    base = base.replace("'", "-")
    base = base.replace(" ", "-")
    return base


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 build_examples_from_vocab.py <input.csv>")
        sys.exit(1)

    input_csv = Path(sys.argv[1])
    if not input_csv.exists():
        print(f"[FATAL] CSV file not found: {input_csv}", file=sys.stderr)
        sys.exit(1)

    # Prepare error log
    error_log_path = input_csv.parent / "examples-error.log"
    error_log = error_log_path.open("w", encoding="utf-8")

    client = load_client()

    # Output examples.csv in the same directory as the input CSV
    output_csv = input_csv.parent / "examples.csv"

    with input_csv.open("r", encoding="utf-8", newline="") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:

        reader = csv.reader(fin)
        writer = csv.writer(fout)

        # Write header for examples.csv
        writer.writerow(["expression_française", "exemple_fr", "traduction_en"])

        # Skip header line of input
        try:
            next(reader)
        except StopIteration:
            log("[WARN] Input CSV appears to be empty.", error_log)
            return

        for row_num, row in enumerate(reader, start=2):
            if len(row) < 2:
                log(f"[WARN] Row {row_num} has fewer than 2 columns, skipping.", error_log)
                continue

            english_name = row[0].strip()
            french_name = row[1].strip()
            # gender = row[2] if len(row) > 2 else ""

            if not french_name:
                log(f"[WARN] Row {row_num} has empty French name, skipping.", error_log)
                continue

            # Build base name: spaces, ', and / to '-'
            base_name = make_base_name(french_name)
            txt_path = input_csv.parent / f"{base_name}.txt"

            if not txt_path.exists():
                log(f"[WARN] Text file not found for row {row_num}: {txt_path}", error_log)
                continue

            # Read first 3 non-empty lines from the txt file
            try:
                with txt_path.open("r", encoding="utf-8") as ftxt:
                    lines = [ln.strip() for ln in ftxt.readlines() if ln.strip()]
            except Exception as e:
                log(f"[ERROR] Failed to read {txt_path}: {e}", error_log)
                continue

            if len(lines) < 3:
                log(
                    f"[WARN] {txt_path} has only {len(lines)} non-empty line(s), expected 3; using what is available.",
                    error_log,
                )

            for i, french_example in enumerate(lines[:3], start=1):
                try:
                    english_translation = translate_line(client, french_example)
                except Exception as e:
                    log(
                        f"[ERROR] Translation failed for {txt_path} line {i}: {e}",
                        error_log,
                    )
                    english_translation = ""

                # col1: original French name (from col2 of input)
                # col2: example line in French
                # col3: English translation
                writer.writerow([french_name, french_example, english_translation])

                print(
                    f"[INFO] Wrote example {i} for '{french_name}' "
                    f"from {txt_path.name} to {output_csv.name}"
                )

    error_log.close()
    print(f"[DONE] Examples written to {output_csv}")
    print(f"[INFO] Errors and warnings logged to {error_log_path}")


if __name__ == "__main__":
    main()

