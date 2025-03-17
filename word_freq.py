from wordfreq import get_frequency_dict
from wordfreq import word_frequency

# Définir le seuil de fréquence a
a = 0.9e-6  # Par exemple, mots avec une fréquence > 0.0001

# Récupérer la liste des mots français et leurs fréquences
freq_dict = get_frequency_dict("fr", wordlist="best")

# Filtrer les mots qui ont une fréquence > a
mots_frequents = [mot for mot, freq in freq_dict.items() if freq > a]


print("Quelques exemples:", mots_frequents[-10:])  # Afficher les 20 premiers mots
print(word_frequency("caard", 'fr'))
