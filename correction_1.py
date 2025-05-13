import sys
import time
import json
import ast
import pandas as pd
from bs4 import BeautifulSoup
from cerebras.cloud.sdk import Cerebras

# --- Configuration des fichiers ---
INPUT_CSV  = "input/soliguide_v2.csv"
OUTPUT_CSV = "output/correction_1.csv"

# --- Encodage UTF-8 sur stdout/stderr ---
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
else:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# --- Lecture et dé-duplication du CSV d'entrée ---
df = pd.read_csv(INPUT_CSV, delimiter=";", encoding='latin1')
df_unique = df.drop_duplicates(subset="place_id").reset_index(drop=True)

# --- Limitation du nombre de lignes (paramètre optionnel) ---
try:
    n_rows = int(sys.argv[1])
    if n_rows > 0:
        df_unique = df_unique.head(n_rows)
except (IndexError, ValueError):
    pass

# --- Initialisation du client Cerebras ---
client = Cerebras(api_key="")

# --- Prompt système amélioré ---
system_prompt = (
    "Tu es un correcteur orthographique professionnel. Pour chaque description complète, détecte uniquement "
    "les fragments contenant une faute (orthographe, accord, conjugaison ou répétition). "
    "Pour chaque fragment fautif, indique également l’erreur commise de manière concise.\n"
    "Réponds STRICTEMENT au format JSON suivant :\n"
    "{\n"
    "  \"erreurs\": [\n"
    "    {\"texte\": \"fragment_fautif1\", \"explication\": \"explication de l'erreur\"},\n"
    "    {\"texte\": \"fragment_fautif2\", \"explication\": \"explication de l'erreur\"}\n"
    "  ]\n"
    "}\n"
    "Si aucune erreur n'est détectée, réponds : {\"erreurs\":[]}"
)

# --- Traitement des descriptions ---
start_time = time.time()
results = []

for index, row in df_unique.iterrows():
    place_name = row.get("place_name", f"Place_{index}")
    raw_html = row.get("description", "")

    # Nettoyage HTML → texte brut
    description = BeautifulSoup(str(raw_html), "html.parser").get_text(separator=" ").strip()

    try:
        comp = client.chat.completions.create(
            model="llama-3.3-70b",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": description}
            ]
        )
        raw = comp.choices[0].message.content.strip()

        # Parsing JSON strict puis fallback
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(raw)
            except Exception:
                data = {"erreurs": None}

        erreurs = data.get("erreurs") if isinstance(data, dict) else None

        if erreurs is None:
            results.append({
                "place_name": place_name,
                "texte_fautif": f"JSON invalide: {raw}",
                "explication": ""
            })
        elif not erreurs:
            results.append({
                "place_name": place_name,
                "texte_fautif": "",
                "explication": ""
            })
        elif isinstance(erreurs, list) and isinstance(erreurs[0], dict):
            for item in erreurs:
                results.append({
                    "place_name": place_name,
                    "texte_fautif": item.get("texte", ""),
                    "explication": item.get("explication", "")
                })
        else:
            for fragment in erreurs:
                results.append({
                    "place_name": place_name,
                    "texte_fautif": fragment,
                    "explication": "(explication manquante)"
                })

    except Exception as e:
        results.append({
            "place_name": place_name,
            "texte_fautif": f"ERREUR API: {e}",
            "explication": ""
        })

    # Pause pour limiter le risque de throttling
    time.sleep(2)

# --- Export CSV final ---
print(f"Export vers '{OUTPUT_CSV}'...")
df_results = pd.DataFrame(results, columns=["place_name", "texte_fautif", "explication"])
df_results.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

elapsed = time.time() - start_time
print(f"Terminé en {elapsed:.2f}s, fichier généré : '{OUTPUT_CSV}'")
