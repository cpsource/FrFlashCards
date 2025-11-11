#/mnt/myproject/bin/python

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# https://stackoverflow.com/questions/42661771/how-to-get-mod-wsgi-to-pick-up-my-virtualenv
sys.path.insert(0,"/mnt/myproject/lib/python3.12/site-packages")

# Make sure Python can find your app
sys.path.insert(0, '/var/www/FrFlashCards')

# Debug: see which Python we’re actually using
#print("WSGI Python:", sys.executable, file=sys.stderr)

# Load your ~/.env for NEON_DATABASE_URL
dotenv_path = Path("/etc/frflashy/.env")

try:
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        if os.getenv("NEON_DATABASE_URL"):
            print(f"[INFO] Loaded environment from {dotenv_path}", file=sys.stderr)
        else:
            print(f"[ERROR] {dotenv_path} loaded, but NEON_DATABASE_URL is missing", file=sys.stderr)
    else:
        raise FileNotFoundError(f"{dotenv_path} not found")

except Exception as e:
    print(f"[FATAL] Failed to load environment: {e}", file=sys.stderr)

# Import your Flask app
from api_app import app as application

