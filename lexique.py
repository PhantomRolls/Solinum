import spacy
from wordfreq import word_frequency
from bs4 import BeautifulSoup
import pandas as pd

data = pd.read_csv("soliguide.csv", delimiter=';')
data=data[:600]
place_description = data['place_description']
place_description_unique = place_description.drop_duplicates()

with open("soliguide.html", "w", encoding="utf-8") as file:
    file.write(place_description_unique.iloc[1])


soup = BeautifulSoup(place_description_unique.iloc[1], "html.parser")
text = soup.get_text()


nlp = spacy.load("fr_core_news_sm")

def is_passive_sentence(sent):
   
    for token in sent:
        if "Pass" in token.morph.get("Voice"):
            return True
    return False

def count_subordinates(doc):

    sub_clause_count = 0
    sub_clause_words = []
    for token in doc:
        if token.dep_ in ["mark", "ccomp", "acl", "advcl", "relcl"] and token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.text == ",":
                sub_clause_count += 1
                sub_clause_words.append(token.text)
    return sub_clause_count, sub_clause_words
        
def note_falc_avance(texte, sentence_length_thresh=15, uncommon_thresh=1e-6):
    uncommon=[]
    doc = nlp(texte)
    sentences = list(doc.sents)
    nb_sentences = len(sentences)
    if nb_sentences == 0:
        return 0, {}

    total_words = 0
    total_uncommon = 0
    passive_count = 0
    sub_count, sub_words = count_subordinates(doc)
    
    for sent in sentences:

        words = [token for token in sent if token.is_alpha]
        total_words += len(words)

        for token in words:
            lemma = token.lemma_.lower()
            freq_token= word_frequency(token.text, 'fr')
            freq_lemma = word_frequency(lemma, 'fr')
            if max(freq_token, freq_lemma) < uncommon_thresh and not token.is_upper:
                total_uncommon += 1
                uncommon.append(token.text)
        

        if is_passive_sentence(sent):
            passive_count += 1

    avg_sentence_length = total_words / nb_sentences
    uncommon_ratio = total_uncommon / total_words if total_words else 0
    passive_ratio = passive_count / nb_sentences
    sub_ratio = sub_count / nb_sentences
    

    score = 100

    if avg_sentence_length > sentence_length_thresh:
        score -= (avg_sentence_length - sentence_length_thresh) * 2

    score -= uncommon_ratio * 200
    score -= passive_ratio * 50
    score -= sub_ratio * 50
    
    score = max(0, min(100, score))

    details = {
        "avg_sentence_length": avg_sentence_length,
        "total_words": total_words,  
        "total_uncommon_words": total_uncommon,
        "uncommon": uncommon,
        "passive_sentences": passive_count,
        "passive_sentences_ratio": passive_ratio,
        "subordinate_clauses": sub_count,
        "subordinate_clauses": sub_ratio,
        "subordinate_clause_words": sub_words,
        
    }
    return score, details

with open("texte_complexe.txt", "r", encoding="utf-8") as fichier:
    texte_complexe = fichier.read()

print(texte_complexe)
score, details = note_falc_avance(texte_complexe)
print(f"Score FALC avancé : {score:.2f}/100")
print("Détails de l'analyse :", details)

print('o\no')

print(text)
score, details = note_falc_avance(text)
print(f"Score FALC avancé : {score:.2f}/100")
print("Détails de l'analyse :", details)