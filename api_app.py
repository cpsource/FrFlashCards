from flask import Flask, request, jsonify, send_file, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

import os
import psycopg2
import psycopg
import sys
import io

# Get top-level flask object
app = Flask(__name__)
# Set the secret key from environment variable
app.secret_key = os.getenv('FLASK_SECRET_KEY')
# Optional: Add a check to make sure it's set
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY not found in environment variables!")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect here if not logged in

# Define your User class
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

# User loader - Flask-Login uses this to reload user from session
@login_manager.user_loader
def load_user(user_id):
    # Load user from your database
    # This is called on every request for logged-in users
    # For now, a simple example:
    conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL'))
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    conn.close()

    if result:
        return User(id=result[0], username=result[1], email=result[2])
    return None

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check credentials (you should hash passwords!)
        conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL'))
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash FROM users WHERE username = %s",
            (username,)
        )
        result = cur.fetchone()
        conn.close()
        
        if result and check_password_hash(result[3], password):
            user = User(id=result[0], username=result[1], email=result[2])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials", 401
    
    # Return login form HTML
    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Username">
            <input type="password" name="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
    '''

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Protected route example
@app.route('/dashboard')
@login_required
def dashboard():
    return f"Hello {current_user.username}!"

@app.route("/")
def index():
    return {"message": "API root is alive."}

@app.route("/hello")
def hello():
    return {"message": "Hello from Flask!"}

@app.route("/time")
@login_required
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
@login_required
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

#
# Audio Capture
#

# Flask route for audio capture
# Add this to your Flask application (e.g., app.py)

from datetime import datetime
from openai import OpenAI

# Create client only once when first needed
_client = None

def get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    return _client

# Initialize OpenAI client
#client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/upload-audio', methods=['POST'])
@login_required
def upload_audio():
    """
    Handle audio file uploads from the audio-capture.html page.
    Transcribes the audio using Whisper and provides pronunciation feedback using GPT-4.
    """
    client = get_openai_client()
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    
    # Get the expected text from the form data
    expected_text = request.form.get('expected_text', '').strip()
    
    # Create recordings directory if it doesn't exist
    recordings_dir = '/var/www/FrFlashCards/recordings'
    os.makedirs(recordings_dir, exist_ok=True)
    
    # Save the file
    filename = audio_file.filename
    filepath = os.path.join(recordings_dir, filename)
    audio_file.save(filepath)
    
    try:
        # Transcribe with Whisper
        with open(filepath, 'rb') as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="fr"  # Specify French for better accuracy
            )
        
        transcribed_text = transcript.text
        
        # Get pronunciation feedback from GPT-4
        feedback = get_pronunciation_feedback(transcribed_text, expected_text)
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'transcription': transcribed_text,
            'feedback': feedback,
            'expected': expected_text
        })
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing audio: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


def get_pronunciation_feedback(transcribed, expected):
    """
    Use GPT-4 to compare transcription with expected text
    and provide helpful, encouraging feedback.
    
    Args:
        transcribed: What Whisper heard from the user
        expected: What the user was trying to say
        
    Returns:
        Friendly feedback string
    """

    # Get client when needed
    client = get_openai_client()
    
    if not expected:
        # If no expected text provided, just acknowledge what was said
        return f"Great job! I heard: '{transcribed}'"
    
    # Normalize for comparison (case-insensitive, basic punctuation)
    transcribed_normalized = transcribed.lower().strip().rstrip('.')
    expected_normalized = expected.lower().strip().rstrip('.')
    
    # If they match closely, give enthusiastic praise
    if transcribed_normalized == expected_normalized:
        praise_messages = [
            "Perfect! Your pronunciation was excellent! 🎉",
            "Bravo! That was spot-on! 👏",
            "Excellent work! You nailed it! ⭐",
            "Outstanding! Your French pronunciation is great! 🌟"
        ]
        import random
        return random.choice(praise_messages)
    
    # Otherwise, get detailed feedback from GPT-4
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # or use gpt-4o-mini for lower cost
            messages=[
                {
                    "role": "system",
                    "content": """You are a friendly, encouraging French pronunciation tutor. 
                    Compare what the student said with what they were trying to say.
                    Provide brief, specific, and encouraging feedback.
                    
                    Guidelines:
                    - Keep feedback to 2-3 sentences maximum
                    - Start with something positive if possible
                    - Point out specific pronunciation differences
                    - Give a concrete tip for improvement
                    - Use simple language, avoid technical phonetic terms
                    - Be warm and encouraging, never critical or harsh
                    - If they were close, emphasize what they did well
                    
                    Example good feedback:
                    "Good effort! You said 'le shat' but it should be 'le chat'. The 'ch' in French makes a 'sh' sound, like in 'shoe'. Try saying it again with that softer 'sh' sound!"
                    """
                },
                {
                    "role": "user",
                    "content": f"""Expected: "{expected}"
Student said: "{transcribed}"

Provide brief, encouraging pronunciation feedback."""
                }
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error getting GPT feedback: {str(e)}")
        # Fallback message if GPT call fails
        return f"You said '{transcribed}', trying to say '{expected}'. Keep practicing!"


# Optional: Route to list all recordings
@app.route('/recordings', methods=['GET'])
@login_required
def list_recordings():
    """
    List all audio recordings in the recordings directory.
    Useful for reviewing past practice sessions.
    """
    recordings_dir = '/var/www/FrFlashCards/recordings'
    
    if not os.path.exists(recordings_dir):
        return jsonify({'recordings': []})
    
    files = []
    for filename in os.listdir(recordings_dir):
        if filename.endswith('.wav'):
            filepath = os.path.join(recordings_dir, filename)
            files.append({
                'filename': filename,
                'size': os.path.getsize(filepath),
                'created': os.path.getctime(filepath)
            })
    
    # Sort by creation time, newest first
    files.sort(key=lambda x: x['created'], reverse=True)
    
    return jsonify({'recordings': files})


# Optional: Route to delete old recordings (for cleanup)
@app.route('/recordings/<filename>', methods=['DELETE'])
@login_required
def delete_recording(filename):
    """
    Delete a specific recording file.
    Useful for cleaning up storage.
    """
    recordings_dir = '/var/www/FrFlashCards/recordings'
    filepath = os.path.join(recordings_dir, filename)
    
    # Security: ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'status': 'success', 'message': f'Deleted {filename}'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


"""
SETUP INSTRUCTIONS:

1. Install required packages:
   pip3 install openai python-dotenv --break-system-packages

2. Create a .env file in your project root:
   OPENAI_API_KEY=sk-your-actual-api-key-here

3. Add .env to your .gitignore file (IMPORTANT for security):
   echo ".env" >> .gitignore

4. Make sure the recordings directory exists and has correct permissions:
   sudo mkdir -p /var/www/FrFlashCards/recordings
   sudo chown www-data:www-data /var/www/FrFlashCards/recordings
   sudo chmod 755 /var/www/FrFlashCards/recordings

5. Restart Apache:
   sudo systemctl restart apache2

COST ESTIMATE:
- Whisper API: ~$0.006 per minute of audio
- GPT-4o: ~$0.0025-0.005 per feedback request
- For 100 practice sessions (average 10 seconds each): ~$0.30-0.50 total

TROUBLESHOOTING:
- If you get "No module named 'openai'", run the pip install command again
- If you get authentication errors, check your API key in the .env file
- If transcription is poor quality, ensure audio is clear and in French
- Check Apache error logs: sudo tail -f /var/log/apache2/error.log
"""

@app.route('/pronounce', methods=['POST'])
@login_required
def pronounce():
    """
    Generate high-quality French pronunciation using OpenAI TTS.
    Returns an MP3 audio file.
    
    Cost: ~$0.015 per 1000 characters (~$0.0003 per phrase)
    """
    text = request.json.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        client = get_openai_client()
        
        # Generate speech using OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
            input=text,
            speed=0.9  # Slightly slower for learning
        )
        
        # Return the audio file
        audio_bytes = io.BytesIO(response.content)
        audio_bytes.seek(0)
        
        return send_file(
            audio_bytes,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='pronunciation.mp3'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

"""
To use OpenAI TTS instead of browser TTS, update the JavaScript in audio-capture.html:

async function playPronunciation() {
    const expectedText = phraseInput.value.trim();
    
    if (!expectedText) {
        showMessage('Please enter a phrase first', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/pronounce', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: expectedText })
        });
        
        if (response.ok) {
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
        } else {
            showMessage('Error generating pronunciation', 'error');
        }
    } catch (err) {
        console.error('Error:', err);
        showMessage('Error generating pronunciation', 'error');
    }
}

COMPARISON:
Browser TTS:
✓ Free
✓ Instant
✓ Works offline
✗ Voice quality varies
✗ Limited French accents

OpenAI TTS:
✓ Professional quality
✓ Natural French accent
✓ Consistent across devices
✗ Costs ~$0.0003 per phrase
✗ Requires API call
"""
    
