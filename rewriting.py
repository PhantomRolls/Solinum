#!/usr/bin/env python3
import time
import pandas as pd
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import sys
from cerebras.cloud.sdk import Cerebras

# --- Configuration des fichiers d'entrée/sortie ---
INPUT_CSV  = "input/soliguide_v2.csv"
OUTPUT_CSV = "output/rewriting.csv"

# --- Initialisation du client OpenRouter ---
client = Cerebras(
    api_key="",
)

# --- Prompt système pour la simplification ---
system_prompt = (
    """
    Tu es un expert en simplification de l'information.
    Ta mission est de réécrire un texte en langage clair et accessible à tous, "
    "y compris aux personnes ayant des difficultés de lecture, de compréhension "
    "ou ne maîtrisant pas bien le français administratif. Ce que tu écris doit être "
    "entre en html et sans retour à la ligne.
    Voici les consignes à suivre :
    - Utilise des phrases courtes
    - Garde le sens du texte original, mais rends-le plus facile à lire
    - Ne rajoute aucun commentaire
    """
).replace("\n", " ")

def main():
    start_time = time.time()

    try:
        rows = int(sys.argv[1])
        if rows < 1:
            rows = None
    except (IndexError, ValueError):
        rows = None

    df = pd.read_csv(INPUT_CSV, sep=';', encoding='latin1')
    df = df.drop_duplicates(subset='place_id')
    if rows is not None:
        df = df.head(rows)

    results = []

    for index, row in df.iterrows():
        place_name = row.get("place_name", f"Place_{index}")
        raw_html   = row.get("description", "")
        text = BeautifulSoup(str(raw_html), "html.parser").get_text().strip()

        if not text:
            simplified = ""
            print(f"⚠ {place_name} → Pas de description, ignoré.")
        else:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b",
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": text}
                    ]
                )
                simplified = response.choices[0].message.content.strip()
                print(f"✔ {place_name} → {simplified}")
            except Exception as e:
                simplified = f"Erreur : {e}"
                print(f"✖ {place_name} → {simplified}")

        results.append({
            "place_name": place_name,
            "new_description": simplified
        })

        time.sleep(2)  # pour éviter le throttling

    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT_CSV, sep=",", index=False, encoding='utf-8-sig')

    elapsed = time.time() - start_time
    print(f"Terminé en {elapsed:.2f}s, fichier généré: '{OUTPUT_CSV}'")

if __name__ == '__main__':
    main()
