# Flask route for audio capture with OpenAI Whisper transcription and GPT-4 feedback
# Add this to your Flask application (e.g., app.py)

from flask import Flask, request, jsonify
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """
    Handle audio file uploads from the audio-capture.html page.
    Transcribes the audio using Whisper and provides pronunciation feedback using GPT-4.
    """
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
@app.route('/api/recordings', methods=['GET'])
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
@app.route('/api/recordings/<filename>', methods=['DELETE'])
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
