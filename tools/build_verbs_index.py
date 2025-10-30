#!/usr/bin/env python3
"""
Build Verbs Index Page
This script scans a directory for HTML files and creates an index page (verbs.html)
in the current directory with links pointing to files in the verbs/ subdirectory.
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
        
        # If no good description found, create one from title or filename
        if not description or len(description) < 20:
            filename_lower = filepath.lower()
            if "lent" in filename_lower and "lentement" in filename_lower:
                description = "Learn the difference between the adjective 'lent' (slow) and the adverb 'lentement' (slowly) in French."
            elif "mangeur" in filename_lower:
                description = "Understand how French transforms verbs into nouns using the -eur suffix, with 'mangeur' as an example."
            elif "helpful" in filename_lower or "hint" in filename_lower:
                description = "Collection of audio recommendations and resources to improve French listening, vocabulary, and pronunciation."
            elif "verb" in filename_lower or "conjugat" in filename_lower:
                description = "French verb conjugation patterns and practice exercises."
            elif "tense" in filename_lower:
                description = "Understanding French verb tenses and their proper usage."
            else:
                description = f"French learning resource: {title}"
        
        return title, description
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        filename = Path(filepath).stem.replace('-', ' ').replace('_', ' ').title()
        return filename, "French learning resource"

def generate_index_page(source_directory, output_filename="verbs.html", subdirectory_name="verbs"):
    """
    Generate the index HTML page.
    
    Args:
        source_directory: Directory containing HTML files to index
        output_filename: Name of the output file (default: verbs.html)
        subdirectory_name: Name of subdirectory for links (default: verbs)
    """
    
    # Get all HTML files except the output file
    html_files = []
    for file in os.listdir(source_directory):
        if file.endswith('.html') and file != output_filename:
            html_files.append(file)
    
    # Sort files alphabetically
    html_files.sort()
    
    # Extract information from each file
    file_data = []
    for filename in html_files:
        filepath = os.path.join(source_directory, filename)
        title, description = extract_file_info(filepath)
        file_data.append({
            'filename': filename,
            'title': title,
            'description': description
        })
    
    # Determine the page title based on the output filename
    if "verb" in output_filename.lower():
        page_title = "French Verb Resources"
        page_subtitle = "Master French verb conjugations and usage"
    elif "hint" in output_filename.lower():
        page_title = "French Learning Hints"
        page_subtitle = "Your comprehensive guide to mastering French grammar and vocabulary"
    else:
        page_title = "French Learning Resources"
        page_subtitle = "Explore our collection of French learning materials"
    
    # Generate the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} - Resource Index</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {{
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header-section {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 40px;
            text-align: center;
        }}
        h1 {{
            color: #764ba2;
            font-size: 2.8em;
            margin-bottom: 20px;
        }}
        .subtitle {{
            color: #666;
            font-size: 1.2em;
            font-style: italic;
        }}
        .resource-table {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .table {{
            margin-bottom: 0;
        }}
        .table thead th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 20px;
            font-size: 1.2em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .table tbody tr {{
            transition: all 0.3s ease;
        }}
        .table tbody tr:hover {{
            background: #f8f9fa;
            transform: translateX(5px);
        }}
        .table tbody td {{
            padding: 20px;
            vertical-align: middle;
            border-top: 1px solid #dee2e6;
        }}
        .resource-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #764ba2;
            text-decoration: none;
            display: block;
            margin-bottom: 5px;
        }}
        .resource-title:hover {{
            color: #667eea;
            text-decoration: underline;
        }}
        .resource-description {{
            color: #666;
            font-size: 0.95em;
            line-height: 1.5;
        }}
        .resource-number {{
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
        }}
        .stats-section {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .stat-item {{
            display: inline-block;
            margin: 0 30px;
            color: #764ba2;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}
        .footer-section {{
            text-align: center;
            margin-top: 40px;
            color: white;
        }}
        .btn-return {{
            margin-top: 20px;
        }}
        @media (max-width: 768px) {{
            .resource-number {{
                width: 40px;
                height: 40px;
                font-size: 1em;
            }}
            h1 {{
                font-size: 2em;
            }}
            .table tbody td {{
                padding: 15px 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <h1>📚 {page_title} 📚</h1>
            <p class="subtitle">{page_subtitle}</p>
        </div>
        
        <div class="resource-table">
            <table class="table">
                <thead>
                    <tr>
                        <th style="width: 80px; text-align: center;">#</th>
                        <th>Resource</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # Add table rows with links pointing to subdirectory
    for i, data in enumerate(file_data, 1):
        # Create the link path with subdirectory
        link_path = f"{subdirectory_name}/{data['filename']}"
        html_content += f"""
                    <tr>
                        <td style="text-align: center;">
                            <div class="resource-number">{i}</div>
                        </td>
                        <td>
                            <a href="{link_path}" class="resource-title">{data['title']}</a>
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
    
    # Write the HTML file in the current directory
    output_path = output_filename
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Successfully created {output_path} in current directory")
        print(f"📊 Added {len(file_data)} resources to the index")
        print(f"🔗 Links point to: {subdirectory_name}/*.html")
        return True
    except Exception as e:
        print(f"❌ Error writing {output_filename}: {e}")
        return False

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python build_index.py <directory> [output_filename] [subdirectory_name]")
        print("Examples:")
        print("  python build_index.py ./verbs")
        print("  python build_index.py ./verbs verbs.html verbs")
        print("  python build_index.py ./hints hints.html hints")
        sys.exit(1)
    
    source_directory = sys.argv[1]
    
    # Optional arguments
    output_filename = sys.argv[2] if len(sys.argv) > 2 else "verbs.html"
    subdirectory_name = sys.argv[3] if len(sys.argv) > 3 else "verbs"
    
    # Check if directory exists
    if not os.path.isdir(source_directory):
        print(f"Error: '{source_directory}' is not a valid directory")
        sys.exit(1)
    
    # Check if there are HTML files
    html_files = [f for f in os.listdir(source_directory) if f.endswith('.html') and f != output_filename]
    if not html_files:
        print(f"Warning: No HTML files found in '{source_directory}' (excluding {output_filename})")
        print("The index page will be created but will be empty.")
    
    print(f"🔍 Scanning directory: {source_directory}")
    print(f"📄 Found {len(html_files)} HTML files to index")
    print(f"📝 Output file: {output_filename} (in current directory)")
    print(f"📁 Links will point to: {subdirectory_name}/*.html")
    
    # Generate the index page
    if generate_index_page(source_directory, output_filename, subdirectory_name):
        print(f"✨ Index page '{output_filename}' created successfully in current directory!")
    else:
        print(f"Failed to create index page")
        sys.exit(1)

if __name__ == "__main__":
    main()
