from openai import OpenAI
import pandas as pd
import time
from bs4 import BeautifulSoup
import json
import spacy
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
else:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Charger le modèle spaCy français
nlp = spacy.load("fr_core_news_sm")

# Charger le fichier CSV
df = pd.read_csv("soliguide.csv", delimiter=";")
df_unique = df.drop_duplicates(subset="place_id")



# Initialiser le client OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=""
)

# Prompt système pour obtenir une réponse JSON structurée
system_prompt = ("""
    Tu es un correcteur orthographique professionnel. Pour chaque phrase, détecte uniquement les fautes d’orthographe, les erreurs d’accord, les erreurs de conjugaison et les répétitions de mots. Ne signale aucune autre faute. Réponds uniquement au format JSON, sous la forme :
{"erreurs": [
  {"type": "orthographe", "texte": "[...]", "suggestion": "[...]"},
  {"type": "accord", "texte": "[...]", "suggestion": "[...]"},
  {"type": "conjugaison", "texte": "[...]", "suggestion": "[...]"},
  {"type": "répétition", "texte": "[...]", "suggestion": "[...]"}
]}
Si aucune erreur n'est détectée, réponds : {"erreurs": []}"""

)

results = []

# Traiter chaque ligne du CSV
for index, row in df_unique.head(1).iterrows():
    place_name = row["place_name"] if "place_name" in row else f"Place_{index}"
    description = row.get("place_description", "")
    
    # Nettoyer le texte du HTML
    text = BeautifulSoup(str(description), "html.parser").get_text()
    
    # Découper le texte en phrases avec spaCy
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    # Pour chaque phrase, appeler le LLM
    for i, sentence in enumerate(sentences, start=1):
        try:
            completion = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                temperature=0,
                extra_headers={
                    "HTTP-Referer": "https://ton-site.com",
                    "X-Title": "Correcteur orthographe"
                },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": sentence}
                ]
            )
            print(f"🔄 Phrase {i} analysée")
            
            raw_response = completion.choices[0].message.content.strip()
            try:
                json_data = json.loads(raw_response)
                erreurs = json_data.get("erreurs", [])
                
                # S'il n'y a pas d'erreur, on ajoute une ligne avec "Pas d'erreur"
                if not erreurs:
                    results.append({
                        "place_name": place_name,
                        "sentence_number": i,
                        "sentence": sentence,
                        "type": "",
                        "texte_fautif": "",
                        "suggestion": "Pas d'erreur"
                    })
                else:
                    # Pour chaque faute détectée dans la phrase, ajouter une ligne
                    for err in erreurs:
                        results.append({
                            "place_name": place_name,
                            "sentence_number": i,
                            "sentence": sentence,
                            "type": err.get("type", ""),
                            "texte_fautif": err.get("texte", ""),
                            "suggestion": err.get("suggestion", "")
                        })
            except json.JSONDecodeError:
                results.append({
                    "place_name": place_name,
                    "sentence_number": i,
                    "sentence": sentence,
                    "type": "",
                    "texte_fautif": "",
                    "suggestion": f"Réponse non JSON : {raw_response}"
                })
        except Exception as e:
            results.append({
                "place_name": place_name,
                "sentence_number": i,
                "sentence": sentence,
                "type": "Erreur API",
                "texte_fautif": "",
                "suggestion": str(e)
            })
        time.sleep(1)  # Attendre 1 seconde entre les requêtes pour éviter le throttling

# Créer la DataFrame et l'enregistrer en CSV
df_results = pd.DataFrame(results)
df_results.to_csv("correction_1.csv", sep=",", index=False, encoding="utf-8")
print("✅ Fichier 'correction_1.csv' généré avec succès.")
