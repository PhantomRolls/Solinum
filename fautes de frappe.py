from openai import OpenAI
import pandas as pd
import time
from bs4 import BeautifulSoup

df = pd.read_csv("soliguide.csv", delimiter=';')
df_unique = df.drop_duplicates(subset='place_id')


results = []

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)



for index, row in df_unique.head(5).iterrows():

    p_d = row['place_description']
    place_name = row['place_name'] if 'place_name' in row else f"Place_{index}"
    

    text_to_correct= BeautifulSoup(str(p_d), "html.parser").get_text()
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            temperature=0,
            extra_headers={
                "HTTP-Referer": "https://ton-site.com",  # Facultatif
                "X-Title": "Correcteur orthographe",   # Facultatif
            },
            messages=[
                {
                    "role": "system",
                    "content": """
                    Tu es un détecteur de faute orthographiques professionnel. Indique de manière ultra concise les erreurs de frappe et d'orthographe. Ne relève pas les problèmes de ponctuation et les acronymes.
                    
                    S'il n'y a pas d'erreurs, retourne simplement 'Pas d'erreurs'. Répond sans retour à la ligne. Ne rajoute aucun commentaire. """
                },
                {
                    "role": "user",
                    "content": text_to_correct
                }
            ]
        )
        new_description = completion.choices[0].message.content.strip()
    except Exception as e:
        new_description = f"Erreur : {e}"

    print(f"✔ {place_name} → {new_description}")
    print(text_to_correct)
    results.append({
        "place_name": place_name,
        "erreurs": new_description
    })
    time.sleep(1)


df_new_descriptions = pd.DataFrame(results)

df_new_descriptions.to_csv("erreurs.csv", sep=",", index=False, encoding='utf-8')
    
print("✅ Texte corrigé :")
print(completion.choices[0].message.content)
