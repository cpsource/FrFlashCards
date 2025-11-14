#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_frflashy_image_and_sound.py

- Downloads an image (saved as .png) to the current directory.
- Generates FR speech (MP3/WAV) to the current directory.
- Adapts to multiple OpenAI SDK variants for TTS.

Usage:
  export OPENAI_API_KEY=sk-...
  python get_frflashy_image_and_sound.py \
    --image "https://commons.wikimedia.org/wiki/Special:FilePath/Small%20spoon.jpg" \
    --french-text "Ceci est une cuillère." \
    --outfile-prefix "cuillere"
"""

import argparse, os, sys, re, time, base64, pathlib
from urllib.parse import urlparse

# ---------- deps ----------
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Please: pip install requests", file=sys.stderr); sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Please: pip install openai", file=sys.stderr); sys.exit(1)

DEFAULT_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120 Safari/537.36")

def safe_filename(name: str) -> str:
    keep = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    clean = "".join(c if c in keep else "_" for c in name)
    return "_".join(clean.strip().split())[:120] or f"file_{int(time.time())}"

def _to_original_if_thumb(url: str) -> str:
    """Wikimedia: /thumb/.../640px-File.jpg → /.../File.jpg"""
    m = re.search(
        r"^(https?://upload\.wikimedia\.org/wikipedia/commons)"
        r"/thumb/([^/]+)/([^/]+)/([^/]+)/(?:\d+px-)?\4$", url
    )
    if m:
        base, d1, d2, filename = m.groups()
        return f"{base}/{d1}/{d2}/{filename}"
    return url

def _requests_session(user_agent: str, referer: str | None) -> requests.Session:
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5,
                    status_forcelist=(429, 500, 502, 503, 504),
                    allowed_methods=frozenset(["GET"]))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({"User-Agent": user_agent})
    if referer:
        s.headers.update({"Referer": referer})
    return s

def download_image(src: str, outfile_prefix: str | None,
                   user_agent: str, referer: str | None) -> str:
    """Save image as .png in CWD. Works with Special:FilePath + redirects."""
    parsed = urlparse(src)
    out_png = f"{safe_filename(outfile_prefix) if outfile_prefix else safe_filename(pathlib.Path(parsed.path).stem or 'image')}.png"

    # local path
    if parsed.scheme not in ("http", "https"):
        p = pathlib.Path(src)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {src}")
        pathlib.Path(out_png).write_bytes(p.read_bytes())
        print(f"[OK] Image saved as {out_png}")
        return out_png

    session = _requests_session(user_agent, referer)
    try:
        r = session.get(src, timeout=30, allow_redirects=True)
        if r.status_code == 404:
            src2 = _to_original_if_thumb(src)
            if src2 != src:
                r = session.get(src2, timeout=30, allow_redirects=True)
        r.raise_for_status()
        data = r.content
    except requests.HTTPError as e:
        # final fallback via original if thumb
        src2 = _to_original_if_thumb(src)
        if src2 != src:
            r2 = session.get(src2, timeout=30, allow_redirects=True)
            r2.raise_for_status()
            data = r2.content
        else:
            raise RuntimeError(f"Image download failed: {e}") from e

    pathlib.Path(out_png).write_bytes(data)
    print(f"[OK] Image saved as {out_png}")
    return out_png

def _extract_audio_bytes_from_responses(resp) -> bytes:
    """
    For Responses API result:
    - Look for base64 audio at item['audio']['data'] or similar.
    - Walk a few common shapes to be robust across SDK versions.
    """
    # Try modern shape: resp.output (list) → content (list) → item.audio.data
    try:
        for block in getattr(resp, "output", []) or []:
            for item in getattr(block, "content", []) or []:
                audio = getattr(item, "audio", None) or (item.get("audio") if isinstance(item, dict) else None)
                if audio and ("data" in audio):
                    return base64.b64decode(audio["data"])
    except Exception:
        pass

    # Fallback: raw dict-esque
    try:
        d = resp if isinstance(resp, dict) else resp.model_dump()
        for block in d.get("output", []):
            for item in block.get("content", []):
                audio = item.get("audio")
                if audio and audio.get("data"):
                    return base64.b64decode(audio["data"])
    except Exception:
        pass

    raise RuntimeError("Could not locate audio bytes in Responses payload.")

def generate_tts(text: str, voice: str, fmt: str, model: str,
                 outfile_prefix: str | None) -> str:
    """Create speech file, adapting to SDK differences."""
    if fmt not in ("mp3", "wav"):
        raise ValueError("format must be 'mp3' or 'wav'")
    ext = ".mp3" if fmt == "mp3" else ".wav"
    out_audio = f"{safe_filename(outfile_prefix) if outfile_prefix else safe_filename(text[:60] or 'audio')}{ext}"

    client = OpenAI()

    # Attempt 1: audio.speech.create(..., format=fmt)
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, format=fmt)
        audio_bytes = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        pathlib.Path(out_audio).write_bytes(audio_bytes)
        print(f"[OK] Audio saved as {out_audio} (format=)")
        return out_audio
    except TypeError:
        pass  # try next signature
    except Exception as e:
        # If it's not a TypeError, we still try the other forms
        last_err = e
    else:
        return out_audio

    # Attempt 2: audio.speech.create(..., response_format=fmt)
    try:
        resp = client.audio.speech.create(model=model, voice=voice, input=text, response_format=fmt)
        audio_bytes = resp.read() if hasattr(resp, "read") else getattr(resp, "content", resp)
        pathlib.Path(out_audio).write_bytes(audio_bytes)
        print(f"[OK] Audio saved as {out_audio} (response_format=)")
        return out_audio
    except TypeError:
        pass
    except Exception:
        pass  # fall through

    # Attempt 3: Responses API (modalities + audio dict)
    try:
        r = client.responses.create(
            model=model,
            input=text,
            modalities=["text", "audio"],
            audio={"voice": voice, "format": fmt},
        )
        audio_bytes = _extract_audio_bytes_from_responses(r)
        pathlib.Path(out_audio).write_bytes(audio_bytes)
        print(f"[OK] Audio saved as {out_audio} (Responses API)")
        return out_audio
    except Exception as e:
        raise RuntimeError(f"TTS API error (all strategies failed): {e}")

def main():
    ap = argparse.ArgumentParser(description="Get image (.png) and French audio via OpenAI TTS.")
    ap.add_argument("--image", required=True, help="Image URL/local path. Special:FilePath works.")
    ap.add_argument("--french-text", required=True, help="French text to synthesize.")
    ap.add_argument("--voice", default="alloy", help="TTS voice (e.g., alloy).")
    ap.add_argument("--format", default="mp3", choices=["mp3", "wav"], help="Audio format (default: mp3).")
    ap.add_argument("--model", default="gpt-4o-mini-tts", help="TTS model (e.g., gpt-4o-mini-tts, tts-1).")
    ap.add_argument("--outfile-prefix", default=None, help="Base name for BOTH outputs (e.g., 'cuillere').")
    ap.add_argument("--user-agent", default=DEFAULT_UA, help="HTTP User-Agent for image fetch.")
    ap.add_argument("--referer", default="https://frflashy.com/", help="HTTP Referer for image fetch.")
    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(2)

    try:
        img = download_image(args.image, args.outfile_prefix, args.user_agent, args.referer)
    except Exception as e:
        print(f"[ERROR] Image error: {e}", file=sys.stderr)
        sys.exit(3)

    try:
        aud = generate_tts(args.french_text, args.voice, args.format, args.model, args.outfile_prefix)
    except Exception as e:
        print(f"[ERROR] TTS error: {e}", file=sys.stderr)
        sys.exit(4)

    print("\n✅ Done.")
    print(f"   Image: {img}")
    print(f"   Audio: {aud}")

if __name__ == "__main__":
    main()

