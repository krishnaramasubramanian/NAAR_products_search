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
    match = process.extractOne(
        word,
        choices,
        scorer=fuzz.WRatio,
        score_cutoff=cutoff(word)
    )
    if not match:
        return word
    candidate = match[0]
    dist = DamerauLevenshtein.distance(word, candidate)
    print(match)
    l = len(word)

    if l >= 8 and dist <= 2:
        return candidate
    elif l >= 4 and dist <= 1:
        return candidate
    else:
        return word

def correct_query(query):

    corrected = []
    query = normalize_query(query)
    for word in query.split():
        corrected.append(
            correct_word(word)
        )

    return " ".join(corrected)

if __name__ == '__main__':
    correct_query('chaaree')