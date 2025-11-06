#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_mp3_single.py
Generate a single MP3 file from provided text using OpenAI TTS.

Usage:
  python make_mp3_single.py output_name "Bonjour tout le monde."

Example:
  python make_mp3_single.py greeting "Bonjour, comment allez-vous ?"

Requires:
  - OPENAI_API_KEY environment variable
  - openai package (pip install openai)
"""

import os
import sys
import re
import pathlib
import base64
import time

try:
    from openai import OpenAI
except Exception:
    print("[FATAL] Missing dependency: pip install openai", file=sys.stderr)
    sys.exit(1)


def slugify(name: str) -> str:
    """Convert spaces → underscores and strip non-filename-safe characters."""
    s = name.strip().lower().replace(" ", "_")
    s = re.sub(r"[^\w-]", "_", s)
    return s or f"audio_{int(time.time())}"


def safe_write_bytes(path: str, data) -> None:
    """Write bytes safely to a file."""
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
    """Extract base64 audio data from a responses.create() result."""
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
    """Generate MP3 using multiple compatible methods."""
    client = OpenAI()
    out_mp3 = f"{out_base}.mp3"

    # Attempt A: standard audio.speech.create
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    # Attempt B: with response_format
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, response_format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    # Attempt C: via Responses API fallback
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

    raise RuntimeError("TTS API error: all methods failed")


def main():
    if len(sys.argv) != 3:
        print("Usage: python make_mp3_single.py <output-name> \"<text>\"", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("[FATAL] OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(2)

    out_base = slugify(sys.argv[1])
    text = sys.argv[2].strip()

    print(f"[INFO] Generating MP3: {out_base}.mp3")
    print(f"[INFO] Text: {text}")

    try:
        result_file = tts_to_mp3(text, out_base)
        size = pathlib.Path(result_file).stat().st_size
        print(f"[✅] Created {result_file} ({size} bytes)")
    except Exception as e:
        print(f"[ERROR] MP3 generation failed: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()

