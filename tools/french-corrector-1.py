#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
french-corrector.py

Usage:
  python3 french-corrector.py "<student_text>"
  python3 french-corrector.py --explain "<student_text>"

Example:
  python3 french-corrector.py "etre bien dans ses baskets"
  → être bien dans ses baskets
  
  python3 french-corrector.py --explain "etre bien dans ses baskets"
  → être bien dans ses baskets
  
  Corrections made:
  - "etre" → "être": Missing circumflex accent on the verb "être" (to be)
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


def correct_with_explanation(client, student_text):
    """Get correction with explanations."""
    prompt = (
        "Tu es un professeur de français corrigeant la phrase écrite par un élève. "
        "Corrige la grammaire, l'orthographe et ajoute les accents français manquants. "
        "Renvoie d'abord la phrase corrigée, puis sur une nouvelle ligne, "
        "liste chaque correction avec une brève explication en format:\n"
        '- "mot incorrect" → "mot correct": explication\n\n'
        "Si aucune correction n'est nécessaire, renvoie seulement la phrase originale."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": student_text},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


def correct_simple(client, student_text):
    """Get correction without explanations."""
    prompt = (
        "Tu es un professeur de français corrigeant la phrase écrite par un élève. "
        "Corrige la grammaire, l'orthographe et ajoute les accents français manquants, "
        "sans ajouter d'explications ni de texte supplémentaire. "
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

    return response.choices[0].message.content.strip()


def main():
    # Check for --explain flag
    explain = False
    args = sys.argv[1:]
    
    if '--explain' in args:
        explain = True
        args.remove('--explain')
    
    if len(args) < 1:
        print("Usage: python3 french-corrector.py [--explain] \"<student_text>\"")
        print("\nOptions:")
        print("  --explain    Show explanations for corrections")
        print("\nExamples:")
        print('  python3 french-corrector.py "etre bien dans ses baskets"')
        print('  python3 french-corrector.py --explain "etre bien dans ses baskets"')
        sys.exit(1)

    student_text = args[0].strip()
    if not student_text:
        print("")
        sys.exit(0)

    client = OpenAI(api_key=load_api_key())

    if explain:
        result = correct_with_explanation(client, student_text)
    else:
        result = correct_simple(client, student_text)
    
    print(result)


if __name__ == "__main__":
    main()
