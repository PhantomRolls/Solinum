import spacy

# Charger le modèle français de spaCy
nlp = spacy.load("fr_core_news_md")

# Dictionnaire de remplacement : mots peu courants -> synonymes plus courants
synonymes = {
    "approfondir": "étudier",
    "néanmoins": "mais",
    "par conséquent": "donc",
    "inéluctable": "inévitable",
    # Vous pouvez compléter ce dictionnaire avec d'autres remplacements
}

def remplacer_synonymes(doc):
    """
    Remplace les mots peu courants dans un document spaCy par des synonymes plus simples.
    """
    tokens_modifies = []
    for token in doc:
        # On vérifie en minuscule pour matcher avec le dictionnaire
        mot = token.text
        if mot.lower() in synonymes:
            # Conserver la majuscule si nécessaire
            remplacement = synonymes[mot.lower()]
            if mot[0].isupper():
                remplacement = remplacement.capitalize()
            tokens_modifies.append(remplacement)
        else:
            tokens_modifies.append(mot)
    return " ".join(tokens_modifies)

def segmenter_phrase(phrase, max_mots=12):
    """
    Si la phrase est trop longue, on la découpe en phrases plus courtes.
    Ici, on découpe par tranche de 'max_mots' mots.
    """
    mots = phrase.split()
    if len(mots) <= max_mots:
        return [phrase]
    
    segments = []
    for i in range(0, len(mots), max_mots):
        segment = " ".join(mots[i:i+max_mots])
        # On s'assure que la phrase commence par une majuscule et se termine par un point
        segment = segment.capitalize()
        if not segment.endswith('.'):
            segment += '.'
        segments.append(segment)
    return segments

def transformer_en_falc(texte):
    """
    Transforme un texte en texte FALC.
    - Découpe en phrases avec spaCy.
    - Remplace les mots complexes par des synonymes simples.
    - Découpe les phrases longues en segments courts.
    """
    doc = nlp(texte)
    phrases_falc = []
    
    for sent in doc.sents:
        # Remplacer les mots par des synonymes simples
        phrase_simplifiee = remplacer_synonymes(sent)
        
        # On force une structure déclarative en s'assurant que la phrase se termine par un point
        phrase_simplifiee = phrase_simplifiee.strip()
        if not phrase_simplifiee.endswith('.'):
            phrase_simplifiee += '.'
        
        # Segmenter si la phrase est trop longue
        segments = segmenter_phrase(phrase_simplifiee, max_mots=12)
        phrases_falc.extend(segments)
        
    # Rassembler les phrases simplifiées
    return " ".join(phrases_falc)

# Exemple d'utilisation
texte_original = (
    "Afin d'approfondir notre compréhension du phénomène, nous devons analyser les données. "
    "Néanmoins, il est inéluctable que certaines variables complexes apparaissent, par conséquent, "
    "des ajustements méthodologiques sont nécessaires."
)

texte_falc = transformer_en_falc(texte_original)
print("Texte original :")
print(texte_original)
print("\nTexte FALC :")
print(texte_falc)
