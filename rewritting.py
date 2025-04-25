import pandas as pd
from openai import OpenAI
import time
from bs4 import BeautifulSoup


df = pd.read_csv("soliguide.csv", delimiter=';')
df_unique = df.drop_duplicates(subset='place_id')


results = []


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=""
)


system_prompt = """Tu es un expert en simplification de l'information.
Ta mission est de réécrire un texte en langage clair et accessible à tous, y compris aux personnes ayant des difficultés de lecture, de compréhension ou ne maîtrisant pas bien le français administratif. Ce  que tu écris doit être entre en html et sans retour à la ligne.
Voici les consignes à suivre :
- Utilise des phrases courtes
- Garde le sens du texte original, mais rends-le plus facile à lire
- Ne rajoute aucun commentaires"""


for index, row in df_unique.head(1).iterrows():

    p_d = row['place_description']
    place_name = row['place_name'] if 'place_name' in row else f"Place_{index}"
    

    text_to_simplify = BeautifulSoup(str(p_d), "html.parser").get_text()
    
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            temperature = 0,
            extra_headers={
                "HTTP-Referer": "https://ton-site.com",  # Facultatif
                "X-Title": "Correcteur orthographe",      # Facultatif
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_to_simplify}
            ]
        )
        new_description = completion.choices[0].message.content.strip()
    except Exception as e:
        new_description = f"Erreur : {e}"
    
    print(f"✔ {place_name} → {new_description}")
    
    results.append({
        "place_name": place_name,
        "new_description": new_description
    })
    time.sleep(1)


df_new_descriptions = pd.DataFrame(results)


df_new_descriptions.to_csv("rewritting.csv", sep=",", index=False, encoding='utf-8')
df_new_descriptions["new_description"] = '"' + df_new_descriptions["new_description"] + '"'

print("\n✅ DataFrame généré :")
print(df_new_descriptions.head())
