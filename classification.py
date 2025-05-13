#!/usr/bin/env python3
import sys
import time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from cerebras.cloud.sdk import Cerebras

# --- Configuration des fichiers ---
INPUT_CSV  = "input/soliguide_v2.csv"
OUTPUT_CSV = "output/classification.csv"
BATCH_SIZE = 10

# --- Récupération du nombre de lignes à traiter ---
try:
    n_rows = int(sys.argv[1])
    if n_rows < 1:
        n_rows = None
except (IndexError, ValueError):
    n_rows = None

# --- Chargement et dé-duplication du CSV ---
df = pd.read_csv(INPUT_CSV, delimiter=";", encoding='latin1')
# On suppose que la colonne 'service_name' contient le libellé d'origine
# Déduplique sur les colonnes place_id et service_id
df_unique = df.drop_duplicates(subset=["place_id", "service_id"]).reset_index(drop=True)
if n_rows is not None:
    df_unique = df_unique.head(n_rows)

# --- Initialisation du client OpenRouter ---
client = Cerebras(
    api_key="",
)

# --- Prompt système pour la classification batchée ---
system_prompt = (
    """Tu es un assistant intelligent chargé d’orienter des textes vers un service Solinum.
    Tu vas recevoir un lot de descriptions numérotées.
    Voici la liste des services disponibles : Accompagnement à l’emploi, Accompagnement social, Accueil de jour, Activités diverses, Activités sportives, acupuncture, Addiction, Aide à la mobilité, allergologie, Animaux, Atelier de cuisine, Atelier numérique, Bagagerie, Bibliothèque, Bien-être, Bon/chèque alimentaire, Boutique Solidaire, cardiologie, Co-voiturage, Coffre-fort numérique, Colis bébé, Conseil administratif, Conseil aux parents, Conseil budget, Conseil Handicap, Conseil logement, Cours de français, Cuisine partagée, Dentaire, Dépistage, dermatologie, Distribution de repas, Domiciliation, Douche, échographie, Écrivain public, endocrinologie, Épicerie sociale et solidaire, Espace de repos, Espace familles, Fontaine à eau, Frigo solidaire, Garde d’enfants, gastro-entérologie, gynécologie, Halte de nuit, Hébergement citoyen, Hébergement d’urgence, Hébergement long-terme, Infirmerie, Insertion par l’Activité Économique, Jardin solidaire, kinésithérapie, Laverie, mammographie, Masques, Médecin généraliste, Mise à disposition de véhicule, Musée, nutrition, ophtalmologie, Ordinateur, orthophonie, ostéo, oto-rhino-laryngologie, Panier alimentaire, pédicure, Permanence juridique, phlébologie, pneumologie, Point d'information et d’orientation, Prise, Produits d'hygiène, Psychologie, radiologie, rhumatologie, Soins enfants, Soutien scolaire, stomatologie, Suivi Grossesse, Téléphone, Toilettes, Transport avec chauffeur, urologie, Vaccination, Vêtements, Vétérinaire, Wifi.
    Tu es un assistant intelligent chargé d’orienter des textes vers un service Solinum.
    Tu vas recevoir un lot de descriptions numérotées.
    Ne répète pas la liste des services dans ta réponse.
    Pour chaque description, choisis **un seul** service dans la liste suivante et renvoie **uniquement** un objet JSON strict, sans aucun texte supplémentaire :

    {
    "services": ["service1", "service2", ..., "serviceN"]
    }

    où chaque élément de la liste correspond exactement au service attribué à la description du même numéro.  
    Si pour une description aucun service n’est pertinent, mets "Aucun service adapté" à cette position.
"""
)

# --- Préparation des résultats ---
results_dict = {}
# Lignes sans description → NaN
for idx, row in df_unique[df_unique['service_description'].isna()].iterrows():
    results_dict[idx] = {
        'place_name':       row.get('place_name', f'Place_{idx}'),
        'full_url':         row.get('full_url', ''),
        'service_name':     row.get('service_name', ''),
        'service_attribue': np.nan
    }

start_time = time.time()
# --- Traitement des descriptions valides en batch ---
valid_df = df_unique[df_unique['service_description'].notna()]
for start in range(0, len(valid_df), BATCH_SIZE):
    batch = valid_df.iloc[start:start + BATCH_SIZE]

    # Construire le texte numéroté
    items = []
    for i, (idx, row) in enumerate(batch.iterrows(), start=1):
        text = BeautifulSoup(str(row['service_description']), 'html.parser').get_text().strip()
        items.append(f"{i}. {text}")
    numbered_text = "\n\n".join(items)

    # Appel API
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user',   'content': numbered_text}
    ]
    try:
        comp = client.chat.completions.create(
            model='llama-3.3-70b',
            temperature=0,
            messages=messages
        )
        raw_out = comp.choices[0].message.content.strip()
        snippet = raw_out[raw_out.find('{'): raw_out.rfind('}')+1] if '{' in raw_out and '}' in raw_out else raw_out
        resp = json.loads(snippet)
        assigned = resp.get('services', [])
    except Exception as e:
        assigned = [f'ERREUR API : {e}'] * len(batch)

    # Stocker les résultats du batch
    for service, (idx, row) in zip(assigned, batch.iterrows()):
        results_dict[idx] = {
            'place_name':       row.get('place_name', f'Place_{idx}'),
            'full_url':         row.get('full_url', ''),
            'service_name':     row.get('service_name', ''),
            'service_attribue': service or 'Aucun service adapté'
        }

    time.sleep(2)

# --- Export ---
final_results = [results_dict[i] for i in sorted(results_dict.keys())]
df_out = pd.DataFrame(final_results)
df_out["full_url"] = "'" + df_out["full_url"].astype(str) + "'"

df_out.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

df = pd.read_csv("output/classification.csv")
df_diff = df[df['service_name'] != df['service_attribue']]
df_diff.to_csv("output/classification_tri.csv", index=False)


elapsed = time.time() - start_time
print(f"Terminé en {elapsed:.2f}s,\n✅ Fichier '{OUTPUT_CSV}' généré pour {len(final_results)} entrées.")
print("✅ Nouveau fichier 'services_differents.csv' créé avec succès.")
