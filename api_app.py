from flask import Flask, request, jsonify
import os
import psycopg
import sys

app = Flask(__name__)

@app.route("/")
def index():
    return {"message": "API root is alive."}

@app.route("/hello")
def hello():
    return {"message": "Hello from Flask!"}

@app.route("/time")
def db_time():
    """Return current time from Neon/Postgres"""
    dsn = os.getenv("NEON_DATABASE_URL")
    if not dsn:
        return jsonify(error="NEON_DATABASE_URL not set"), 500

    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW()")
                (now,) = cur.fetchone()
        return jsonify(now=str(now))
    except Exception as e:
        return jsonify(error=str(e)), 500

# --- Get the Neon database URL ---
DSN = os.getenv("NEON_DATABASE_URL")
if not DSN:
    raise RuntimeError("❌ NEON_DATABASE_URL not found in ~/.env or environment")
    
def get_conn():
    return psycopg.connect(DSN, autocommit=True)
    
@app.route("/examples")
def get_examples():
    """
    Example: GET /api/examples?expression=le%20manteau
    Returns: JSON array of french/english examples
    """
    expression = request.args.get("expression", "").strip()
    if not expression:
        return jsonify({"error": "missing expression parameter"}), 400

    rows = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT french, english
                FROM examples
                WHERE expression = %s
                ORDER BY id
                """,
                (expression,),
            )
            for french, english in cur.fetchall():
                rows.append({"french": french, "english": english})

    return jsonify({"expression": expression, "examples": rows})
