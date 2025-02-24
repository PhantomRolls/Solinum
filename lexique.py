import spacy
from wordfreq import word_frequency
from bs4 import BeautifulSoup
import pandas as pd

data = pd.read_csv("soliguide.csv", delimiter=';')
data=data[:100]
place_description = data['place_description']

with open("soliguide.html", "w", encoding="utf-8") as file:
    file.write(place_description.iloc[0])


soup = BeautifulSoup(place_description.iloc[10], "html.parser")
text = soup.get_text()
print(text)
# Charge le modèle français de spaCy (assurez-vous de l'avoir installé via "python -m spacy download fr_core_news_sm")
nlp = spacy.load("fr_core_news_sm")

def is_passive_sentence(sent):
    """
    Détecte si une phrase est au passif.
    Pour cela, on vérifie si un token possède l'attribut Morph "Voice=Pass".
    """
    for token in sent:
        # La méthode token.morph.get("Voice") retourne une liste de valeurs.
        if "Pass" in token.morph.get("Voice"):
            return True
    return False

def note_falc_avance(texte, sentence_length_thresh=15, uncommon_thresh=1e-6):
    """
    Calcule une note de lisibilité (0 à 100) en s'inspirant de critères FALC.
    
    Critères :
      - Longueur moyenne des phrases (pénalité de 2 points par mot au-dessus de sentence_length_thresh).
      - Ratio de mots peu courants (utilisant wordfreq ; on pénalise 1 point par pourcentage).
      - Proportion de phrases en voix passive (1 point de pénalité par pourcentage de phrases passives).
    
    Retourne également quelques détails sur l'analyse.
    """
    doc = nlp(texte)
    sentences = list(doc.sents)
    nb_sentences = len(sentences)
    if nb_sentences == 0:
        return 0, {}

    total_words = 0
    total_uncommon = 0
    passive_count = 0

    for sent in sentences:
        # Sélectionne les tokens alphabétiques (pour ignorer la ponctuation, etc.)
        words = [token for token in sent if token.is_alpha]
        total_words += len(words)
        
        # Compte les mots peu courants
        for token in words:
            # Récupère la fréquence du mot en français
            freq = word_frequency(token.text.lower(), 'fr')
            if freq < uncommon_thresh and not token.is_upper:
                total_uncommon += 1
        
        # Détecte si la phrase est passive
        if is_passive_sentence(sent):
            passive_count += 1

    avg_sentence_length = total_words / nb_sentences
    uncommon_ratio = total_uncommon / total_words if total_words else 0
    passive_ratio = passive_count / nb_sentences

    # Démarre avec une note de 100
    score = 100

    # Pénalité pour longueur moyenne des phrases :
    if avg_sentence_length > sentence_length_thresh:
        score -= (avg_sentence_length - sentence_length_thresh) * 2

    # Pénalité pour mots peu courants :
    # Par exemple, si 20 % des mots sont peu courants, on soustrait 20 points.
    score -= uncommon_ratio * 100

    # Pénalité pour phrases passives :
    score -= passive_ratio * 100

    # S'assure que le score reste entre 0 et 100
    score = max(0, min(100, score))

    details = {
        "avg_sentence_length": avg_sentence_length,
        "uncommon_ratio": uncommon_ratio,
        "passive_ratio": passive_ratio,
        "total_sentences": nb_sentences,
        "total_words": total_words,
        "total_uncommon_words": total_uncommon,
        "passive_sentences": passive_count
    }
    return score, details

# Exemple de texte complexe
texte_complexe = ("Le Refuge offre une aide et un accompagnement personnalisés pour faciliter l'intégration des personnes accueillies, en les aidant à gagner confiance dans leur capacité à s'exprimer et à faire face aux défis de la vie quotidienne. L'équipe du Refuge comprend des professionnels formés pour soutenir chacun dans son parcours de recherche d'une solution. Les locaux du Refuge disposent également d'un jardin fleuri où les résidents peuvent pratiquer l'hébergement animalier."
                  )
score, details = note_falc_avance(texte_complexe)
print(f"Score FALC avancé : {score:.2f}/100")
print("Détails de l'analyse :", details)
