#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_mp3.py
Reads a CSV (English,French,Gender) and creates an MP3 for each row using OpenAI TTS.

- Filenames: English name → lowercase, spaces→underscores.
- If the French word begins with l’ or l' (elision), adds a gender note:
  feminine  -> "Le mot est féminin."
  masculine -> "Le mot est masculin."
- Optional flag --skip-non-elision (or -s) will skip all non-elision entries.
- Logs progress and continues on errors.
- Requires env var: OPENAI_API_KEY

Usage:
  python make_mp3.py bathroom-vocabulary.csv
  python make_mp3.py bathroom-vocabulary.csv --skip-non-elision
"""

import csv
import os
import sys
import re
import time
import pathlib
import argparse

# ---- OpenAI (robust import) ----
try:
    from openai import OpenAI
except Exception:
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
        try:
            p.write_bytes(bytes(data))
        except Exception:
            if hasattr(data, "read"):
                p.write_bytes(data.read())
            else:
                raise


def _extract_audio_bytes_from_responses(resp) -> bytes:
    import base64 as _b64
    try:
        for blk in getattr(resp, "output", []) or []:
            for item in getattr(blk, "content", []) or []:
                aud = getattr(item, "audio", None)
                if aud and getattr(aud, "data", None):
                    return _b64.b64decode(aud.data)
    except Exception:
        pass
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
    """Generate MP3 using several stable call patterns."""
    client = OpenAI()
    out_mp3 = f"{out_base}.mp3"

    # Attempt A
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    # Attempt B
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, response_format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    # Attempt C (Responses API)
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
            gender = (row.get("Gender") or "").strip().lower()
            if not en or not fr:
                continue
            yield en, fr, gender


def begins_with_elision(fr: str) -> bool:
    """True if word begins with l’ or l' (elision)."""
    s = fr.lstrip()
    return bool(re.match(r"^l[’']\s*", s, flags=re.IGNORECASE))


def gender_note(gender: str) -> str | None:
    if gender == "feminine":
        return "Le mot est féminin."
    if gender == "masculine":
        return "Le mot est masculin."
    return None


def build_tts_text(fr: str, gender: str) -> str:
    """Add gender note if elision detected."""
    base = f"Ceci est {fr}."
    if begins_with_elision(fr):
        note = gender_note(gender)
        if note:
            return f"{base} {note}"
    return base


def main():
    parser = argparse.ArgumentParser(description="Generate MP3s from a French vocabulary CSV using OpenAI TTS.")
    parser.add_argument("csv_file", help="CSV filename (English,French,Gender)")
    parser.add_argument("-s", "--skip-non-elision", action="store_true",
                        help="Skip rows whose French word does NOT start with l'/l’.")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("[FATAL] OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(2)

    csv_file = pathlib.Path(args.csv_file)
    if not csv_file.exists():
        print(f"[FATAL] CSV not found: {csv_file}", file=sys.stderr)
        sys.exit(3)

    print(f"[INFO] Reading: {csv_file}")
    total = ok = fail = skipped = 0

    for en, fr, gender in read_rows(csv_file):
        total += 1
        if args.skip_non_elision and not begins_with_elision(fr):
            skipped += 1
            print(f"⏭️  Skipped '{en}' (no l'/l’ prefix).")
            continue

        slug = slugify(en)
        text = build_tts_text(fr, gender)
        add_note = begins_with_elision(fr) and (gender_note(gender) is not None)

        print(f"▶ [{total}] {en!r} → {slug}.mp3 | FR: {fr} | gender={gender or 'n/a'}")
        if add_note:
            print("   ℹ️  Added gender note for elision (l’/l').")

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

    print("\n[SUMMARY]")
    print(f"   total rows : {total}")
    print(f"   success    : {ok}")
    print(f"   failed     : {fail}")
    print(f"   skipped    : {skipped}")


if __name__ == "__main__":
    main()

