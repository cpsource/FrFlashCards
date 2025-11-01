#!/bin/bash
# Usage: ./move_and_resize.sh <basename>
# Example: ./move_and_resize.sh spoon
# Moves image.png from Downloads, renames it, and resizes to 100px.

# Exit immediately if a command fails
set -euo pipefail

# --- Check argument ---
if [ $# -ne 1 ]; then
  echo "Error: missing argument."
  echo "Usage: $0 <basename>"
  exit 1
fi

BASENAME="$1"
SRC="/mnt/c/Users/pagec/Downloads/image.png"
DEST="${BASENAME}.png"

# --- Move and rename ---
if [ ! -f "$SRC" ]; then
  echo "Error: source file not found at $SRC"
  exit 2
fi

echo "Moving $SRC → $DEST"
mv "$SRC" "$DEST"

# --- Resize ---
echo "Resizing $DEST to 100 px"
python ../tools/resize_png-2.py "$DEST" 100

echo "✅ Done: $DEST resized."

