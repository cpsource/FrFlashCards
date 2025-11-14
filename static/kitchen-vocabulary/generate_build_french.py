#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv, sys, re
from pathlib import Path

BASH_HEADER = """#!/bin/bash
# Auto-generated from CSV by generate_build_french.py
# Usage:
#   export OPENAI_API_KEY=sk-...
#   chmod +x build_french
#   ./build_french

set -euo pipefail

LOG_FILE="build_french.log"
VOICE="alloy"
FORMAT="mp3"
MODEL="gpt-4o-mini-tts"

echo "Starting French build..." | tee "$LOG_FILE"
"""

# IMPORTANT
# - Any bash ${VAR} is written as ${{VAR}} so Python .format() won't touch it.
# - Any literal Python dict braces in the heredoc are escaped as {{ and }}.
BLOCK_TEMPLATE = r"""
# --- {eng_display} ---
ENG="{eng_slug}"
IMG_URL="{img_url}"
FRENCH_TEXT="{french_sentence}"

echo "▶ Processing ${{ENG}} ..." | tee -a "$LOG_FILE"

# 1) Try full run (image + audio). Never abort overall flow.
python3 get_frflashy_image_and_sound.py \
  --image "$IMG_URL" \
  --french-text "$FRENCH_TEXT" \
  --voice "$VOICE" \
  --format "$FORMAT" \
  --model "$MODEL" \
  --outfile-prefix "$ENG" \
  2>&1 | tee -a "$LOG_FILE" || true

# 2) Resize PNG if present
if [ -f "${{ENG}}.png" ]; then
  echo "   Found PNG → resizing to 100 px" | tee -a "$LOG_FILE"
  python3 ../tools/resize_png-2.py "${{ENG}}.png" 100 2>&1 | tee -a "$LOG_FILE" || true
else
  echo "⚠️  No PNG for ${{ENG}} (image may have failed)." | tee -a "$LOG_FILE"
fi

# 3) Ensure MP3 exists and is non-empty; if not, rebuild audio ONLY with a robust inline helper
if [ ! -s "${{ENG}}.mp3" ]; then
  echo "⚠️  ${{ENG}}.mp3 missing or zero-bytes — retrying audio-only..." | tee -a "$LOG_FILE"
  rm -f "${{ENG}}.mp3"

  # Inline Python fallback: generate MP3 regardless of image result
  python3 - << 'PY' 2>&1 | tee -a "$LOG_FILE" || true
import os, sys, base64, pathlib
FRENCH_TEXT = {french_sentence_py}
OUT = "{eng_slug}.mp3"
VOICE = os.environ.get("VOICE","alloy")
MODEL = os.environ.get("MODEL","gpt-4o-mini-tts")

try:
    from openai import OpenAI
except Exception as e:
    print("[ERROR] Fallback TTS: openai package missing:", e)
    sys.exit(0)

def write_bytes(path, b):
    pathlib.Path(path).write_bytes(b if isinstance(b, (bytes, bytearray)) else bytes(b))

client = OpenAI()

# Strategy A: Responses API (modalities audio)
try:
    r = client.responses.create(
        model=MODEL,
        input=FRENCH_TEXT,
        modalities=["text","audio"],
        audio={{"voice": VOICE, "format": "mp3"}},
    )
    # extract base64 audio
    def _extract(resp):
        try:
            d = resp if isinstance(resp, dict) else resp.model_dump()
            for blk in d.get("output", []):
                for item in blk.get("content", []):
                    aud = item.get("audio")
                    if aud and aud.get("data"):
                        return base64.b64decode(aud["data"])
        except Exception:
            pass
        # object-attr style
        try:
            for blk in getattr(resp, "output", []) or []:
                for it in getattr(blk, "content", []) or []:
                    aud = getattr(it, "audio", None)
                    if aud and getattr(aud, "data", None):
                        return base64.b64decode(aud.data)
        except Exception:
            pass
        return None
    data = _extract(r)
    if data:
        write_bytes(OUT, data)
        if os.path.getsize(OUT) > 0:
            print("[OK] Audio fallback via Responses API →", OUT)
            sys.exit(0)
except Exception:
    pass

# Strategy B: classic audio.speech.create with either format= or response_format=
try:
    try:
        resp = client.audio.speech.create(model=MODEL, voice=VOICE, input=FRENCH_TEXT, format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        write_bytes(OUT, data)
        if os.path.getsize(OUT) > 0:
            print("[OK] Audio fallback via audio.speech.create(format=) →", OUT)
            sys.exit(0)
    except TypeError:
        resp = client.audio.speech.create(model=MODEL, voice=VOICE, input=FRENCH_TEXT, response_format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        write_bytes(OUT, data)
        if os.path.getsize(OUT) > 0:
            print("[OK] Audio fallback via audio.speech.create(response_format=) →", OUT)
            sys.exit(0)
except Exception as e:
    print("[WARN] Audio fallback failed:", e)

print("[ERROR] Audio fallback could not produce a valid mp3 for", OUT)
PY

  # Verify again after fallback
  if [ ! -s "${{ENG}}.mp3" ]; then
    echo "❌ FAILED to produce non-empty MP3 for ${{ENG}}" | tee -a "$LOG_FILE"
  else
    echo "✅ Recovered MP3 for ${{ENG}}" | tee -a "$LOG_FILE"
  fi
else
  echo "   MP3 OK for ${{ENG}}" | tee -a "$LOG_FILE"
fi

echo "✅ Completed ${{ENG}}" | tee -a "$LOG_FILE"
"""

BASH_FOOTER = """
echo "All entries processed. See build_french.log for details."
"""

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_") or "item"

def guess_special_filepath_url(english_word: str) -> str:
    filename = english_word.strip().replace(" ", "%20")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}.jpg"

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_build_french.py <csv_path> [output_bash_path]", file=sys.stderr)
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("build_french")

    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"English", "French", "Gender"}
        if not required.issubset(reader.fieldnames or []):
            print(f"[ERROR] CSV must have headers: {', '.join(sorted(required))}", file=sys.stderr)
            sys.exit(1)
        rows = [(r["English"].strip(), r["French"].strip(), (r.get("Gender") or "").strip())
                for r in reader if (r.get("English") and r.get("French"))]

    parts = [BASH_HEADER]
    for eng, fr, _gender in rows:
        eng_slug = slugify(eng)
        french_sentence = f"Ceci est {fr}."
        img_url = guess_special_filepath_url(eng_slug)
        parts.append(BLOCK_TEMPLATE.format(
            eng_display=eng,
            eng_slug=eng_slug,
            french_sentence=french_sentence.replace('"','\\"'),
            french_sentence_py=repr(french_sentence),
            img_url=img_url
        ))
    parts.append(BASH_FOOTER)

    out_path.write_text("".join(parts), encoding="utf-8")
    out_path.chmod(0o755)
    print(f"[OK] Generated bash file: {out_path.resolve()}")

if __name__ == "__main__":
    main()

