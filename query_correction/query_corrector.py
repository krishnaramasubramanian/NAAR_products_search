import pickle
from .aliases import ALIASES
from rapidfuzz import process, fuzz
from rapidfuzz.distance import DamerauLevenshtein
from .normalize import normalize_query
with open(
    "catalog_vocab.pkl",
    "rb"
) as f:
    VOCAB = pickle.load(f)

def cutoff(word):

    l = len(word)

    if l <= 3:
        return 100

    elif l <= 7:
        return 80

    else:
        return 75

    # exact match
def correct_word(word):

    if word in VOCAB:
        return word

    if word in ALIASES:
        return ALIASES[word]

    choices = [
        v for v in VOCAB
        if abs(len(v) - len(word)) <= 2
    ]

    results = process.extract(
        word,
        choices,
        scorer=fuzz.WRatio,
        limit=2
    )

    if not results:
        return word

    candidate, score, _ = results[0]

    dist = DamerauLevenshtein.distance(
        word,
        candidate
    )

    length_ratio = (
        len(candidate)
        / max(len(word), 1)
    )

    gap = 100

    if len(results) > 1:
        gap = score - results[1][1]

    if (
        score >= 90
        and length_ratio >= 0.7
        and gap >= 10
    ):
        if (
            len(word) >= 8
            and dist <= 2
        ):
            return candidate

        if (
            len(word) < 8
            and dist <= 1
        ):
            return candidate

    return word

def correct_query(query): 
    corrected = [] 
    query = normalize_query(query) 
    for word in query.split(): 
        corrected.append( correct_word(word) ) 
    return " ".join(corrected)   