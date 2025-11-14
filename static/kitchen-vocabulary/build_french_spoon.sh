#!/bin/bash
# build_french_spoon.sh
# Creates: cuillere.png + cuillere.mp3 in current directory.

set -euo pipefail

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "[ERROR] export OPENAI_API_KEY=sk-..." >&2
  exit 1
fi

IMG_URL="https://commons.wikimedia.org/wiki/Special:FilePath/Small%20spoon.jpg"
# Or wooden spoon:
# IMG_URL="https://commons.wikimedia.org/wiki/Special:FilePath/Cuiller%20en%20bois%20-%20dessus.jpg"

FRENCH_TEXT="Ceci est une cuillère."

python3 get_frflashy_image_and_sound.py \
  --image "$IMG_URL" \
  --french-text "$FRENCH_TEXT" \
  --voice "alloy" \
  --format "mp3" \
  --model "gpt-4o-mini-tts" \
  --outfile-prefix "cuillere"

echo "✅ Generated cuillere.png and cuillere.mp3"

