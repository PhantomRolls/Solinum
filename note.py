#!/usr/bin/env python3
import sys
import os
from bs4 import BeautifulSoup
import pandas as pd
import spacy
from wordfreq import word_frequency

# --- Configuration des fichiers d'entrée/sortie ---
INPUT_CSV  = "input/soliguide_v2.csv"
INPUT_TXT  = "fichiers_csv/texte_complexe.txt"
OUTPUT_CSV = "output/note.csv"

# --- Chargement du modèle spaCy français ---
nlp = spacy.load("fr_core_news_sm")

# --- Fonctions d'analyse ---

def is_passive_sentence(sent):
    return any("Pass" in token.morph.get("Voice") for token in sent)


def count_subordinates(doc):
    sub_clause_count = 0
    sub_clause_words = []
    for token in doc:
        if token.dep_ in ["mark", "ccomp", "acl", "advcl", "relcl"] and token.i > 0:
            prev = doc[token.i - 1]
            if prev.text == ",":
                sub_clause_count += 1
                sub_clause_words.append(token.text)
    return sub_clause_count, sub_clause_words


def note_falc_avance(texte, sentence_length_thresh=15, uncommon_thresh=1e-6):
    doc = nlp(texte)
    sentences = list(doc.sents)
    nb_sent = len(sentences)
    if nb_sent == 0:
        return 0, {}

    total_words = 0
    total_uncommon = 0
    passive_count = 0
    sub_count, sub_words = count_subordinates(doc)
    uncommon_tokens = []

    for sent in sentences:
        words = [t for t in sent if t.is_alpha]
        total_words += len(words)
        for token in words:
            lemma = token.lemma_.lower()
            freq_t = word_frequency(token.text, 'fr')
            freq_l = word_frequency(lemma, 'fr')
            if max(freq_t, freq_l) < uncommon_thresh and not token.is_upper:
                total_uncommon += 1
                uncommon_tokens.append(token.text)
        if is_passive_sentence(sent):
            passive_count += 1

    avg_len = total_words / nb_sent
    uncommon_ratio = total_uncommon / total_words if total_words else 0
    passive_ratio = passive_count / nb_sent
    sub_ratio = sub_count / nb_sent

    # Calcul du score
    score = 100
    if avg_len > sentence_length_thresh:
        score -= (avg_len - sentence_length_thresh) * 2
    score -= uncommon_ratio * 200
    score -= passive_ratio * 50
    score -= sub_ratio * 50
    score = max(0, min(100, score))

    details = {
        "avg_sentence_length": avg_len,
        "total_words": total_words,
        "total_uncommon_words": total_uncommon,
        "uncommon_tokens": uncommon_tokens,
        "passive_sentences": passive_count,
        "passive_ratio": passive_ratio,
        "subordinate_clauses": sub_count,
        "subordinate_ratio": sub_ratio,
        "subordinate_words": sub_words
    }
    return score, details


def main():
    # Lecture de l'argument rows (nombre de lignes)
    try:
        rows = int(sys.argv[1])
        if rows < 1:
            rows = None
    except (IndexError, ValueError):
        rows = None

    # Lecture et sélection des lignes
    df = pd.read_csv(INPUT_CSV, sep=';')
    df = df.drop_duplicates(subset='place_id')
    if rows is not None:
        df = df.head(rows)

    results = []

    # Parcours de chaque description
    for index, row in df.iterrows():
        place_name = row.get('place_name', f"Place_{index}")
        raw_html = row.get('place_description', '')
        texte = BeautifulSoup(str(raw_html), "html.parser").get_text()

        # Analyse FALC avancé
        score, details = note_falc_avance(texte)

        # Stockage du résultat avec le texte
        result = {
            'place_name': place_name,
            'texte': texte,
            'score': score
        }
        result.update(details)
        results.append(result)

        # Affichage console
        print(f"🔍 {place_name} → Score: {score:.2f}/100")

    # Export CSV
    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"✅ Fichier '{OUTPUT_CSV}' généré avec succès.")

if __name__ == '__main__':
    main()