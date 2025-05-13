import pandas as pd
import re
from bs4 import BeautifulSoup
import spacy

# Charger le modèle spaCy français
nlp = spacy.load("fr_core_news_sm")

# Jours de la semaine
jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# Extraire horaires du texte au format HH:MM
def normaliser_horaire(texte):
    texte = texte.lower()
    horaires = []

    for h, m in re.findall(r"\b(\d{1,2})h(\d{2})\b", texte):
        horaires.append(f"{h.zfill(2)}:{m}")

    for h in re.findall(r"\b(\d{1,2})h\b", texte):
        hhmm = f"{h.zfill(2)}:00"
        if hhmm not in horaires:
            horaires.append(hhmm)

    for h in re.findall(r"\b\d{1,2}:\d{2}\b", texte):
        if h not in horaires:
            horaires.append(h)
    return horaires


# Associer jours et horaires via spaCy
def assign_jours_horaires_spacy(texte):
    texte = str(texte).lower()
    doc = nlp(texte)
    mapping = {}

    for token in doc:
        if token.text in jours:
            jour = token.text
            horaires = []
            for tok in token.subtree:
                if tok.text != jour:
                    horaires.extend(normaliser_horaire(tok.text))
            if horaires:
                mapping[jour] = horaires
    return mapping


# Parser les horaires de schedules
def parse_schedule_html(html):
    horaires_by_jour = {}
    if pd.isna(html) or not html.strip():
        return horaires_by_jour

    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div")

    for div in divs:
        text = div.get_text().lower()
        for jour in jours:
            if jour in text:
                matches = re.findall(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", text)
                horaires = []
                for match in matches:
                    start, end = match.split("-")
                    horaires.extend([start.strip(), end.strip()])
                if jour in horaires_by_jour:
                    horaires_by_jour[jour].extend(horaires)
                else:
                    horaires_by_jour[jour] = horaires
    return horaires_by_jour


# Détection d’incohérences
def detect_incoherence(mapping_desc, mapping_sched):
    incoherences = []
    for jour, horaires in mapping_desc.items():
        horaires_base = mapping_sched.get(jour, [])
        for h in horaires:
            if all(h != s for s in horaires_base):
                incoherences.append((jour, h))
    return incoherences


# Chargement du CSV
df = pd.read_csv("input/soliguide_v2.csv", delimiter=";", encoding="latin1")

# Traitement ligne par ligne
results = []

for _, row in df.iterrows():
    desc = str(row["service_description"])
    schedule_html = row["schedules"]
    mapping_desc = assign_jours_horaires_spacy(desc)
    mapping_sched = parse_schedule_html(schedule_html)
    incoh = detect_incoherence(mapping_desc, mapping_sched)
    if incoh:
        results.append(
            {
                "incoherence_jour_horaire": "; ".join([f"{j}: {h}" for j, h in incoh]),
                "full_url": row["full_url"],
                "service_name": row["service_name"],
                "place_name": row["place_name"],
            }
        )

# Sauvegarde du fichier
df_out = pd.DataFrame(results)
df_out["full_url"] = "'" + df_out["full_url"].astype(str) + "'"
df_out.to_csv('output/mots suspects/horaires.csv', sep=";", index=False, encoding="utf-8")

print("✅ Fichier 'output/mots suspects/horaires.csv' généré avec succès.")
