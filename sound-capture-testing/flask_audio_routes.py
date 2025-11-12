# Flask route for audio capture
# Add this to your Flask application (e.g., app.py)

from flask import Flask, request, jsonify
import os
from datetime import datetime

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """
    Handle audio file uploads from the audio-capture.html page.
    Saves WAV files to the recordings directory.
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    
    # Create recordings directory if it doesn't exist
    recordings_dir = 'recordings'
    os.makedirs(recordings_dir, exist_ok=True)
    
    # Save the file
    filename = audio_file.filename
    filepath = os.path.join(recordings_dir, filename)
    audio_file.save(filepath)
    
    # Optional: You can process the audio here
    # For example, using speech_recognition, pydub, etc.
    
    return jsonify({
        'status': 'success',
        'filename': filename,
        'path': filepath
    })


# Optional: Route to serve the audio capture page
@app.route('/audio-capture')
def audio_capture():
    return render_template('audio-capture.html')


# Optional: Route to list all recordings
@app.route('/recordings', methods=['GET'])
def list_recordings():
    """
    List all audio recordings in the recordings directory.
    """
    recordings_dir = 'recordings'
    
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
