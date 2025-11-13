#!/bin/bash
# Find all backup files
cd /var/www/FrFlashCards
find . -name "*~" -o -name "*.bak" -o -name "*.old" -o -name "#*#"

# Delete them
find . -name "*~" -delete
find . -name "*.bak" -delete
find . -name "*.old" -delete
find . -name "#*#" -delete
