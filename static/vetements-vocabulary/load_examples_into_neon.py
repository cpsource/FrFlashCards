#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
from pathlib import Path

import psycopg

CSV_PATH = Path("examples.csv")  # adjust if needed

def main():
    dsn = os.environ.get("NEON_DATABASE_URL")
    if not dsn:
        raise SystemExit("NEON_DATABASE_URL not set in environment")

    if not CSV_PATH.exists():
        raise SystemExit(f"{CSV_PATH} not found")

    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, start=1):
                    if len(row) < 3:
                        print(f"Skipping row {row_num}: not enough columns")
                        continue
                    expression = row[0].strip()  # "le manteau"
                    french = row[1].strip()
                    english = row[2].strip()
                    cur.execute(
                        """
                        INSERT INTO examples (expression, french, english)
                        VALUES (%s, %s, %s)
                        """,
                        (expression, french, english),
                    )
                    print(f"Inserted row {row_num}: {expression}")

if __name__ == "__main__":
    main()

