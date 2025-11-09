#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_mp3_single.py
Generate a single MP3 file from provided text using OpenAI TTS.

Usage:
  python make_mp3_single.py <output-name> "<instructions>" "<text>"
"""

import os
import sys
import re
import time
import pathlib

# --- OpenAI SDK ---
try:
    from openai import OpenAI
except Exception:
    print("[FATAL] Missing dependency: pip install openai", file=sys.stderr)
    sys.exit(1)

# =========================
# Configuration
# =========================
TONE_VOICE_MAP = {
    "cheerful": "alloy",
    "happy": "alloy",
    "joyful": "alloy",
    "calm": "verse",
    "soft": "verse",
    "gentle": "verse",
    "slow": "verse",
    "formal": "alloy",
    "serious": "alloy",
    "clear": "alloy",
    "excited": "alloy",
    "energetic": "alloy",
    "lively": "alloy",
    "sad": "verse",
    "somber": "verse",
}

VOICE_MAP_BY_GENDER = {
    "female": "alloy",
    "male": "verse",
}

DEFAULT_VOICE = "alloy"
DEFAULT_MODEL = "gpt-4o-mini-tts"


def slugify(name: str) -> str:
    s = name.strip().lower().replace(" ", "_")
    s = re.sub(r"[^\w-]", "_", s)
    return s or f"audio_{int(time.time())}"


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
            for item in d.get("content", []) or []:
                aud = item.get("audio")
                if aud and aud.get("data"):
                    return _b64.b64decode(aud["data"])
    except Exception:
        pass
    raise RuntimeError("Could not locate audio bytes in Responses payload.")


def choose_voice_from_tone(instr: str) -> str | None:
    instr_l = instr.lower()
    for tone_key, voice in TONE_VOICE_MAP.items():
        if re.search(rf"\b{re.escape(tone_key)}\b", instr_l):
            return voice
    return None


def choose_voice_from_gender(instr: str) -> str | None:
    instr_l = instr.lower()
    if any(w in instr_l for w in ["woman", "women", "female", "girl", "feminine"]):
        return VOICE_MAP_BY_GENDER.get("female")
    if any(w in instr_l for w in ["man", "male", "masculine", "boy"]):
        return VOICE_MAP_BY_GENDER.get("male")
    return None


def choose_voice(instructions: str) -> str:
    instr = instructions.strip()
    m = re.search(r"\bvoice\s*=\s*([a-z0-9_\-]+)\b", instr, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    tone_voice = choose_voice_from_tone(instr)
    if tone_voice:
        return tone_voice
    gender_voice = choose_voice_from_gender(instr)
    if gender_voice:
        return gender_voice
    return DEFAULT_VOICE


def tts_to_mp3(text: str, out_base: str, *, voice: str, model: str = DEFAULT_MODEL) -> str:
    client = OpenAI()
    out_mp3 = f"{out_base}.mp3"

    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, response_format="mp3")
        data = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        safe_write_bytes(out_mp3, data)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    try:
        r = client.responses.create(
            model=model,
            input=text,
            modalities=["text", "audio"],
            audio={"voice": voice, "format": "mp3"},
        )
        import base64
        audio_bytes = _extract_audio_bytes_from_responses(r)
        safe_write_bytes(out_mp3, audio_bytes)
        if pathlib.Path(out_mp3).stat().st_size > 0:
            return out_mp3
    except Exception:
        pass

    raise RuntimeError("TTS API error: all methods failed")


def main():
    if len(sys.argv) != 4:
        print("Usage: python make_mp3_single.py <output-name> \"<instructions>\" \"<text>\"", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("[FATAL] OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(2)

    out_base = slugify(sys.argv[1])
    instructions = sys.argv[2].strip()
    text = sys.argv[3].strip()

    # 👇 ADDITION: if there's only one word, prepend "En français, on dit ..."
    #if len(text.split()) == 1:
    text = f"En français, on dit << {text} >>"

    voice = choose_voice(instructions)

    print(f"[INFO] Generating MP3: {out_base}.mp3")
    print(f"[INFO] Voice selected: {voice}")
    if instructions:
        print(f"[INFO] Instructions: {instructions}")
    print(f"[INFO] Text {text} length: {len(text)} characters")

    try:
        result_file = tts_to_mp3(text, out_base, voice=voice)
        size = pathlib.Path(result_file).stat().st_size
        print(f"[✅] Created {result_file} ({size} bytes)")
    except Exception as e:
        print(f"[ERROR] MP3 generation failed: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()

