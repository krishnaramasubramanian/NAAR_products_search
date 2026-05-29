import meilisearch
from dataclasses import dataclass
from typing import List
import re
# Meilisearch client
client = meilisearch.Client('http://localhost:7700')

INDEX_NAME = 'products'

def normalize_query(q):
    q = q.lower()
    # remove punctuation
    q = re.sub(r'[^a-z0-9\s]', '', q)
    q = re.sub(r'\s+', ' ', q).strip()
    return q

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
        
        # Search - typo tolerance is configured at index level
        results = index.search(
            query,
            {
                'limit': top_k,
                'attributesToRetrieve': ['_id', 'title', 'seller_name'],
                'showRankingScore': True
            }
        )
        
        # Convert to MeilisearchResult objects
        search_results = []
        for hit in results['hits']:
            search_results.append(
                MeilisearchResult(
                    product_id=hit['_id'],
                    title=hit.get('title', ''),
                    seller=hit.get('seller_name', ''),
                    score=hit.get('_rankingScore', 0)
                )
            )
        
        
        return search_results
    
    except Exception as e:
        print(f"Meilisearch error: {e}")
        return []
