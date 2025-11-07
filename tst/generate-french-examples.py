#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate-french-examples.py

Usage:
  python3 generate-french-examples.py [--trace] <number-of-examples> "<french-expression>"

Example:
  python3 generate-french-examples.py 3 "courbes du corps"

If <expression>.txt already exists, reuses it instead of calling the LLM.
Otherwise, generates examples, saves them to <expression>.txt, and prints HTML to stdout.
"""

import sys
import os
import re
import html
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

MODEL_EXAMPLES = "gpt-4o"
MODEL_TRANSLATE = "gpt-4o-mini"
TRACE_ENABLED = False


def trace(msg: str):
    if TRACE_ENABLED:
        print(f"[TRACE] {msg}", file=sys.stderr, flush=True)


def load_api_key() -> str:
    """Load the OpenAI key from ~/.env or environment."""
    home_env = Path.home() / ".env"
    if home_env.exists():
        load_dotenv(home_env)
        trace(f"Loaded .env from {home_env}")
    else:
        load_dotenv()
        trace("Loaded .env from current directory (if present)")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[FATAL] OPENAI_API_KEY not found in environment.", file=sys.stderr)
        sys.exit(1)
    return api_key


def clean_and_split_examples(raw_lines: list[str]) -> list[str]:
    """Clean raw lines and split multiple sentences into separate items."""
    examples = []
    for line in raw_lines:
        line = re.sub(r"^[\d\-\*\.\s]+", "", line).strip()
        if not line:
            continue
        parts = re.split(r"(?<=[.!?])\s+", line)
        for p in parts:
            p = p.strip()
            if p and len(p) > 2:
                examples.append(p)
    return examples


def get_examples(client: OpenAI, n: int, expr: str) -> list[str]:
    """Generate French examples using GPT."""
    trace(f"Requesting {n} examples for '{expr}' using {MODEL_EXAMPLES}")
    system_prompt = (
        "Tu es un professeur de français. "
        "Génère des phrases d'exemple courtes, naturelles, en français uniquement."
    )
    user_prompt = (
        f"Donne {n} phrases d'exemple différentes en français qui utilisent naturellement "
        f"l'expression « {expr} ».\n"
        f"Réponds avec exactement {n} lignes, sans numéros, ni texte supplémentaire."
    )

    resp = client.chat.completions.create(
        model=MODEL_EXAMPLES,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
    )

    content = resp.choices[0].message.content or ""
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    examples = clean_and_split_examples(lines)
    trace(f"Got {len(examples)} French examples")
    return examples[:n]


def translate_all_to_english(client: OpenAI, french_sentences: list[str]) -> list[str]:
    """Translate all French sentences to English in one API call."""
    if not french_sentences:
        return []
    joined_text = "\n".join(french_sentences)
    trace(f"Translating {len(french_sentences)} sentences with {MODEL_TRANSLATE}")

    system_prompt = (
        "You are a precise and concise French-to-English translator. "
        "Translate each line into clear, natural English. "
        "Return the translations in the same order, one per line."
    )
    user_prompt = f"Translate the following French sentences:\n{joined_text}"

    resp = client.chat.completions.create(
        model=MODEL_TRANSLATE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    translations_raw = resp.choices[0].message.content or ""
    translations = [ln.strip() for ln in translations_raw.splitlines() if ln.strip()]
    trace(f"Got {len(translations)} translation lines")

    if len(translations) < len(french_sentences):
        translations += [""] * (len(french_sentences) - len(translations))
    return translations


def main():
    global TRACE_ENABLED
    args = sys.argv[1:]
    if "--trace" in args:
        TRACE_ENABLED = True
        args.remove("--trace")
        trace("Trace mode enabled")

    if len(args) < 2:
        print("Usage: python3 generate-french-examples.py [--trace] <number-of-examples> \"<french-expression>\"")
        sys.exit(1)

    try:
        n = int(args[0])
    except ValueError:
        print("[ERROR] First argument must be an integer.", file=sys.stderr)
        sys.exit(1)

    expr = " ".join(args[1:]).strip()
    trace(f"Args -> n={n}, expr='{expr}'")

    # Determine .txt filename
    base_name = expr.replace(" ", "_").replace("'", "_")
    txt_path = Path(f"{base_name}.txt")

    api_key = load_api_key()
    client = OpenAI(api_key=api_key)

    # If .txt exists, load it; otherwise, generate
    if txt_path.exists():
        trace(f"Using cached examples from {txt_path}")
        content = txt_path.read_text(encoding="utf-8")
        examples = [line.strip() for line in content.splitlines() if line.strip()]
    else:
        try:
            examples = get_examples(client, n, expr)
            txt_path.write_text("\n".join(examples), encoding="utf-8")
            trace(f"Wrote new examples to {txt_path}")
        except Exception as e:
            print(f"[ERROR] Example generation failed: {e}", file=sys.stderr)
            sys.exit(2)

    try:
        translations = translate_all_to_english(client, examples)
    except Exception as e:
        print(f"[ERROR] Translation failed: {e}", file=sys.stderr)
        translations = [""] * len(examples)

    esc_expr = html.escape(expr)

    # ---- HTML OUTPUT ----
    print(f'<div class="french-examples" style="text-align:center;">')
    print(f'  <h3>Exemples pour « {esc_expr} »</h3>')
    print('  <table style="margin:auto; border-collapse:collapse; border:1px solid #ccc;">')
    for ex, en in zip(examples, translations):
        print('    <tr style="border:1px solid #ccc;">')
        print('      <td style="text-align:left; padding:10px; border:1px solid #ccc;">')
        print(f'        {html.escape(ex)}<br><em>{html.escape(en)}</em>')
        print('      </td>')
        print('    </tr>')
    print('  </table>')
    print('</div>')

    trace("Program done")


if __name__ == "__main__":
    main()

