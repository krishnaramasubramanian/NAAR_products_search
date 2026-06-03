
import meilisearch
from dataclasses import dataclass
from typing import List
import re

# Meilisearch client
client = meilisearch.Client('http://localhost:7700')
INDEX_NAME = 'products'


def normalize_query(q: str) -> str:
    q = q.lower()
    q = re.sub(r'[^a-z0-9\s]', '', q)
    q = re.sub(r'\s+', ' ', q).strip()
    return q


def passes_coverage_gate(query: str, title: str) -> bool:

    q_tokens = query.lower().split()
    t_tokens = title.lower().split()

    extended_t_tokens = set(t_tokens)
    for i in range(len(t_tokens) - 1):
        extended_t_tokens.add(t_tokens[i] + t_tokens[i + 1])

    for qt in q_tokens:
        for tt in extended_t_tokens:
            if not tt.startswith(qt):
                continue
            if len(qt) >= 4:
                return True
            coverage = len(qt) / len(tt)
            if coverage >= 0.4:
                return True

    return False


@dataclass
class MeilisearchResult:
    product_id: str
    title: str
    seller: str
    score: float


def search(query: str, top_k: int = 10) -> List[MeilisearchResult]:
    if not query or not query.strip():
        return []

    query = query.strip()
    normalized_query = normalize_query(query)

    try:
        index = client.index(INDEX_NAME)
        results = index.search(
            query,
            {
                'limit': top_k,
                'attributesToRetrieve': ['_id', 'title', 'seller_name'],
                'showRankingScore': True
            }
        )

        search_results = []
        for hit in results['hits']:
            title = hit.get('title', '')

            #if not passes_coverage_gate(normalized_query, normalize_query(title)):
                #continue

            search_results.append(
                MeilisearchResult(
                    product_id=hit['_id'],
                    title=title,
                    seller=hit.get('seller_name', ''),
                    score=hit.get('_rankingScore', 0)
                )
            )

        return search_results

    except Exception as e:
        print(f"Meilisearch error: {e}")
        return []
