#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
french-corrector.py

Usage:
  python3 french-corrector.py "<student_text>"

Example:
  python3 french-corrector.py "etre bien dans ses baskets"
  → être bien dans ses baskets
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

MODEL = "gpt-4o-mini"

def load_api_key():
    """Load OPENAI_API_KEY from ~/.env or environment."""
    env_path = Path.home() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[FATAL] OPENAI_API_KEY not found in environment.")
        sys.exit(1)
    return api_key


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 french-corrector.py \"<student_text>\"")
        sys.exit(1)

    student_text = sys.argv[1].strip()
    if not student_text:
        print("")
        sys.exit(0)

    client = OpenAI(api_key=load_api_key())

    prompt = (
        "Tu es un professeur de français corrigeant la phrase écrite par un élève. "
        "Corrige la grammaire, l’orthographe et ajoute les accents français manquants, "
        "sans ajouter d’explications ni de texte supplémentaire. "
        "Renvoie seulement la phrase corrigée."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": student_text},
        ],
        temperature=0.2,
    )

    corrected = response.choices[0].message.content.strip()
    print(corrected)


if __name__ == "__main__":
    main()
