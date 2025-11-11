#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
    python make-examples.py vocab.csv

Reads a CSV whose middle column is the French expression. For each expression:

- Counts how many rows already exist in the `examples` table for that expression.
- If there are already 3 or more, it skips that expression.
- Otherwise, it asks the OpenAI API to generate simple A1/A2-level examples
  (French sentence + English translation) and inserts rows into:

    examples(expression, french, english)

until there are 3 total for that expression.
"""

import csv
import sys
import os
import json
import logging
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI


# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("make-examples")


# ---------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------
def load_environment():
    """
    Load environment variables from a known .env location,
    then from default search locations as fallback.
    """
    # Try /etc/frflashy/.env first (your current setup),
    # then fall back to default load_dotenv() behavior.
    explicit_path = Path("/home/ubuntu/.env")
    if explicit_path.exists():
        load_dotenv(explicit_path)
        logger.info(f"Loaded environment from {explicit_path}")
    else:
        load_dotenv()
        logger.info("Loaded environment from default .env search path")

    dsn = os.getenv("NEON_DATABASE_URL")
    if not dsn:
        logger.error("NEON_DATABASE_URL is not set in environment")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY is not set in environment")
        sys.exit(1)

    return dsn


# ---------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------
def get_existing_count(cur, expression: str) -> int:
    cur.execute(
        "SELECT COUNT(*) FROM examples WHERE expression = %s",
        (expression,),
    )
    (count,) = cur.fetchone()
    return int(count)


def insert_example(cur, expression: str, french: str, english: str) -> None:
    cur.execute(
        """
        INSERT INTO examples (expression, french, english)
        VALUES (%s, %s, %s)
        """,
        (expression, french, english),
    )


# ---------------------------------------------------------------------
# AI helper
# ---------------------------------------------------------------------
def generate_example(client: OpenAI, expression: str) -> tuple[str, str]:
    """
    Ask the OpenAI API to generate ONE simple French sentence
    using the given expression, plus its English translation.

    Returns:
        (french_sentence, english_sentence)
    """
    system_msg = (
        "You are helping A1/A2 French learners. "
        "Given a French expression, you will produce exactly one simple, natural "
        "French sentence using that expression, and its English translation. "
        "Use present, passé composé, or futur proche only. "
        "Respond in strict JSON with keys 'french' and 'english'."
    )

    user_msg = (
        f"Expression: {expression}\n\n"
        "Return JSON like:\n"
        '{ "french": "…", "english": "…" }'
    )

    # Using chat.completions; adjust model name if you prefer another
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from model: %s", e)
        logger.error("Raw content was: %r", content)
        raise

    french = data.get("french", "").strip()
    english = data.get("english", "").strip()

    if not french or not english:
        raise ValueError(f"Model response missing fields: {data!r}")

    return french, english


# ---------------------------------------------------------------------
# CSV handling
# ---------------------------------------------------------------------
def iter_french_expressions(csv_path: Path):
    """
    Yield the French (middle) column from each row in the CSV.

    Assumes:
        col[0] = English
        col[1] = French
        col[2] = Gender (or something else)
    """
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue
            # Skip header if it looks like one
            if i == 0 and any("french" in c.lower() for c in row):
                continue
            if len(row) < 2:
                continue
            french = row[1].strip()
            if not french:
                continue
            yield french


# ---------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python make-examples.py <csv-file>", file=sys.stderr)
        sys.exit(1)

    csv_arg = Path(sys.argv[1])
    if not csv_arg.exists():
        logger.error("CSV file not found: %s", csv_arg)
        sys.exit(1)

    dsn = load_environment()
    client = OpenAI()  # uses OPENAI_API_KEY from environment

    # Connect to Neon/Postgres
    logger.info("Connecting to database...")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for expression in iter_french_expressions(csv_arg):
                logger.info("Processing expression: %r", expression)

                try:
                    count = get_existing_count(cur, expression)
                except Exception as e:
                    logger.error(
                        "Failed to get existing count for %r: %s",
                        expression, e
                    )
                    continue

                if count >= 3:
                    logger.info(
                        "Already have %d examples for %r; skipping.",
                        count, expression
                    )
                    continue

                needed = 3 - count
                logger.info(
                    "Need %d more example(s) for %r.",
                    needed, expression
                )

                for n in range(needed):
                    try:
                        french, english = generate_example(client, expression)
                        logger.info(
                            "Generated example %d for %r: FR=%r EN=%r",
                            count + n + 1, expression, french, english
                        )
                        insert_example(cur, expression, french, english)
                    except Exception as e:
                        logger.error(
                            "Failed to generate/insert example for %r: %s",
                            expression, e
                        )
                        # continue to next expression; don't crash the whole run
                        break

            # connection context manager will commit if no uncaught exception


if __name__ == "__main__":
    main()

