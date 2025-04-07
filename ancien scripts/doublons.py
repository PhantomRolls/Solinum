import pandas as pd
from openai import OpenAI
import time

# 1. Charger les données
df = pd.read_csv("soliguide.csv", delimiter=';')
df_unique = df.drop_duplicates(subset='service_name')
services = df_unique['service_name'].dropna().tolist()


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=""
)

# 3. Définir le prompt système
system_prompt = """Tu es un assistant spécialisé en simplification de l'information.
Pour chaque nom de service que je te donne, écris une courte description en langage clair (accessible à tous, y compris aux personnes ayant des difficultés de lecture ou de compréhension).
La description doit :
- être simple et directe
- expliquer ce que fait le service
- éviter les termes techniques ou administratifs
- faire 1 ou 2 phrases maximum."""

# 4. Créer une liste pour stocker les résultats
results = []

# 5. Générer les descriptions
for service_name in services[:5]:
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            extra_headers={
                "HTTP-Referer": "https://ton-site.com",
                "X-Title": "Correcteur orthographe",
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": service_name}
            ]
        )
        description = completion.choices[0].message.content.strip()
    except Exception as e:
        description = f"Erreur : {e}"

    print(f"✔ {service_name} → {description}")
    results.append({
        "service_name": service_name,
        "description": description
    })
    time.sleep(1)  # petit délai de sécurité pour ne pas surcharger l’API

# 6. Créer le DataFrame final
df_descriptions = pd.DataFrame(results)

# 7. (Facultatif) Exporter le DataFrame
df_descriptions.to_csv("services_descriptions.csv", index=False, encoding='utf-8')


print("\n✅ DataFrame généré :")
print(df_descriptions.head())
