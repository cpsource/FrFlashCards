#!/usr/bin/env python3
"""
Build Hints Index Page
This script scans a directory for HTML files and creates an index page (hints.html)
with links to each file and descriptions extracted from the files.
"""

import os
import sys
import re
from html.parser import HTMLParser
from pathlib import Path

class TitleAndContentExtractor(HTMLParser):
    """HTML parser to extract title and initial content from HTML files."""
    
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.in_title = False
        self.in_body = False
        self.in_h1 = False
        self.in_p = False
        self.in_intro = False
        self.h1_content = ""
        self.p_content = []
        self.text_buffer = ""
        
    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "body":
            self.in_body = True
        elif tag == "h1" and self.in_body:
            self.in_h1 = True
        elif tag == "p" and self.in_body and len(self.p_content) < 2:
            self.in_p = True
        # Check for intro sections or subtitles
        elif tag == "div":
            for attr, value in attrs:
                if attr == "class" and ("intro" in value or "subtitle" in value):
                    self.in_intro = True
    
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
            self.title = self.text_buffer.strip()
            self.text_buffer = ""
        elif tag == "h1":
            self.in_h1 = False
            if self.text_buffer:
                self.h1_content = self.text_buffer.strip()
                self.text_buffer = ""
        elif tag == "p":
            self.in_p = False
            if self.text_buffer and len(self.p_content) < 2:
                # Clean up the text
                cleaned_text = re.sub(r'\s+', ' ', self.text_buffer.strip())
                # Remove emojis and special characters for cleaner description
                cleaned_text = re.sub(r'[^\w\s\-.,!?\'"éèêëàâäôöûüçîï]', '', cleaned_text)
                if cleaned_text and len(cleaned_text) > 10:
                    self.p_content.append(cleaned_text)
            self.text_buffer = ""
        elif tag == "div":
            self.in_intro = False
    
    def handle_data(self, data):
        if self.in_title or self.in_h1 or (self.in_p and self.in_body):
            self.text_buffer += data

