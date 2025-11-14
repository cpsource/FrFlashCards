#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_mp3.py
Reads a CSV (English,French,Gender) and creates an MP3 for each row using OpenAI TTS.
- Filenames are derived from the English name with spaces → underscores.
- Logs progress and continues on errors.
- Requires env: OPENAI_API_KEY

Usage:
  python make_mp3.py bathroom-vocabulary.csv
"""

import csv
import os
import sys
import re
import time
import pathlib

# ---- OpenAI (robust to minor SDK diffs) ----
try:
    from openai import OpenAI
except Exception as e:
    print("[FATAL] Missing dependency: pip install openai", file=sys.stderr)
    sys.exit(1)

def slugify(name: str) -> str:
    """Lowercase, spaces→_, strip non-word to underscores, collapse repeats."""
    s = name.strip().lower().replace(" ", "_")
    s = re.sub(r"[^\w]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or f"item_{int(time.time())}"

def safe_write_bytes(path: str, data) -> None:
    p = pathlib.Path(path)
    if isinstance(data, (bytes, bytearray)):
        p.write_bytes(data)
    else:
        # some SDKs return streaming-like objects or str
        try:
            p.write_bytes(bytes(data))
        except Exception:
            # last-ditch: try .read()
            if hasattr(data, "read"):
                p.write_bytes(data.read())
            else:
                raise

def _extract_audio_bytes_from_responses(resp) -> bytes:
    """
    Mirrors the approach from your existing helper: walk typical Responses payloads
    to find base64 audio at item['audio']['data'].
    """
    import base64 as _b64
    # object-attr style
    try:
        for blk in getattr(resp, "output", []) or []:
            for item in getattr(blk, "content", []) or []:
                aud = getattr(item, "audio", None)
                if aud and getattr(aud, "data", None):
                    return _b64.b64decode(aud.data)
    except Exception:
        pass
    # dict-like / model_dump()
    try:
        d = resp if isinstance(resp, dict) else resp.model_dump()
        for blk in d.get("output", []) or []:
            for item in blk.get("content", []) or []:
                aud = item.get("audio")
                if aud and aud.get("data"):
                    return _b64.b64decode(aud["data"])
    except Exception:
        pass
    raise RuntimeError("Could not locate audio bytes in Responses payload.")

def tts_to_mp3(text: str, out_base: str, voice: str = "alloy", model: str = "gpt-4o-mini-tts") -> str:
    """
    Generate MP3 using several stable call patterns (format=, response_format=, Responses API).
    Returns the path to the MP3. Raises on failure.
    """
    client = OpenAI()
    out_mp3 = f"{out_base}.mp3"

    # Attempt A: audio.speech.create(..., format="mp3")
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except TypeError:
        pass
    except Exception:
        pass

    # Attempt B: audio.speech.create(..., response_format="mp3")
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, response_format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except TypeError:
        pass
    except Exception:
        pass

    # Attempt C: Responses API (modalities=["text","audio"])
    try:
        r = client.responses.create(
            model=model,
            input=text,
            modalities=["text", "audio"],
            audio={"voice": voice, "format": "mp3"},
        )
        audio_bytes = _extract_audio_bytes_from_responses(r)
        safe_write_bytes(out_mp3, audio_bytes)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    raise RuntimeError("TTS API error: all strategies failed")

def read_rows(csv_path: pathlib.Path):
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"English", "French", "Gender"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must have headers: {', '.join(sorted(required))}")
        for row in reader:
            en = (row.get("English") or "").strip()
            fr = (row.get("French") or "").strip()
            if not en or not fr:
                continue
            yield en, fr, (row.get("Gender") or "").strip()

def main():
    if len(sys.argv) != 2:
        print("Usage: python make_mp3.py <csv-file>", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("[FATAL] OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(2)

    csv_file = pathlib.Path(sys.argv[1])
    if not csv_file.exists():
        print(f"[FATAL] CSV not found: {csv_file}", file=sys.stderr)
        sys.exit(3)

    print(f"[INFO] Reading: {csv_file}")
    total = 0
    ok = 0
    fail = 0

    try:
        for en, fr, gender in read_rows(csv_file):
            total += 1
            slug = slugify(en)
            text = f"Ceci est {fr}."
            print(f"▶ [{total}] {en!r} → base='{slug}.mp3' | FR: {fr}")

            try:
                out = tts_to_mp3(text, slug)
                size = pathlib.Path(out).stat().st_size if pathlib.Path(out).exists() else 0
                if size == 0:
                    raise RuntimeError("zero-byte mp3 produced")
                print(f"   ✅ MP3 OK: {out} ({size} bytes)")
                ok += 1
            except Exception as e:
                print(f"   ❌ MP3 ERROR for {en!r}: {e}")
                fail += 1
    except Exception as e:
        print(f"[FATAL] Could not process CSV: {e}", file=sys.stderr)
        sys.exit(4)

    print("\n[SUMMARY]")
    print(f"   total rows: {total}")
    print(f"   success   : {ok}")
    print(f"   failed    : {fail}")

if __name__ == "__main__":
    main()

