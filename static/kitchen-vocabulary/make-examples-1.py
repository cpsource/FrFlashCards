#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
    python make-examples.py vocab.csv

Reads a CSV whose middle column is the French expression. For each expression:

- Looks in the `examples` table by `expression`.
- If there are already 3 or more examples, skip that expression.
- Otherwise, call the OpenAI API to generate simple examples (French + English)
  until there are 3 UNIQUE French sentences for that expression.

Table:
    examples(expression, french, english)
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
    Load environment variables from /etc/frflashy/.env if present,
    otherwise fall back to default .env search.
    """
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
def get_existing_french(cur, expression: str) -> set[str]:
    """
    Return a set of French sentences already stored for this expression.
    """
    cur.execute(
        "SELECT french FROM examples WHERE expression = %s",
        (expression,),
    )
    rows = cur.fetchall()
    # We keep exact strings, but you could normalize (strip/lower) if desired
    return {r[0].strip() for r in rows if r and r[0]}


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
        "No slang, no complex tenses. "
        "Respond in strict JSON with keys 'french' and 'english'."
    )

    user_msg = (
        f"Expression: {expression}\n\n"
        "Return JSON like:\n"
        '{ "french": "…", "english": "…" }'
    )

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

    logger.info("Connecting to database...")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for expression in iter_french_expressions(csv_arg):
                logger.info("Processing expression: %r", expression)

                try:
                    existing_french = get_existing_french(cur, expression)
                except Exception as e:
                    logger.error(
                        "Failed to get existing examples for %r: %s",
                        expression, e
                    )
                    continue

                count = len(existing_french)
                if count >= 3:
                    logger.info(
                        "Already have %d examples for %r; skipping.",
                        count, expression
                    )
                    continue

                needed = 3 - count
                logger.info(
                    "Need %d more unique example(s) for %r.",
                    needed, expression
                )

                # Try to generate up to `needed` new UNIQUE examples.
                for n in range(needed):
                    # Allow a few attempts to get a unique sentence
                    max_attempts = 5
                    for attempt in range(1, max_attempts + 1):
                        try:
                            french, english = generate_example(client, expression)
                        except Exception as e:
                            logger.error(
                                "Generation error for %r (attempt %d): %s",
                                expression, attempt, e
                            )
                            french = english = ""
                            # Try again if attempts remain
                            continue

                        if not french:
                            logger.warning(
                                "Empty French sentence for %r (attempt %d); retrying.",
                                expression, attempt
                            )
                            continue

                        if french in existing_french:
                            logger.info(
                                "Got duplicate French example for %r (attempt %d): %r",
                                expression, attempt, french
                            )
                            # Try again if we still have attempts
                            continue

                        # We have a unique French sentence.
                        logger.info(
                            "Inserting example %d for %r: FR=%r EN=%r",
                            count + 1, expression, french, english
                        )
                        insert_example(cur, expression, french, english)
                        existing_french.add(french)
                        count += 1
                        break  # break out of attempts loop, go to next needed example
                    else:
                        # We exhausted attempts without a unique example.
                        logger.warning(
                            "Could not generate a new unique example for %r after %d attempts; moving on.",
                            expression, max_attempts
                        )
                        # Stop trying to add more for this expression; go to next expression
                        break

        # On exiting the context managers, psycopg will commit if no unhandled exception


if __name__ == "__main__":
    main()

