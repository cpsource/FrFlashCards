#!/bin/bash
# Auto-generated script to build web pages
# Generated from 4 .mp3 files in lesanimaux

set -e  # Exit on error

python tools/bldwebpage.py "lesanimaux/un-canari.png" "lesanimaux/un-canari.mp3" "un canari" 1 4
python tools/bldwebpage.py "lesanimaux/un-chien.png" "lesanimaux/un-chien.mp3" "un chien" 2 4
python tools/bldwebpage.py "lesanimaux/un-hamster.png" "lesanimaux/un-hamster.mp3" "un hamster" 3 4
python tools/bldwebpage.py "lesanimaux/un-oiseau.png" "lesanimaux/un-oiseau.mp3" "un oiseau" 4 4

echo 'All pages built successfully!'
