#!/usr/bin/env python3
import pandas as pd
from bs4 import BeautifulSoup
import re
import os
import sys

# --- Configuration ---
INPUT_CSV = "input/soliguide_v2.csv"
OUTPUT_CSV = "output/mots suspects/flags.csv"
FLAGS = [
    "phone"
]  # Mots ou fragments à détecter
DETECT_SUBSTRING = True  # True = détection partielle (Ctrl+F), False = mot exact

# --- Initialisation du contexte d'exécution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# --- Chargement des données ---
df = pd.read_csv(INPUT_CSV, delimiter=';', encoding='latin1')
df_unique = df.drop_duplicates(subset='place_id')

results = []

def flag_descriptions():
    for idx, row in df_unique.iterrows():
        place_id = row.get('place_id', idx)
        place_name = row.get('place_name', f"Place_{idx}")
        raw_html = row.get('description', '')
        text = BeautifulSoup(str(raw_html), 'html.parser').get_text()

        flagged = []
        for mot in FLAGS:
            if DETECT_SUBSTRING:
                pattern = re.escape(mot)  # Détection partielle
            else:
                pattern = rf"\b{re.escape(mot)}\b"  # Détection exacte

            if re.search(pattern, text, flags=re.IGNORECASE):
                flagged.append(mot)

        if flagged:
            excerpt = text[:100].replace('\n', ' ')
            if len(text) > 100:
                excerpt += '...'
            results.append({
                'place_id': place_id,
                'place_name': place_name,
                'flagged_words': ';'.join(flagged),
                'full_url' : row["full_url"],
            })

# --- Exécution principale ---
if __name__ == '__main__':
    flag_descriptions()
    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"✅ {len(df_out)} descriptions flagged. Fichier généré : '{OUTPUT_CSV}'")