def extract_file_info(filepath):
    """Extract title and description from an HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parser = TitleAndContentExtractor()
        parser.feed(content)
        
        # Get title (prefer HTML title tag, fallback to H1)
        title = parser.title or parser.h1_content or "Untitled"
        
        # Clean up title - remove emojis and extra spaces
        title = re.sub(r'[^\w\s\-.,!?\'"éèêëàâäôöûüçîï()]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Get description from paragraphs
        description = ""
        if parser.p_content:
            description = parser.p_content[0]
            # Limit description length
            if len(description) > 150:
                description = description[:147] + "..."
        
        # If no good description found, create one from title
        if not description or len(description) < 20:
            if "lent" in filepath.lower() and "lentement" in filepath.lower():
                description = "Learn the difference between the adjective 'lent' (slow) and the adverb 'lentement' (slowly) in French."
            elif "mangeur" in filepath.lower():
                description = "Understand how French transforms verbs into nouns using the -eur suffix, with 'mangeur' as an example."
            elif "helpful" in filepath.lower() or "hint" in filepath.lower():
                description = "Collection of audio recommendations and resources to improve French listening, vocabulary, and pronunciation."
            else:
                description = f"French learning resource: {title}"
        
        return title, description
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        filename = Path(filepath).stem.replace('-', ' ').replace('_', ' ').title()
        return filename, "French learning resource"

def generate_hints_page(directory):
    """Generate the hints.html index page."""
    
    # Get all HTML files except hints.html
    html_files = []
    for file in os.listdir(directory):
        if file.endswith('.html') and file != 'hints.html':
            html_files.append(file)
    
    # Sort files alphabetically
    html_files.sort()
    
    # Extract information from each file
    file_data = []
    for filename in html_files:
        filepath = os.path.join(directory, filename)
        title, description = extract_file_info(filepath)
        file_data.append({
            'filename': filename,
            'title': title,
            'description': description
        })
    
    # Generate the HTML content
    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>French Learning Hints - Resource Index</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header-section {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 40px;
            text-align: center;
        }
        h1 {
            color: #764ba2;
            font-size: 2.8em;
            margin-bottom: 20px;
        }
        .subtitle {
            color: #666;
            font-size: 1.2em;
            font-style: italic;
        }
        .hints-table {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .table {
            margin-bottom: 0;
        }
        .table thead th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 20px;
            font-size: 1.2em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .table tbody tr {
            transition: all 0.3s ease;
        }
        .table tbody tr:hover {
            background: #f8f9fa;
            transform: translateX(5px);
        }
        .table tbody td {
            padding: 20px;
            vertical-align: middle;
            border-top: 1px solid #dee2e6;
        }
        .resource-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #764ba2;
            text-decoration: none;
            display: block;
            margin-bottom: 5px;
        }
        .resource-title:hover {
            color: #667eea;
            text-decoration: underline;
        }
        .resource-description {
            color: #666;
            font-size: 0.95em;
            line-height: 1.5;
        }
        .resource-number {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.3em;
        }
        .stats-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .stat-item {
            display: inline-block;
            margin: 0 30px;
            color: #764ba2;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }
        .footer-section {
            text-align: center;
            margin-top: 40px;
            color: white;
        }
        .btn-return {
            margin-top: 20px;
        }
        @media (max-width: 768px) {
            .resource-number {
                width: 40px;
                height: 40px;
                font-size: 1em;
            }
            h1 {
                font-size: 2em;
            }
            .table tbody td {
                padding: 15px 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <h1>📚 French Learning Hints 📚</h1>
            <p class="subtitle">Your comprehensive guide to mastering French grammar and vocabulary</p>
        </div>
        
        <div class="hints-table">
            <table class="table">
                <thead>
                    <tr>
                        <th style="width: 80px; text-align: center;">#</th>
                        <th>Resource</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # Add table rows
    for i, data in enumerate(file_data, 1):
        html_content += f"""
                    <tr>
                        <td style="text-align: center;">
                            <div class="resource-number">{i}</div>
                        </td>
                        <td>
                            <a href="{data['filename']}" class="resource-title">{data['title']}</a>
                            <div class="resource-description">{data['description']}</div>
                        </td>
                    </tr>"""
    
    # Close the HTML
    html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="stats-section">
            <div class="stat-item">
                <div class="stat-number">{len(file_data)}</div>
                <div class="stat-label">Total Resources</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">🇫🇷</div>
                <div class="stat-label">Language</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">A1-B2</div>
                <div class="stat-label">Levels Covered</div>
            </div>
        </div>
        
        <div class="footer-section">
            <p>Continue building your French skills with these carefully curated resources!</p>
            <a href="../index.html" class="btn btn-light btn-lg btn-return">
                ↩️ Return to Main Page
            </a>
        </div>
    </div>
    
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    # Write the HTML file
    output_path = os.path.join(directory, 'hints.html')
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Successfully created {output_path}")
        print(f"📊 Added {len(file_data)} resources to the index")
        return True
    except Exception as e:
        print(f"❌ Error writing hints.html: {e}")
        return False

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python build_hints_index.py <directory>")
        print("Example: python build_hints_index.py ./hints")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # Check if directory exists
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        sys.exit(1)
    
    # Check if there are HTML files
    html_files = [f for f in os.listdir(directory) if f.endswith('.html') and f != 'hints.html']
    if not html_files:
        print(f"Warning: No HTML files found in '{directory}' (excluding hints.html)")
        print("The index page will be created but will be empty.")
    
    print(f"🔍 Scanning directory: {directory}")
    print(f"📄 Found {len(html_files)} HTML files to index")
    
    # Generate the hints page
    if generate_hints_page(directory):
        print("✨ Hints index page created successfully!")
    else:
        print("Failed to create hints index page")
        sys.exit(1)

if __name__ == "__main__":
    main()
