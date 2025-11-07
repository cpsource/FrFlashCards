#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make-generate-single-script.py

Reads a CSV file with columns: English, French, Gender
and produces a bash script that calls:

    python3 generate-single.py 'French term'

for each row, with an echo before each call so progress can be tracked.

Usage:
    python3 make-generate-single-script.py vetements-a1-a2.csv [output_script.sh]

If output_script.sh is not given, defaults to: run-generate-single.sh
"""

import sys
import csv
from pathlib import Path


def bash_single_quote(s: str) -> str:
    """
    Safely single-quote a string for bash.

    'foo'       -> 'foo'
    "l'étui"    -> 'l'\''étui'
    """
    return "'" + s.replace("'", "'\"'\"'") + "'"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 make-generate-single-script.py <input.csv> [output_script.sh]")
        sys.exit(1)

    input_csv = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_sh = Path(sys.argv[2])
    else:
        output_sh = Path("run-generate-single.sh")

    if not input_csv.exists():
        print(f"[ERROR] CSV file not found: {input_csv}")
        sys.exit(1)

    # Read CSV
    rows = []
    with input_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Expect columns including "French"
        if "French" not in reader.fieldnames:
            print("[ERROR] CSV must have a 'French' column.")
            sys.exit(1)
        for row in reader:
            french = row.get("French", "").strip()
            if french:
                rows.append(french)

    # Build bash script content
    lines = []
    lines.append("#!/usr/bin/env bash")
    lines.append("set -euo pipefail")
    lines.append("")
    lines.append("# Auto-generated script to build flash cards with generate-single.py")
    lines.append(f"# Source CSV: {input_csv}")
    lines.append("")

    for french in rows:
        quoted = bash_single_quote(french)
        # Echo for tracking
        lines.append(f'echo "=== Processing: {french} ==="')
        lines.append(f"python3 generate-single.py {quoted}")
        lines.append("")  # blank line between entries

    output_sh.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Make it executable (optional; works on Unix-like systems)
    try:
        output_sh.chmod(0o755)
    except Exception:
        # On non-Unix systems this might fail; ignore
        pass

    print(f"✅ Generated bash script: {output_sh}")


if __name__ == "__main__":
    main()

