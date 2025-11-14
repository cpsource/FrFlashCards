# Optional: High-quality French pronunciation using OpenAI TTS
# Add this route if you want professional-quality French audio instead of browser TTS

from flask import Flask, request, send_file
import os
from openai import OpenAI
import io

@app.route('/pronounce', methods=['POST'])
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
