import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Masquer les logs TensorFlow

import pandas as pd
from sentence_transformers import SentenceTransformer, util

# 🔹 Charger les données
df = pd.read_csv("services_cleaned.csv", delimiter=";")
service_names = df["Services"].dropna().tolist()  # Juste les titres

# 🔹 Charger le modèle d'embedding
print("Chargement du modèle all-mpnet-base-v2...")
model = SentenceTransformer("all-mpnet-base-v2")

# 🔹 Encoder uniquement les noms de service
print("Encodage des titres de services...")
title_embeddings = model.encode(service_names, convert_to_tensor=True)

# 🔹 Fonction pour afficher le Top K services les plus proches
def find_best_service_from_titles(new_text, top_k=3):
    query_embedding = model.encode(new_text, convert_to_tensor=True)
    similarities = util.pytorch_cos_sim(query_embedding, title_embeddings)[0]
    top_indices = similarities.topk(top_k).indices.tolist()

    return [
        {
            "Texte proposé": new_text,
            "Service": service_names[i],
            "Score": round(similarities[i].item(), 4)
        }
        for i in top_indices
    ]

# 🔁 Exemple d’utilisation
if __name__ == "__main__":
    exemple = input("\n📥 Entrez une description à analyser :\n> ")
    suggestions = find_best_service_from_titles(exemple)

    print("\n🔍 Suggestions de services les plus proches (sur titres seuls) :\n")
    for s in suggestions:
        print(f"• {s['Service']} — score : {s['Score']}")
