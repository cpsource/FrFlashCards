#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
safe_name.py

Takes one command-line argument (a French name or expression),
applies filename normalization similar to the JS `safeName()` function,
and prints the result.
"""

import re
import sys


def safe_name(name: str) -> str:
    """Normalize French names into safe filenames."""
    result = name.strip()
    result = re.sub(r"\s*/\s*", "-", result)   # replace " / " or " /" or "/ " with single dash
    result = re.sub(r"^l'", "l-", result, flags=re.IGNORECASE)  # l'imperméable → l-imperméable
    result = re.sub(r"\s+", "-", result)       # spaces → -
    result = re.sub(r"'", "-", result)         # any remaining apostrophes → -
    result = re.sub(r"-+", "-", result)        # collapse multiple consecutive dashes
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 safe_name.py \"<french expression>\"")
        sys.exit(1)

    input_name = sys.argv[1]
    normalized = safe_name(input_name)
    print(normalized)


if __name__ == "__main__":
    main()

