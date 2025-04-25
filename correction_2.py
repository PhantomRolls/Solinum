import re
import pandas as pd
from bs4 import BeautifulSoup
import language_tool_python

# --- CONFIGURATION ---
INPUT_CSV  = "soliguide.csv"
OUTPUT_CSV = "correction_2.csv"

# Regex pour répétitions de mots et de lettres
RE_REPEAT_WORDS   = re.compile(r'\b(\w+)(?:\s+\1\b)+', flags=re.IGNORECASE)
RE_REPEAT_LETTERS = re.compile(r'(.)\1{2,}')

# Initialise LanguageTool pour le français
tool = language_tool_python.LanguageTool('fr')

# Pattern pour reconnaître un acronyme (2+ majuscules ou chiffres ou tirets)
RE_ACRONYME = re.compile(r'^[A-Z0-9ÀÂÉÈÊÔÙÛÄËÏÖÜÇ\-]{2,}$')

def analyse_texte(html_text: str) -> str:
    # 1) Extraction du texte brut
    text = BeautifulSoup(str(html_text), "html.parser").get_text(separator=" ")

    # 2) Vérification par LanguageTool
    matches = tool.check(text)
    ortho_msgs = []
    for m in matches:
        if m.ruleIssueType != 'misspelling':
            continue

        # Extrait le fragment exact signalé comme faute
        erreur = text[m.offset : m.offset + m.errorLength]

        # Ignore si c'est un acronyme
        if RE_ACRONYME.fullmatch(erreur):
            continue

        # Sinon, propose jusqu'à 5 suggestions
        sugg = m.replacements[:5] or ["(aucune suggestion)"]
        # On affiche le mot fautif plutôt que tout le contexte
        ortho_msgs.append(f"{erreur} → {', '.join(sugg)}")

    # 3) Répétitions de mots
    repet_mots = [g.group(0) for g in RE_REPEAT_WORDS.finditer(text)]
    repet_mots_msgs = [f"Répétitions mot : «{r}»" for r in repet_mots]

    # 4) Répétitions de lettres (défrappe)
    repet_lettres = [g.group(0) for g in RE_REPEAT_LETTERS.finditer(text)]
    repet_lettres_msgs = [f"Répétitions lettres : «{r}»" for r in repet_lettres]

    toutes = ortho_msgs + repet_mots_msgs + repet_lettres_msgs
    return " | ".join(toutes) if toutes else "Pas d'erreurs"

def main():
    df = pd.read_csv(INPUT_CSV, sep=';')
    df = df.drop_duplicates(subset='place_id', keep='first').reset_index(drop=True)
    df = df.head(5)
    sorties = []
    for _, row in df.iterrows():
        pid  = row.get("place_id", "")
        name = row.get("place_name", f"Place_{pid}")
        desc = row.get("place_description", "")

        erreurs = analyse_texte(desc)
        sorties.append({
            "place_id":   pid,
            "place_name": name,
            "erreurs":    erreurs
        })

    pd.DataFrame(sorties).to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    print(f"✅ {OUTPUT_CSV} généré avec succès.")

if __name__ == "__main__":
    main()
