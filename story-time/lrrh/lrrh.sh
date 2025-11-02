#!/usr/bin/env bash
# Generate all MP3s needed by lrrh.html using your single-file TTS tool.
# Requires: OPENAI_API_KEY set and ../tools/make_mp3_single.py available.

set -euo pipefail

TTS="../tools/make_mp3_single.py"
INSTR="clear, formal, use a woman's voice"

# ---- Full story (as presented on the page) ----
FULL="Un jour, le Petit Chaperon rouge est allée voir sa grand-mère. Elle porte un panier avec un couteau, une baguette, du fromage et une bouteille de vin. C’est un cadeau pour sa grand-mère. Bientôt, elle va frapper à la porte et elle va dire bonjour."
python "$TTS" "lrrh_full" "$INSTR" "$FULL"

# ---- Per-phrase audio (match lrrh.html data-audio filenames exactly) ----
python "$TTS" "lrrh_un_jour"              "$INSTR" "Un jour"
python "$TTS" "lrrh_petit_chaperon_rouge" "$INSTR" "le Petit Chaperon rouge"
python "$TTS" "lrrh_est_allee_voir"       "$INSTR" "est allée voir"
python "$TTS" "lrrh_sa_grand_mere"        "$INSTR" "sa grand-mère"

python "$TTS" "lrrh_porte"                "$INSTR" "porte"
python "$TTS" "lrrh_un_panier"            "$INSTR" "un panier"
python "$TTS" "lrrh_un_couteau"           "$INSTR" "un couteau"
python "$TTS" "lrrh_une_baguette"         "$INSTR" "une baguette"
python "$TTS" "lrrh_du_fromage"           "$INSTR" "du fromage"
python "$TTS" "lrrh_une_bouteille_de_vin" "$INSTR" "une bouteille de vin"

python "$TTS" "lrrh_cest_un_cadeau"       "$INSTR" "C’est un cadeau"
python "$TTS" "lrrh_pour_sa_grand_mere"   "$INSTR" "pour sa grand-mère"

python "$TTS" "lrrh_bientot"              "$INSTR" "Bientôt"
python "$TTS" "lrrh_va_frapper"           "$INSTR" "va frapper"
python "$TTS" "lrrh_va_dire_bonjour"      "$INSTR" "va dire bonjour"

echo "✅ All MP3s generated."

