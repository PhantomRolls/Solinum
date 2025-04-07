import pandas as pd

df = pd.read_csv("Lexique.csv", delimiter=';')
mot_recherche = 'de'
print(df.loc[df["1_ortho"] == mot_recherche, "7_freqlemfilms2"])


data = pd.read_csv("soliguide.csv", delimiter=';')

from ydata_profiling import ProfileReport


profile = ProfileReport(data, title="Rapport de Profilage", explorative=True)
profile.to_file("rapport_profilage.html")