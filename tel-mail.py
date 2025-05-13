#!/usr/bin/env python3
import re
import pandas as pd

# --- Configuration des fichiers d'entrée/sortie ---
INPUT_CSV  = "input/soliguide_v2.csv"
OUTPUT_CSV = "output/mots suspects/tel-mail.csv"

# Expressions régulières pour chaque type de problème
regex_patterns = {

    "téléphone": [
        r"\b0[1-9](?:[\s.\-]?\d{2}){4}\b",
        r"\+33\s?[1-9](?:[\s.\-]?\d{2}){4}\b",
    ],
    "email": [
        r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
    ],
}

# Fonction de détection
def detect_problems(text: str) -> str | None:
    text = str(text)
    found = []
    for label, patterns in regex_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                found.append(label)
                break
    return ", ".join(found) if found else None

def main():
    # Charger les données
    df = pd.read_csv(INPUT_CSV, delimiter=";", encoding="latin1")
    df = df.drop_duplicates(subset=["place_id", "service_id"]).reset_index(drop=True)

    # Appliquer la détection
    df["place_description_problem"]   = df["description"].apply(detect_problems)
    df["service_description_problem"] = df["service_description"].apply(detect_problems)

    # Filtrer les lignes avec au moins un problème
    df_filtered = df[
        df["place_description_problem"].notna() |
        df["service_description_problem"].notna()
    ]

    # Réorganiser les colonnes demandées
    columns_order = [
        "place_description_problem",
        "service_description_problem",
        "full_url",
        "service_name",
        "place_name"
    ]
    df_out = df_filtered[columns_order]
    
    df_out["full_url"] = "'" + df_out["full_url"].astype(str) + "'"
    # Sauvegarder
    df_out.to_csv(
        OUTPUT_CSV,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )
    print(f"✅ Fichier '{OUTPUT_CSV}' généré avec succès.")

if __name__ == '__main__':
    main()
