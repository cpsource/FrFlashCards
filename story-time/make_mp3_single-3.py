#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_mp3_single-2.py
Generate a single MP3 file from provided text using OpenAI TTS.

Usage:
  python make_mp3_single-2.py <output-name> "<instructions>" "<text>"

Examples:
  python make_mp3_single-2.py greeting "use a woman's voice, cheerful" "Bonjour tout le monde."
  python make_mp3_single-2.py notice "voice=alloy, formal" "Attention: la porte se ferme automatiquement."

Notes:
  - The <instructions> are used ONLY to set generation parameters (e.g., voice/tone).
  - The actual spoken text is given by <text>.
  - We always assume the text is FRENCH and want French output.
  - The script is defensive and adapts to the installed openai-python version:
      * It inspects the parameters of audio.speech.create at runtime
        and only passes arguments that are actually supported.
"""

import os
import sys
import re
import time
import pathlib
import inspect

try:
    from openai import OpenAI
except Exception:
    print("[FATAL] Missing dependency: pip install openai", file=sys.stderr)
    sys.exit(1)

# =========================
# Configuration
# =========================

# Map vague tone words to voices
TONE_VOICE_MAP = {
    "cheerful": "alloy",
    "happy":    "alloy",
    "joyful":   "alloy",
    "calm":     "verse",
    "soft":     "verse",
    "gentle":   "verse",
    "slow":     "verse",
    "formal":   "alloy",
    "serious":  "alloy",
    "clear":    "alloy",
    "excited":  "alloy",
    "energetic":"alloy",
    "lively":   "alloy",
    "sad":      "verse",
    "somber":   "verse",
}

VOICE_MAP_BY_GENDER = {
    "female": "alloy",
    "male":   "verse",
}

DEFAULT_VOICE = "alloy"
DEFAULT_MODEL = "gpt-4o-mini-tts"

# We *want* French. Some SDK versions accept a `language` argument to audio.speech.
# We will pass it ONLY if the installed function actually supports it.
LANG_HINT = "fr"

# =========================
# Utility functions
# =========================

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
    """
    Priority:
      1) explicit voice=NAME
      2) tone-based voice
      3) gender-based voice
      4) DEFAULT_VOICE
    """
    instr = instructions.strip()

    # 1) explicit override: voice=alloy
    m = re.search(r"\bvoice\s*=\s*([a-z0-9_\-]+)\b", instr, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    # 2) tone-based mapping
    tone_voice = choose_voice_from_tone(instr)
    if tone_voice:
        return tone_voice

    # 3) gender-based mapping
    gender_voice = choose_voice_from_gender(instr)
    if gender_voice:
        return gender_voice

    # 4) default
    return DEFAULT_VOICE

# =========================
# Main TTS logic
# =========================

def tts_to_mp3(text: str, out_base: str, *, voice: str, model: str = DEFAULT_MODEL) -> str:
    """
    Generate MP3 using audio.speech.create, adapting to the installed openai-python version.

    We:
      * Assume `text` is French.
      * Try to pass language='fr' ONLY if the create() function supports it.
      * Try to request mp3 output via `format` or `response_format` ONLY if supported.
    """
    client = OpenAI()
    out_mp3 = f"{out_base}.mp3"

    if not hasattr(client, "audio") or not hasattr(client.audio, "speech"):
        raise RuntimeError("This openai-python version does not expose client.audio.speech; upgrade the SDK.")

    speech_create = client.audio.speech.create

    # Introspect the function signature so we only pass supported kwargs.
    sig = inspect.signature(speech_create)
    params = sig.parameters

    kwargs = {}

    # Required-ish arguments, guarded by presence in signature
    if "model" in params:
        kwargs["model"] = model
    if "voice" in params:
        kwargs["voice"] = voice
    if "input" in params:
        kwargs["input"] = text

    # Prefer explicit mp3 format if supported
    if "format" in params:
        kwargs["format"] = "mp3"
    elif "response_format" in params:
        kwargs["response_format"] = "mp3"

    # Pass language hint ONLY if supported
    if "language" in params:
        kwargs["language"] = LANG_HINT

    print(f"[DEBUG] Calling audio.speech.create with kwargs: {kwargs}")

    resp = speech_create(**kwargs)

    # Different SDK versions return slightly different response types.
    # Try to extract bytes in a robust way.
    data = None
    if isinstance(resp, (bytes, bytearray)):
        data = resp
    elif hasattr(resp, "read"):
        data = resp.read()
    elif hasattr(resp, "content"):
        data = resp.content
    else:
        # Fallback: last resort, try bytes() on it
        data = bytes(resp)

    safe_write_bytes(out_mp3, data)

    if pathlib.Path(out_mp3).stat().st_size <= 0:
        raise RuntimeError("audio.speech.create returned empty data")

    return out_mp3

# =========================
# CLI Entrypoint
# =========================

def main():
    if len(sys.argv) != 4:
        print("Usage: python make_mp3_single-2.py <output-name> \"<instructions>\" \"<text>\"", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("[FATAL] OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(2)

    out_base = slugify(sys.argv[1])
    instructions = sys.argv[2].strip()
    #text = sys.argv[3].strip()
    # Always prepend the French-language hint
    text = f"en français : {sys.argv[3].strip()}"

    voice = choose_voice(instructions)

    print(f"[INFO] Generating MP3: {out_base}.mp3")
    print(f"[INFO] Voice selected: {voice}")
    print(f"[INFO] We assume the input text is French and want French TTS (lang='{LANG_HINT}').")
    if instructions:
        print(f"[INFO] Instructions: {instructions}")
    print(f"[INFO] Text length: {len(text)} characters")

    try:
        result_file = tts_to_mp3(text, out_base, voice=voice)
        size = pathlib.Path(result_file).stat().st_size
        print(f"[✅] Created {result_file} ({size} bytes)")
    except Exception as e:
        print(f"[ERROR] MP3 generation failed: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()

