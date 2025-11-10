
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Debug: see which Python we’re actually using
print("WSGI Python:", sys.executable, file=sys.stderr)

# Make sure Python can find your app
sys.path.insert(0, '/var/www/FrFlashCards')

# Load your ~/.env for NEON_DATABASE_URL
dotenv_path = Path.home() / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# Import your Flask app
from api_app import app as application

