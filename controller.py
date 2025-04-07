from correction import correct_text
from rewriting import rewrite_text
import pandas as pd

# Charger la base de données
df = pd.read_csv("soliguide.csv", delimiter=';')
df_unique = df.drop_duplicates(subset='place_id')

def process_dataframe(apply_correction=True, apply_rewriting=True):
    text_column = "place_description"

    for i, row in df.iterrows():
        text = row[text_column]

        if apply_correction:
            text = correct_text(text)
        if apply_rewriting:
            text = rewrite_text(text)

        df.at[i, text_column] = text

    # Sauvegarde du résultat
    df.to_csv("soliguide_processed.csv", sep=';', index=False)
    print("Traitement terminé. Nouveau fichier : soliguide_processed.csv")

def main():
    print("Choisissez les traitements à appliquer :")
    print("1 - Correction des fautes")
    print("2 - Réécriture")
    print("3 - Les deux")
    choice = input("Votre choix : ")

    apply_correction = choice in ["1", "3"]
    apply_rewriting = choice in ["2", "3"]

    process_dataframe(apply_correction, apply_rewriting)

if __name__ == "__main__":
    main()
