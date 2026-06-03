import spacy
import re
from typing import Optional

# Load once at module level
nlp = spacy.load("en_core_web_md")

# POS tags to keep
KEEP_POS = {"NOUN", "PROPN", "ADJ"}

# Domain-specific adjectives spaCy sometimes misclassifies
FORCE_KEEP = {
    "waterproof", "breathable", "washable", "anti-slip", "non-stick",
    "foldable", "adjustable", "rechargeable", "biodegradable", "stretchable",
}

# Product noise that passes POS filter but adds no semantic value
SEMANTIC_STOPWORDS = {
    "product", "item", "thing", "piece", "set", "pack", "lot",
    "great", "good", "nice", "best", "new", "top", "perfect",
    "amazing", "incredible", "wonderful", "beautiful", "excellent",
    "quality",  # too generic — appears in every product
}


def extract_semantic_tokens(
    text: str,
    deduplicate: bool = True,
    preserve_order: bool = True,
) -> list[str]:
    """
    Extract only nouns and adjectives from a product description.
    Returns lowercased lemmas in their original order.
    """
    if not text:
        return []

    # Light pre-clean (HTML, excessive punctuation)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    doc = nlp(text)

    seen = set()
    tokens = []

    for token in doc:
        # 1. Check forced-keep list first (before POS check)
        lemma = token.lemma_.lower()
        raw = token.text.lower()

        is_keep = (
            token.pos_ in KEEP_POS
            or raw in FORCE_KEEP
            or lemma in FORCE_KEEP
        )
        if not is_keep:
            continue

        # 2. Drop stopwords, punctuation, very short tokens
        if token.is_stop or token.is_punct or len(lemma) < 3:
            continue

        # 3. Drop semantic noise
        if lemma in SEMANTIC_STOPWORDS or raw in SEMANTIC_STOPWORDS:
            continue

        # 4. Deduplicate
        if deduplicate and lemma in seen:
            continue

        seen.add(lemma)
        tokens.append(lemma)

    return tokens


def clean_for_embedding(text: str) -> str:
    """
    Returns a cleaned string ready for vectorization.
    Joins extracted tokens into a space-separated string.
    """
    return " ".join(extract_semantic_tokens(text))
