#!/usr/bin/env python3
"""
bldwebpage.py - Generates a Bootstrap v4 webpage with an image, audio button, and text
Usage: python bldwebpage.py <image.png> <audio.mp3> <text> <test_number> <max_number>
"""

import sys
import os

def generate_html(image_path, audio_path, text, test_number, max_number):
    """Generate HTML content with Bootstrap v4"""
    
    # Calculate next test number (wrap to 1 if exceeds max)
    next_number = 1 if test_number + 1 > max_number else test_number + 1
    
    # Determine the next page filename
    if next_number == 1:
        next_page = "fr-flash.html"
    else:
        next_page = f"tst-{next_number}.html"
    
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nommez cette Image</title>
    <!-- Bootstrap v4 CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {{
            padding: 20px;
        }}
        .image-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .main-image {{
            width: 75%;
            max-width: 75%;
            height: auto;
        }}
        .button-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .answer-text {{
            text-align: center;
            margin-top: 20px;
            font-size: 1.2em;
            display: none;
        }}
        .next-button-container {{
            text-align: center;
            margin-top: 30px;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center my-4">Nommez cette Image</h1>
        
        <div class="image-container">
            <img src="{image_path}" alt="Image à identifier" class="main-image img-fluid">
        </div>
        
        <div class="button-container">
            <button id="answerBtn" class="btn btn-primary btn-lg">Cliquez pour la Réponse</button>
        </div>
        
        <div id="answerText" class="answer-text">
            <p class="lead">{text}</p>
        </div>
        
        <div id="nextButtonContainer" class="next-button-container">
            <button id="repeatBtn" class="btn btn-warning btn-lg mr-3">Répéter</button>
            <a href="{next_page}" class="btn btn-success btn-lg">Image Suivante</a>
        </div>
        
        <audio id="audioPlayer" style="display: none;">
            <source src="{audio_path}" type="audio/mpeg">
            Votre navigateur ne supporte pas l'élément audio.
        </audio>
    </div>

    <!-- jQuery and Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        document.getElementById('answerBtn').addEventListener('click', function() {{
            // Play the audio
            var audio = document.getElementById('audioPlayer');
            audio.play();
            
            // Show the answer text
            document.getElementById('answerText').style.display = 'block';
            
            // Show the next button
            document.getElementById('nextButtonContainer').style.display = 'block';
            
            // Optionally disable the button after clicking
            this.disabled = true;
            this.textContent = 'Réponse révélée';
        }});
        
        // Repeat button functionality
        document.getElementById('repeatBtn').addEventListener('click', function() {{
            // Hide the answer text
            document.getElementById('answerText').style.display = 'none';
            
            // Hide the button container
            document.getElementById('nextButtonContainer').style.display = 'none';
            
            // Re-enable and reset the answer button
            var answerBtn = document.getElementById('answerBtn');
            answerBtn.disabled = false;
            answerBtn.textContent = 'Cliquez pour la Réponse';
            
            // Stop and reset audio
            var audio = document.getElementById('audioPlayer');
            audio.pause();
            audio.currentTime = 0;
        }});
    </script>
</body>
</html>"""
    
    return html_content

def main():
    if len(sys.argv) != 6:
        print("Usage: python bldwebpage.py <image.png> <audio.mp3> <text> <test_number> <max_number>")
        print("Exemple: python bldwebpage.py photo.png reponse.mp3 'La Tour Eiffel' 1 10")
        sys.exit(1)
    
    image_path = sys.argv[1]
    audio_path = sys.argv[2]
    text = sys.argv[3]
    test_number = int(sys.argv[4])
    max_number = int(sys.argv[5])
    
    # Generate HTML content
    html_content = generate_html(image_path, audio_path, text, test_number, max_number)
    
    # Write to output file with test number
    output_filename = f"tst-{test_number}.html"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Page web générée avec succès: {output_filename}")
    print(f"Ouvrez {output_filename} dans votre navigateur pour voir le résultat.")

if __name__ == "__main__":
    main()
