import spacy
from wordfreq import get_frequency_dict, word_frequency

# Charger le modèle de langue français de spaCy
nlp = spacy.load("fr_core_news_sm")

# Définir le seuil de fréquence a
a = 1e-6

# Récupérer la liste des mots français et leurs fréquences
freq_dict = get_frequency_dict("fr", wordlist="best")

# Filtrer les mots qui ont une fréquence inférieure à a 
# et dont le lemme a également une fréquence inférieure à a.
words_with_lemma = []
for mot, freq in freq_dict.items():
    if freq < a:
        # Obtenir le lemme du mot grâce à spaCy
        doc = nlp(mot)
        lemma = doc[0].lemma_ if doc else mot
        
        # Vérifier que la fréquence du lemme est aussi inférieure à a
        if word_frequency(lemma, 'fr') < a:
            words_with_lemma.append((mot, lemma))
    if len(words_with_lemma) >= 10:
        break

# Affichage des 10 premiers mots rares et leurs lemmes associés
print("Les 10 premiers mots rares et leurs lemmes associés :")
for word, lemma in words_with_lemma[:10]:
    print(f"Mot : {word} - Lemma : {lemma}")
