import pandas as pd
import time
from bs4 import BeautifulSoup
import language_tool_python

# Liste des règles à ignorer
rules_to_ignore = [
    # Ponctuation & typographie
    "PUNCTUATION", "COMMA_PARENTHESIS_WHITESPACE", "COMMA_WHICH", "EN_QUOTES",
    "UNPAIRED_BRACKETS", "OXFORD_COMMA", "UPPERCASE_SENTENCE_START",
    "WHITESPACE_RULE", "DOUBLE_PUNCTUATION", "MULTIPLE_WHITESPACE",
    "SPACE_AFTER_PERIOD", "FR.SPACE_AFTER_PERIOD", "SPACE_BEFORE_PERIOD",
    "COMMA_COMPOUND_SENTENCE", "FRENCH_WHITESPACE", "FRENCH_QUOTES",
    "FRENCH_WORD_CONTAINS_UNDERSCORE", "MORFOLOGIK_RULE_FR"

]

# Charger le fichier CSV
df = pd.read_csv("soliguide.csv", delimiter=';')
df_unique = df.drop_duplicates(subset='place_id')

# Initialiser LanguageTool pour le français
tool = language_tool_python.LanguageTool('fr')

results = []

# Parcourir les premières lignes (modifiable)
for index, row in df_unique.head(10).iterrows():
    p_d = row['place_description']
    place_name = row['place_name'] if 'place_name' in row else f"Place_{index}"
    text_to_correct = BeautifulSoup(str(p_d), "html.parser").get_text()

    try:
        erreurs = tool.check(text_to_correct)

        # Filtrage par règle et type
        erreurs_filtrees = [
            e for e in erreurs 
            if e.ruleId not in rules_to_ignore and e.ruleIssueType != 'typographical'
        ]

        if not erreurs_filtrees:
            new_description = "Pas d'erreurs"
        else:
            fautes = [
                f"{e.context.strip()} → {e.message}" 
                for e in erreurs_filtrees
            ]
            new_description = " | ".join(fautes)

    except Exception as e:
        new_description = f"Erreur : {e}"

    print(f"✔ {place_name} → {new_description}")
    results.append({
        "place_name": place_name,
        "erreurs": new_description
    })

    time.sleep(0.3)  # Léger délai pour éviter surcharge

# Exporter le résultat dans un CSV
df_new_descriptions = pd.DataFrame(results)
df_new_descriptions.to_csv("correction_2.csv", sep=",", index=False, encoding='utf-8')

print("✅ Fichier correction_2.csv généré avec succès.")
