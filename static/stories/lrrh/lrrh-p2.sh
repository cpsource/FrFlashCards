#!/usr/bin/env bash
# Generate all MP3s for lrrh-p2.html
# Requires: OPENAI_API_KEY and ../tools/make_mp3_single.py

set -euo pipefail

TTS="../../tools/make_mp3_single.py"
INSTR="clear, formal, use a woman's voice"

# ---- Full page text (page 2) ----
FULL_P2="Le Petit Chaperon rouge voit sa grand-mère et dit : « quels grands yeux tu as ! ». Le loup répond : « C’est pour mieux te voir. ». Puis elle dit : « quelles grandes dents tu as ! ». Et là, le loup a sauté du lit. Le Petit Chaperon rouge a pris le couteau du panier et a tué le loup. Fin."
python "$TTS" "lrrh_p2_full" "$INSTR" "$FULL_P2"

# ---- Per-phrase audios (filenames must match data-audio in HTML) ----
python "$TTS" "lrrh2_voit_grand_mere"        "$INSTR" "Le Petit Chaperon rouge voit sa grand-mère"
python "$TTS" "lrrh2_dit"                    "$INSTR" "dit"
python "$TTS" "lrrh2_quels_grands_yeux"      "$INSTR" "quels grands yeux tu as"
python "$TTS" "lrrh2_repond"                 "$INSTR" "répond"
python "$TTS" "lrrh2_cest_pour_mieux_te_voir" "$INSTR" "C’est pour mieux te voir"
python "$TTS" "lrrh2_dit2"                   "$INSTR" "dit"
python "$TTS" "lrrh2_quelles_grandes_dents"  "$INSTR" "quelles grandes dents tu as"
python "$TTS" "lrrh2_le_loup_a_saute_du_lit" "$INSTR" "le loup a sauté du lit"
python "$TTS" "lrrh2_elle_a_pris_le_couteau" "$INSTR" "a pris le couteau du panier"
python "$TTS" "lrrh2_a_tue_le_loup"          "$INSTR" "a tué le loup"
python "$TTS" "lrrh2_fin"                    "$INSTR" "Fin"

echo "✅ All page-2 MP3s generated."

