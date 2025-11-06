#!/usr/bin/env bash
# Build assets for the idiom "être bien dans ses baskets"

set -euo pipefail

TTS="../tools/make_mp3_single.py"
RESIZER="../tools/resize_png-2.py"

# Instructions for the TTS engine (for you only, not spoken)
INSTR="clear, natural, use a calm woman's French voice"

# Base name (without .mp3 / .png)
BASE="etre_bien_dans_ses_baskets"

echo "=== Building assets for: être bien dans ses baskets ==="

# 1) Generate the main MP3 for the expression
TEXT="être bien dans ses baskets"
echo "[TTS] Generating ${BASE}.mp3 ..."
python3 "$TTS" "$BASE" "$INSTR" "$TEXT"

# 2) Resize the PNG if it exists
if [[ -f "${BASE}.png" ]]; then
  echo "[IMG] Resizing ${BASE}.png to 100px height ..."
  python3 "$RESIZER" "${BASE}.png" 100
else
  echo "[WARN] ${BASE}.png not found. Please create or copy the image first."
fi

echo "✅ Done: MP3 and (if present) PNG processed for ${BASE}."

