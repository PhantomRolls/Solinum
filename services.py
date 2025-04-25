import pandas as pd
from openai import OpenAI
import time
from bs4 import BeautifulSoup

# Charger le CSV et dédupliquer
df = pd.read_csv("soliguide.csv", delimiter=";")
df_unique = df.drop_duplicates(subset="place_id")

results = []

# Initialiser le client OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=""
)

# Prompt système pour la classification
system_prompt = """Tu es un assistant intelligent chargé d’orienter des textes vers un service Solinum.
Pour chaque texte reçu, tu choisis **UN SEUL** service parmi la liste ci-dessous, en te basant UNIQUEMENT sur leur nom.
Si aucun service ne correspond, réponds exactement « Aucun service adapté ».

Liste des services :
Accompagnement à l’emploi, Accompagnement social, Accueil de jour, Activités diverses,
Activités sportives, acupuncture, Addiction, Aide à la mobilité, allergologie, Animaux,
Atelier de cuisine, Atelier numérique, Bagagerie, Bibliothèque, Bien-être,
Bon/chèque alimentaire, Boutique Solidaire, cardiologie, Co-voiturage,
Coffre-fort numérique, Colis bébé, Conseil administratif, Conseil aux parents,
Conseil budget, Conseil Handicap, Conseil logement, Cours de français,
Cuisine partagée, Dentaire, Dépistage, dermatologie, Distribution de repas,
Domiciliation, Douche, echographie, Ecrivain public, endocrinologie,
Epicerie sociale et solidaire, Espace de repos, Espace familles, Fontaine à eau,
Frigo solidaire, Garde d’enfants, gastro-enterologie, gynecologie, Halte de nuit,
Hébergement citoyen, Hébergement d’urgence, Hébergement long-terme,
Infirmerie, Insertion par l’Activité Economique, Jardin solidaire, kinesitherapie,
Laverie, mammographie, Masques, Médecin généraliste,
Mise à disposition de véhicule, Musée, nutrition, ophtalmologie,
Ordinateur, orthophonie, osteo, oto-rhino-laryngologie, Panier alimentaire,
pedicure, Permanence juridique, phlebologie, pneumologie,
Point d'information et d’orientation, Prise, Produits d'hygiène,
Psychologie, radiologie, rhumatologie, Soins enfants, Soutien scolaire,
stomatologie, Suivi Grossesse, Téléphone, Toilettes,
Transport avec chauffeur, urologie, Vaccination, Vêtements, Vétérinaire, Wifi
"""

for index, row in df.head(1).iterrows():
    place_name = row.get("place_name", f"Place_{index}")
    # Extraire le texte brut de la description HTML
    raw_html = row.get("service_description", "")
    text = BeautifulSoup(str(raw_html), "html.parser").get_text().strip()
    if not text:
        # Pas de description : on passe
        results.append({
            "place_name": place_name,
            "service_attribue": "Aucun service adapté"
        })
        continue

    # Construire la requête
    messages = [
        {"role": "system",  "content": system_prompt},
        {"role": "user",    "content": text}
    ]

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            temperature=0,
            extra_headers={
                "HTTP-Referer": "https://ton-site.com",
                "X-Title": "Classification de service"
            },
            messages=messages
        )
        service = completion.choices[0].message.content.strip()
    except Exception as e:
        service = f"Erreur API : {e}"

    print(f"✔ {place_name} → {service}")
    results.append({
        "place_name": place_name,
        "service_attribue": service
    })

    time.sleep(1)  # éviter le throttling

# Enregistrer les résultats
df_out = pd.DataFrame(results)
df_out.to_csv("classification_services.csv", index=False, encoding="utf-8")
print("\n✅ Fichier 'classification_services.csv' généré avec succès.")
