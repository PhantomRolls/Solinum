import pandas as pd

# 1. Charger les données depuis le fichier CSV d'origine
df = pd.read_csv("output/classification_services.csv")  # Remplace par le bon chemin

# 2. Filtrer les lignes où service_name != service_attribue
df_diff = df[df['service_name'] != df['service_attribue']]

# 3. Sauvegarder le résultat dans un nouveau fichier CSV
df_diff.to_csv("output/services_differents.csv", index=False)

print("✅ Nouveau fichier 'services_differents.csv' créé avec succès.")
