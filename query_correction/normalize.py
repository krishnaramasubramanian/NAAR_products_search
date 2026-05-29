import re
import unicodedata


def normalize_query(q):

    q = unicodedata.normalize(
        "NFKD",
        q
    )

    # punctuation → spaces
    normalized = ''.join(
            char for char in q 
            if unicodedata.category(char) != 'Mn')

    normalized = normalized.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized