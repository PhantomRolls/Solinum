#!/usr/bin/env python3
import sys
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
import language_tool_python
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# --- Configuration des fichiers d'entrée/sortie ---
INPUT_CSV  = "input/soliguide_v2.csv"
OUTPUT_CSV = "output/correction_2.csv"

# Regex pour répétitions de mots et de lettres
RE_REPEAT_WORDS   = re.compile(r'\b(\w+)(?:\s+\1\b)+', flags=re.IGNORECASE)
RE_REPEAT_LETTERS = re.compile(r'([A-Za-zÀ-ÿ])\1{2,}')
# Pattern pour reconnaître un acronyme (2+ majuscules, chiffres ou tirets)
RE_ACRONYME = re.compile(r'^[A-Z0-9ÀÂÉÈÊÔÙÛÄËÏÖÜÇ\-]{2,}$')

# --- Initialisation de LanguageTool ---
tool = language_tool_python.LanguageTool('fr')
# pré-chauffe pour lancer la JVM
_ = tool.check("")

# ThreadPool pour exécuter check() avec timeout
executor = ThreadPoolExecutor(max_workers=1)
MAX_CHECK_TIMEOUT = 5  # secondes


def safe_check(text):
    """
    Exécute tool.check(text) avec un timeout, renvoie None en cas de timeout ou d'erreur.
    """
    future = executor.submit(tool.check, text)
    try:
        return future.result(timeout=MAX_CHECK_TIMEOUT)
    except TimeoutError:
        future.cancel()
        return None
    except Exception:
        return None


def analyse_texte(html_text: str, ignore_tokens: set) -> str:
    """
    Analyse un texte HTML et renvoie les erreurs détectées, en ignorant les tokens fournis :
    - fautes d'orthographe
    - erreurs d'accord
    - répétitions de mots
    - répétitions de lettres
    Retourne un message d'erreur si check() échoue ou timeout.
    """
    text = BeautifulSoup(str(html_text), "html.parser").get_text(separator=" ")

    # 1) Vérification par LanguageTool
    matches = safe_check(text)
    if matches is None:
        return f"Erreur LanguageTool (timeout {MAX_CHECK_TIMEOUT}s)"

    ortho_msgs = []
    accord_msgs = []
    for m in matches:
        mot = text[m.offset:m.offset + m.errorLength]
        mot_clean = mot.strip().strip(".,;:?!")
        if not mot_clean:
            continue
        lower = mot_clean.lower()
        # Ignorer si fait partie de place_name
        if lower in ignore_tokens:
            continue
        if m.ruleIssueType == 'misspelling':
            if RE_ACRONYME.fullmatch(mot_clean):
                continue
            sugg = m.replacements[:5] or ["(aucune suggestion)"]
            ortho_msgs.append(f"{mot_clean} → {', '.join(sugg)}")
        elif m.ruleIssueType == 'grammar':
            sugg = m.replacements[:5] or ["(aucune suggestion)"]
            accord_msgs.append(f"Accord: {mot_clean} → {', '.join(sugg)}")

    # 2) Répétitions de mots (ignorer si token dans ignore_tokens)
    repet_mots = [g.group(0) for g in RE_REPEAT_WORDS.finditer(text)
                  if g.group(1).lower() not in ignore_tokens]
    repet_mots_msgs = [f"Répétitions mot : «{r}»" for r in repet_mots]

    # 3) Répétitions de lettres (défrappe)
    repet_lettres = [g.group(0) for g in RE_REPEAT_LETTERS.finditer(text)]
    repet_lettres_msgs = [f"Répétitions lettres : «{r}»" for r in repet_lettres]

    toutes = ortho_msgs + accord_msgs + repet_mots_msgs + repet_lettres_msgs
    return " | ".join(toutes) if toutes else "Pas d'erreurs"


def main():
    start_time = time.time()
    # Lecture optionnelle du nombre de lignes depuis l'UI
    try:
        n_rows = int(sys.argv[1])
        if n_rows < 1:
            n_rows = None
    except (IndexError, ValueError):
        n_rows = None

    # Chargement du CSV et déduplication
    df = pd.read_csv(INPUT_CSV, sep=';')
    df = df.drop_duplicates(subset='place_id', keep='first').reset_index(drop=True)
    if n_rows is not None:
        df = df.head(n_rows)

    results = []
    for idx, row in df.iterrows():
        pid  = row.get('place_id', '')
        name = row.get('place_name', '')
        desc = row.get('place_description', '')

        # Construire l'ensemble des tokens à ignorer depuis place_name
        # On décompose name en mots alphanumériques, en minuscules
        ignore_tokens = set(re.findall(r"\w+", name.lower()))

        if pd.isna(desc) or not str(desc).strip():
            erreurs = "Pas de description"
        else:
            erreurs = analyse_texte(desc, ignore_tokens)

        # N'affiche et n'ajoute que si des erreurs réelles
        if erreurs not in ("Pas d'erreurs", "Pas de description"):
            results.append({'place_id': pid, 'place_name': name, 'erreurs': erreurs})
            print(f"✔ [{idx}] {name} → {erreurs}")

    # Export CSV
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    elapsed = time.time() - start_time
    print(f"✅ '{OUTPUT_CSV}' généré en {elapsed:.2f} secondes.")

if __name__ == '__main__':
    main()
