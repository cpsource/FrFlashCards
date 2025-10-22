#!/bin/bash
# Auto-generated script to build web pages
# Generated from 12 .mp3 files in lesanimaux

set -e  # Exit on error

python tools/bldwebpage.py "lesanimaux/en-lapin.png" "lesanimaux/en-lapin.mp3" "en lapin" 1 12
python tools/bldwebpage.py "lesanimaux/un-canari.png" "lesanimaux/un-canari.mp3" "un canari" 2 12
python tools/bldwebpage.py "lesanimaux/un-chat.png" "lesanimaux/un-chat.mp3" "un chat" 3 12
python tools/bldwebpage.py "lesanimaux/un-chien.png" "lesanimaux/un-chien.mp3" "un chien" 4 12
python tools/bldwebpage.py "lesanimaux/un-cochon-d'lnde.png" "lesanimaux/un-cochon-d'lnde.mp3" "un cochon d'lnde" 5 12
python tools/bldwebpage.py "lesanimaux/un-furet.png" "lesanimaux/un-furet.mp3" "un furet" 6 12
python tools/bldwebpage.py "lesanimaux/un-hamster.png" "lesanimaux/un-hamster.mp3" "un hamster" 7 12
python tools/bldwebpage.py "lesanimaux/un-oiseau.png" "lesanimaux/un-oiseau.mp3" "un oiseau" 8 12
python tools/bldwebpage.py "lesanimaux/un-perroquet.png" "lesanimaux/un-perroquet.mp3" "un perroquet" 9 12
python tools/bldwebpage.py "lesanimaux/un-poisson-rouge.png" "lesanimaux/un-poisson-rouge.mp3" "un poisson rouge" 10 12
python tools/bldwebpage.py "lesanimaux/une-perruche.png" "lesanimaux/une-perruche.mp3" "une perruche" 11 12
python tools/bldwebpage.py "lesanimaux/une-tortue.png" "lesanimaux/une-tortue.mp3" "une tortue" 12 12

echo 'All pages built successfully!'
