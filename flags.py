#!/usr/bin/env python3
import pandas as pd
from bs4 import BeautifulSoup
import re
import os

# Se placer dans le répertoire du script pour chemins relatifs
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Liste des mots ou expressions à signaler
FLAGS = [
    "rendez-vous"
]

# Fichiers d'entrée et de sortie (modifiable)
INPUT_CSV = 'soliguide.csv'
OUTPUT_CSV = 'flags.csv'

# Charger le CSV et enlever les doublons
df = pd.read_csv(INPUT_CSV, delimiter=';')
df_unique = df.drop_duplicates(subset='place_id')

results = []
# Pour chaque entrée, rechercher les mots à flag
def flag_descriptions():
    for idx, row in df_unique.iterrows():
        place_id = row.get('place_id', idx)
        place_name = row.get('place_name', f"Place_{idx}")
        raw_html = row.get('place_description', '')
        text = BeautifulSoup(str(raw_html), 'html.parser').get_text()

        flagged = []
        for mot in FLAGS:
            pattern = rf"\b{re.escape(mot)}\b"
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
                'excerpt': excerpt
            })

if __name__ == '__main__':
    flag_descriptions()
    # Enregistrer les résultats
    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"✅ {len(df_out)} descriptions flagged. Fichier généré : '{OUTPUT_CSV}'")
