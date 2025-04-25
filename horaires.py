import pandas as pd
import re

# Charger le fichier CSV
df = pd.read_csv("soliguide.csv", delimiter=";")

# Expressions régulières pour chaque type de problème
regex_patterns = {
    "horaire": [
        r"\b\d{1,2}[:hH]\d{2}\b",
        r"\b\d{1,2}h\b",
        r"\b\d{1,2} ?h ?à ?\d{1,2} ?h\b",
        r"\bde ?\d{1,2} ?h ?à ?\d{1,2} ?h\b",
        r"\b\d{1,2} ?h ?- ?\d{1,2} ?h\b",
        r"\b\d{1,2} ?:\d{2} ?- ?\d{1,2} ?:\d{2}\b",
    ],
    "téléphone": [
        r"\b0[1-9](?:[\s.-]?\d{2}){4}\b",
        r"\+33\s?[1-9](?:[\s.-]?\d{2}){4}\b",
    ],
    "email": [r"\b[\w\.-]+@[\w\.-]+\.\w+\b"],
}


# Fonction de détection
def detect_problems(texte):
    texte = str(texte)
    found = []
    for label, patterns in regex_patterns.items():
        for pattern in patterns:
            if re.search(pattern, texte):
                found.append(label)
                break
    return ", ".join(found) if found else None


# Appliquer la détection sur les deux descriptions
df["place_description_problem"] = df["place_description"].apply(detect_problems)
df["service_description_problem"] = df["service_description"].apply(detect_problems)

# Filtrer les lignes avec au moins un problème
df_filtered = df[
    (df["place_description_problem"].notna())
    | (df["service_description_problem"].notna())
]

# Réorganiser les colonnes
columns_order = [
    "place_description_problem",
    "service_description_problem",
    "place_id",
    "service_id",
    "service_name",
    "place_name",
    "place_description",
    "service_description",
]
df_result = df_filtered[columns_order]

# Sauvegarder le fichier
df_result.to_csv(
    "problemes_places_et_services.csv", sep=";", index=False, encoding="utf-8"
)

print("✅ Fichier 'problemes_places_et_services.csv' généré avec succès.")
